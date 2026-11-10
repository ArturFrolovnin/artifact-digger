"""Use the existing Dormitory exporter with Library configuration; never save source."""
import bpy, json
from pathlib import Path

source=Path(bpy.data.filepath).parent
assert source.name=='Source' and source.parent.name=='Library'
EXPORT_CONFIG=json.loads((source/'model_config.json').read_text(encoding='utf-8'))
script=source.parent.parent/'Dormitory/Source/Scripts/export_fbx.py'
exec(compile(script.read_text(encoding='utf-8-sig'),str(script),'exec'))
