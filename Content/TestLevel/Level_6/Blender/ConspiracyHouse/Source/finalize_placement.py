"""Verify the approved placement and save only its assets and Level_6.

Execute through Unreal ProgrammaticToolset; requires placement_report.txt.
Does not spawn actors or regenerate geometry.
"""
import json

BASE = '/Game/TestLevel/Level_6/Blender/ConspiracyHouse/'
LEVEL = '/Game/TestLevel/Level_6/level_6_create_map'
REPORT = 'D:/UEProject/ArcheoDig/Content/TestLevel/Level_6/Blender/ConspiracyHouse/Source/placement_report.txt'

def tool(group, name, args):
    return execute_tool('editor_toolset.toolsets.' + group + '.' + name, json.dumps(args)).get('returnValue')

def detail(actor, name):
    return tool('actor.ActorTools', name, {'actor': actor})

def properties(instance, keys):
    return json.loads(tool('object.ObjectTools', 'get_properties', {'instance': instance, 'properties': keys}))

def run():
    report = json.loads(tool('asset.AssetTools', 'read_file', {'file_path': REPORT}))
    assert tool('scene.SceneTools', 'get_current_level', {}) == LEVEL
    actors = tool('scene.SceneTools', 'find_actors', {'name': '', 'tag': '', 'collision_channels': []})
    paths = {a['refPath'] for a in actors}
    assert len(actors) == report['final_actor_count'] == 374
    for suffix, label, loc, rot, scale in report['protected']:
        actor = {'refPath': LEVEL + '.level_6_create_map:' + suffix}
        assert actor['refPath'] in paths, label
        assert detail(actor, 'get_label') == label
        transform = detail(actor, 'get_actor_transform')
        for key, names, values in [('location', 'xyz', loc), ('rotation', ['pitch', 'yaw', 'roll'], rot), ('scale', 'xyz', scale)]:
            assert all(abs(transform[key][n] - v) < 1e-6 for n, v in zip(names, values)), label
    for old in report['removed']:
        assert old['actor']['refPath'] not in paths
    for key, actor in report['placed'].items():
        assert detail(actor, 'get_label') == 'ConspiracyHouse_' + key
        transform = detail(actor, 'get_actor_transform')
        for section, values in report['transform'].items():
            assert all(abs(transform[section][n] - v) < 1e-6 for n, v in values.items())
        bounds = detail(actor, 'get_actor_bounds')
        for axis in 'xy':
            assert bounds['min'][axis] >= report['plot']['min'][axis] - .001
            assert bounds['max'][axis] <= report['plot']['max'][axis] + .001
        component = {'refPath': actor['refPath'] + '.StaticMeshComponent0'}
        p = properties(component, ['staticMesh', 'overrideMaterials'])
        name = 'SM_ConspiracyHouse_' + key
        assert p['staticMesh']['refPath'] == BASE + name + '.' + name
        assert not p['overrideMaterials']
    assets = tool('asset.AssetTools', 'find_assets', {'folder_path': BASE.rstrip('/'), 'name': ''})
    assert len(assets) == 39, len(assets)
    assert all(a.startswith(BASE) for a in assets)
    assert tool('asset.AssetTools', 'save_assets', {'asset_paths': assets + [LEVEL]})
    assert not any(tool('asset.AssetTools', 'is_dirty', {'asset_path': a}) for a in assets + [LEVEL])
    report.update({'status': 'completed', 'level_saved': True, 'assets_saved': 39, 'protected_actor_count': len(report['protected']), 'all_other_actor_labels_and_transforms_unchanged': True})
    tool('asset.AssetTools', 'write_file', {'file_path': REPORT, 'content': json.dumps(report, separators=(',', ':'))})
    return {k: report[k] for k in ['status', 'level_saved', 'assets_saved', 'protected_actor_count', 'transform', 'gate']}
