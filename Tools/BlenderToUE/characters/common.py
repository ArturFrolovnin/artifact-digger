"""Host-independent character pipeline validation. No editor side effects."""
import hashlib
import json
import math
import re
from pathlib import Path


class PipelineError(RuntimeError):
    pass


def require(condition, message):
    if not condition:
        raise PipelineError(message)


def load_config(npc, root=None):
    root = Path(root or Path(__file__).resolve().parents[3]).resolve()
    registry = json.loads((Path(__file__).parent / 'characters.json').read_text(encoding='utf-8-sig'))
    require(npc in registry['characters'], 'Unknown NPC: ' + npc)
    cfg = dict(registry['characters'][npc])
    cfg['rig'] = registry['profiles'][cfg['profile']]
    cfg['npc'] = npc
    cfg['project'] = str(root)
    cfg['log_dir'] = str(root / 'Saved/BlenderToUE/Characters' / npc)
    cfg['fbx'] = str(root / 'SourceAssets/Blender/Characters' / npc / (cfg['unreal_asset'].rsplit('/', 1)[1] + '.fbx'))
    require((root / cfg['source_blend']).is_file(), 'Missing source blend')
    return cfg


def write_json(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding='utf-8')


def file_hash(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()


def material_key(name):
    return 'M_' + re.sub(r'[^A-Za-z0-9_]', '_', name).strip('_')


def compatible(actual, reference, rig):
    """Missing corrective bones in the *Skeleton* are allowed; the reference mesh is exact."""
    a = {b['name']: b for b in actual}
    r = {b['name']: b for b in reference}
    require(len(a) == len(actual), 'Duplicate bone names')
    require(set(a) == set(r), 'Bone set mismatch; added=%s missing=%s' % (sorted(set(a)-set(r)), sorted(set(r)-set(a))))
    worst_p = worst_r = 0.0
    for name, b in a.items():
        ref = r[name]
        require(b['parent'] == ref['parent'], 'Incompatible parent: ' + name)
        distance = math.dist(b['translation'], ref['translation'])
        q, v = b['rotation_xyzw'], ref['rotation_xyzw']
        dot = abs(sum(x*y for x, y in zip(q, v))) / math.sqrt(sum(x*x for x in q)*sum(x*x for x in v))
        angle = math.degrees(2*math.acos(min(1.0, dot)))
        require(distance <= rig['position_tolerance_cm'], 'Rest position differs for %s: %.6f cm' % (name, distance))
        require(angle <= rig['rotation_tolerance_deg'], 'Rest rotation differs for %s: %.6f deg' % (name, angle))
        require(max(abs(x-y) for x, y in zip(b['scale'], ref['scale'])) < 0.0001, 'Rest scale differs: ' + name)
        worst_p, worst_r = max(worst_p, distance), max(worst_r, angle)
    return {'max_position_error_cm': worst_p, 'max_rotation_error_deg': worst_r}


def expected_ue_bounds(bounds_m):
    lo, hi = bounds_m
    return [[lo[0]*100, -hi[1]*100, lo[2]*100], [hi[0]*100, -lo[1]*100, hi[2]*100]]


def validate_bounds(actual_cm, expected_cm, tolerance):
    require(all(abs(a-b) <= tolerance for row, other in zip(actual_cm, expected_cm) for a, b in zip(row, other)),
            'Scale/orientation/bounds mismatch: actual=%s expected=%s' % (actual_cm, expected_cm))
