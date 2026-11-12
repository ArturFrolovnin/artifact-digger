"""Reimport Rudy (building + separate door), or an explicitly configured model.

Run inside Unreal Editor Python. Never changes or saves levels.
"""
import unreal
import json
from pathlib import Path

source=Path(unreal.Paths.project_dir()).resolve()/'SourceAssets/Blender/Buildings/RudyPawnshop/Source'
config=globals().get('IMPORT_CONFIG')
if not config:
    config=json.loads((source/'model_config.json').read_text(encoding='utf-8'))
    assert config['model_id']=='RudyPawnshop'
# Avoid leaking Rudy's default config into later imports from the same console.
shared=source/'reimport_configured.py'
exec(compile(shared.read_text(encoding='utf-8'),str(shared),'exec'),{'IMPORT_CONFIG':config})
