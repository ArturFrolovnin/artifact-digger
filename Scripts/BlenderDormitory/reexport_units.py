import bpy
from pathlib import Path
p=Path('D:/UEProject/ArcheoDig/Scripts/BlenderDormitory/export_fbx.py')
s=p.read_text(encoding='utf-8-sig').replace("apply_scale_options='FBX_SCALE_UNITS'","apply_scale_options='FBX_SCALE_NONE'")
p.write_text(s,encoding='utf-8')
for o in bpy.context.selected_objects:o.select_set(False)
for o in bpy.data.collections['BLD_Dormitory'].all_objects:
    if o.type=='MESH':o.select_set(True)
bpy.ops.export_scene.fbx(filepath='D:/UEProject/ArcheoDig/Content/TestLevel/Level_6/Blender/Source/SM_Dormitory_Blockout.fbx',use_selection=True,object_types={'MESH'},global_scale=1.0,apply_unit_scale=True,apply_scale_options='FBX_SCALE_NONE',axis_forward='-Y',axis_up='Z',use_mesh_modifiers=True,mesh_smooth_type='FACE',use_triangles=True,bake_anim=False)
result={'fbx_reexported':'centimetre scale baked by FBX exporter; editable scene remains metres'}
