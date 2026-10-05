import bpy,bmesh,json,math
from pathlib import Path
from mathutils import Vector
out=Path('D:/UEProject/ArcheoDig/Content/TestLevel/Level_6/Blender/Dormitory/Source')
coll=bpy.data.collections['BLD_Dormitory']; root=bpy.data.objects['Dormitory_ROOT']
meshes=[o for o in coll.all_objects if o.type=='MESH']
assert len(meshes)==59
assert root.location.length<1e-6 and all(abs(v-1)<1e-6 for v in root.scale)
assert bpy.context.mode=='OBJECT'
for o in bpy.context.selected_objects:o.select_set(False)
for o in meshes:o.select_set(True)
bpy.context.view_layer.objects.active=meshes[0]
bpy.ops.object.transform_apply(location=False,rotation=True,scale=True)
flipped=0
for o in meshes:
    bm=bmesh.new(); bm.from_mesh(o.data)
    bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces)); bm.normal_update()
    # Single-sided exterior surfaces need explicit outward direction.
    for f in bm.faces:
        target=None
        n=o.name
        if n.startswith('DORM_20_Brick_'):
            suffix=n.split('DORM_20_Brick_')[1]
            target=Vector({'Front':(0,-1,0),'Rear':(0,1,0),'Left':(-1,0,0),'Right':(1,0,0)}[suffix])
        elif n.startswith(('DORM_25_','DORM_26_','DORM_32_')): target=Vector((0,0,1))
        elif n.startswith('DORM_27_'): target=Vector((1 if f.calc_center_median().x>0 else -1,0,0))
        elif n=='DORM_33_Porch_Trim' and len(f.verts)==3: target=Vector((0,-1,0))
        elif n=='DORM_35_Gable_Oculi' and all(e.is_boundary for e in f.edges): target=Vector((1 if f.calc_center_median().x>0 else -1,0,0))
        if target is not None and f.normal.dot(target)<0: f.normal_flip(); flipped+=1
    bm.to_mesh(o.data); bm.free(); o.data.update()
    used=sorted(set(p.material_index for p in o.data.polygons))
    mats=[o.data.materials[i] for i in used]
    lookup={old:new for new,old in enumerate(used)}
    indices=[lookup[p.material_index] for p in o.data.polygons]
    o.data.materials.clear()
    for m in mats:o.data.materials.append(m)
    for p,i in zip(o.data.polygons,indices):p.material_index=i
bpy.context.view_layer.update()
pts=[o.matrix_world@Vector(c) for o in meshes for c in o.bound_box]
lo=[min(p[i] for p in pts) for i in range(3)]; hi=[max(p[i] for p in pts) for i in range(3)]
assert abs(lo[2])<1e-5
assert all(all(abs(v-1)<1e-6 for v in o.scale) and o.rotation_euler.to_matrix().is_identity for o in meshes)
assert all(o.parent==root for o in meshes)
report={'body_m':[26,18],'min_m':lo,'max_m':hi,'dimensions_m':[hi[i]-lo[i] for i in range(3)],'root_m':list(root.location),'mesh_count':len(meshes),'scale_all_one':True,'rotation_applied':True,'outward_surface_faces_fixed':flipped,'zero_area_faces':sum(p.area<1e-10 for o in meshes for p in o.data.polygons),'triangles':sum(len(p.vertices)-2 for o in meshes for p in o.data.polygons),'export_objects':[o.name for o in meshes],'fbx_units':'metres exported with FBX unit conversion; UE centimetres','axis_forward':'-Y','axis_up':'Z'}
assert report['zero_area_faces']==0
root['export_validation']=json.dumps(report)
# Save the editable source with all architectural assemblies separate.
bpy.ops.wm.save_as_mainfile(filepath=str(out/'Dormitory_Blockout.blend'))
# Mesh-only selection excludes root, cameras, lights and archived test cube.
bpy.ops.export_scene.fbx(filepath=str(out/'SM_Dormitory_Blockout.fbx'),use_selection=True,object_types={'MESH'},global_scale=1.0,apply_unit_scale=True,apply_scale_options='FBX_SCALE_NONE',use_space_transform=True,bake_space_transform=False,axis_forward='-Y',axis_up='Z',use_mesh_modifiers=True,mesh_smooth_type='FACE',use_triangles=True,bake_anim=False,path_mode='AUTO',embed_textures=False)
(out/'SM_Dormitory_Blockout_validation.txt').write_text(json.dumps(report,indent=2),encoding='utf-8')
result={k:v for k,v in report.items() if k!='export_objects'}
result['blend']=str(out/'Dormitory_Blockout.blend'); result['fbx']=str(out/'SM_Dormitory_Blockout.fbx')
