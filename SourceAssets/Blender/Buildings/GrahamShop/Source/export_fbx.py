"""Export the authoritative Graham source with the existing configured exporter.

Run in Blender Object Mode. EXPORT_OUTPUT_DIR optionally redirects validation
exports. Editable objects, curves, lettering and modifiers are never saved here.
"""
import bpy, json
from pathlib import Path

source=Path(bpy.data.filepath).resolve().parent
assert source.name=='Source' and source.parent.name=='GrahamShop'
config=json.loads((source/'model_config.json').read_text(encoding='utf-8'))
assert Path(bpy.data.filepath).name==Path(config['source_blend']).name, \
    'Open the authoritative GrahamShop_Blockout.blend'
script=source.parent.parent/'Dormitory/Source/Scripts/export_fbx.py'
context={'EXPORT_CONFIG':config}
if 'EXPORT_OUTPUT_DIR' in globals():context['EXPORT_OUTPUT_DIR']=EXPORT_OUTPUT_DIR
if 'EXPORT_TARGETS' in globals():context['EXPORT_TARGETS']=EXPORT_TARGETS
exec(compile(script.read_text(encoding='utf-8-sig'),str(script),'exec'),context)
result=context['result']
print('GRAHAMSHOP_EXPORT_OK: FBX files updated. Unreal assets are updated by the next step.')
print('In Unreal Editor > Output Log > Cmd, run:')
print('py "D:/UEProject/ArcheoDig/SourceAssets/Blender/Buildings/GrahamShop/Source/finish_ue_import.py"')
