"""Reimport Graham in place through Rudy's existing configured import workflow.

Run inside the already open Unreal Editor after exporting. No level operations.
"""
try:
    import unreal
except ImportError as exc:
    raise RuntimeError(
        'Run finish_ue_import.py inside Unreal Editor, not Blender. '
        'In Unreal Output Log (Cmd), enter: '
        'py "D:/UEProject/ArcheoDig/SourceAssets/Blender/Buildings/GrahamShop/Source/finish_ue_import.py"'
    ) from exc
import json
from pathlib import Path

project=Path(unreal.Paths.project_dir()).resolve()
source=project/'SourceAssets/Blender/Buildings/GrahamShop/Source'
config=json.loads((source/'model_config.json').read_text(encoding='utf-8'))
assert config['model_id']=='GrahamShop'
dirty=unreal.EditorLoadingAndSavingUtils.get_dirty_content_packages()
for target in [config['unreal_asset']]+[p['unreal_asset'] for p in config['parts']]:
    mesh=unreal.load_asset(target)
    if mesh:
        assert mesh.get_outermost() not in dirty, 'Unsaved asset changes: '+target
script=source.parent.parent/'RudyPawnshop/Source/finish_ue_import.py'
exec(compile(script.read_text(encoding='utf-8'),str(script),'exec'),{'IMPORT_CONFIG':config})
