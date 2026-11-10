"""Export the current Dormitory using temporary evaluated copies.

Fixed architecture goes to the existing main mesh. Named independent parts are
grouped by asset path; linked door instances share one exported door template.
Never modifies or saves editable source objects. EXPORT_TARGETS optionally limits
exports to asset basenames (otherwise all meshes are exported).
"""
import bpy, bmesh, json
from pathlib import Path
from mathutils import Vector, Matrix

config=globals().get('EXPORT_CONFIG',{})
model_id=config.get('model_id','Dormitory')
source_dir=Path(bpy.data.filepath).parent
assert source_dir.name=='Source' and source_dir.parent.name==model_id
out=Path(globals().get('EXPORT_OUTPUT_DIR',source_dir))
out.mkdir(parents=True,exist_ok=True)
main_mesh=config.get('main_mesh','SM_Dormitory_Blockout')
assert bpy.context.mode=='OBJECT'
coll=bpy.data.collections[config.get('collection','BLD_Dormitory')]
root=bpy.data.objects[config.get('root','Dormitory_ROOT')]
assert root.location.length<1e-6 and all(abs(v-1)<1e-6 for v in root.scale)
assert bpy.context.scene.unit_settings.scale_length==1
sources=[o for o in coll.all_objects if o.type in {'MESH','FONT','CURVE'} and not o.get('export_helper',False)]
body=[o for o in sources if not o.get('export_separately',False)]
assert all(bpy.data.objects.get(n) in body for n in config.get('required_objects',['DORM_01_Plinth','DORM_02_Front_Floor_1','DORM_25_Pitched_Roof']))
parts={}
for o in sources:
    if o.get('export_separately',False) and not o.get('export_instance',False):
        parts.setdefault(o['unreal_asset'],[]).append(o)
selected=list(bpy.context.selected_objects)
active=bpy.context.view_layer.objects.active
targets=globals().get('EXPORT_TARGETS')
report={'assets':{},'axis_forward':'-Y','axis_up':'Z','fbx_units':'metres, FBX_SCALE_NONE; UE centimetres'}
original_meshes={o.name:len(o.data.vertices) for o in sources if o.type=='MESH'}

def fix_normals(obj):
    n=obj.get('export_source_name',obj.name)
    # Clipped, deliberately open surfaces have authoritative source winding.
    # Recalculating them as closed volumes can turn exterior faces inward.
    if config.get('preserve_source_normals',False) or n.startswith('DORM_INT_') or obj.get('export_preserve_normals',False):return
    bm=bmesh.new();bm.from_mesh(obj.data)
    bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.normal_update()
    for f in bm.faces:
        target=None
        if n.startswith('DORM_20_Brick_'):
            target=Vector({'Front':(0,-1,0),'Rear':(0,1,0),'Left':(-1,0,0),'Right':(1,0,0)}[n.split('DORM_20_Brick_')[1]])
        elif n.startswith(('DORM_25_','DORM_26_','DORM_32_')):target=Vector((0,0,1))
        elif n.startswith('DORM_27_'):target=Vector((1 if f.calc_center_median().x>0 else -1,0,0))
        elif n=='DORM_33_Porch_Trim' and len(f.verts)==3:target=Vector((0,-1,0))
        elif n=='DORM_35_Gable_Oculi' and all(e.is_boundary for e in f.edges):target=Vector((1 if f.calc_center_median().x>0 else -1,0,0))
        if target is not None and f.normal.dot(target)<0:f.normal_flip()
    bm.to_mesh(obj.data);bm.free();obj.data.update()

def export(objects,name,pivot=None):
    if targets is not None and name not in targets:return
    temporary=[];temporary_data=[];inverse=pivot.inverted() if pivot is not None else Matrix.Identity(4)
    try:
        bpy.ops.object.select_all(action='DESELECT')
        for original in objects:
            obj=original.copy();obj.data=original.data.copy();coll.objects.link(obj)
            temporary.append(obj);temporary_data.append(obj.data)
            obj.parent=None;obj.matrix_world=inverse@original.matrix_world
            obj['export_source_name']=original.name
            obj.select_set(True)
        bpy.context.view_layer.objects.active=temporary[0]
        bpy.ops.object.convert(target='MESH')
        temporary=list(bpy.context.selected_objects)
        bpy.ops.object.transform_apply(location=False,rotation=True,scale=True)
        for obj in temporary:
            temporary_data.append(obj.data)
            fix_normals(obj)
            # Bevels on millimetre-scale keys/paper can create zero-area slivers.
            # Remove only these non-rendering triangles on export copies.
            if obj['export_source_name'].startswith('DORM_INT_') or config.get('remove_degenerate_export_faces',False):
                bm=bmesh.new();bm.from_mesh(obj.data)
                bmesh.ops.triangulate(bm,faces=list(bm.faces))
                bad=[f for f in bm.faces if f.calc_area()<=1e-12 or any(e.calc_length()<2e-7 for e in f.edges)]
                if bad:bmesh.ops.delete(bm,geom=bad,context='FACES')
                bm.to_mesh(obj.data);bm.free();obj.data.update()
            used=sorted({p.material_index for p in obj.data.polygons})
            mats=[obj.data.materials[i] for i in used]
            assert all(mats),'Unassigned used material: '+obj['export_source_name']
            indices=[used.index(p.material_index) for p in obj.data.polygons]
            obj.data.materials.clear()
            for mat in mats:obj.data.materials.append(mat)
            for p,i in zip(obj.data.polygons,indices):p.material_index=i
            if not obj.data.uv_layers and (config.get('generate_missing_uvs',False) or obj['export_source_name'].startswith('DORM_INT_')):
                uv=obj.data.uv_layers.new(name='UVMap')
                for p in obj.data.polygons:
                    dominant=max(range(3),key=lambda i:abs(p.normal[i]));axes=[i for i in range(3) if i!=dominant]
                    for li in p.loop_indices:
                        co=obj.data.vertices[obj.data.loops[li].vertex_index].co
                        uv.data[li].uv=(co[axes[0]],co[axes[1]])
            obj.data.calc_loop_triangles()
            if config.get('remove_degenerate_export_faces',False):
                # Blender's loop-triangle area can round to zero even when
                # BMesh reports a tiny positive area after clipping/bevels.
                bad={t.polygon_index for t in obj.data.loop_triangles if t.area<=1e-12}
                if bad:
                    bm=bmesh.new();bm.from_mesh(obj.data);bm.faces.ensure_lookup_table()
                    bmesh.ops.delete(bm,geom=[bm.faces[i] for i in bad],context='FACES_ONLY')
                    bm.to_mesh(obj.data);bm.free();obj.data.update();obj.data.calc_loop_triangles()
            if config.get('repair_degenerate_uvs',False) and obj.data.uv_layers:
                uv=obj.data.uv_layers.active.data
                bad_polygons=set()
                for tri in obj.data.loop_triangles:
                    a,b,c=[uv[i].uv for i in tri.loops]
                    if abs((b.x-a.x)*(c.y-a.y)-(b.y-a.y)*(c.x-a.x))<1e-14:
                        bad_polygons.add(tri.polygon_index)
                for i in bad_polygons:
                    p=obj.data.polygons[i]
                    dominant=max(range(3),key=lambda k:abs(p.normal[k]));axes=[k for k in range(3) if k!=dominant]
                    for li in p.loop_indices:
                        co=obj.data.vertices[obj.data.loops[li].vertex_index].co
                        uv[li].uv=(co[axes[0]],co[axes[1]])
            assert all(t.area>1e-12 for t in obj.data.loop_triangles), 'Degenerate triangles: '+obj['export_source_name']
        bpy.context.view_layer.update()
        points=[o.matrix_world@v.co for o in temporary for v in o.data.vertices]
        row={'source_objects':[o.name for o in objects],
             'triangles':sum(len(o.data.loop_triangles) for o in temporary),
             'min_m':[min(p[i] for p in points) for i in range(3)],
             'max_m':[max(p[i] for p in points) for i in range(3)],
             'materials':sorted({m.name for o in temporary for m in o.data.materials})}
        bpy.ops.export_scene.fbx(
            filepath=str(out/(name+'.fbx')),use_selection=True,object_types={'MESH'},
            global_scale=1.0,apply_unit_scale=True,apply_scale_options='FBX_SCALE_NONE',
            use_space_transform=True,bake_space_transform=False,axis_forward='-Y',axis_up='Z',
            use_mesh_modifiers=True,mesh_smooth_type='FACE',use_triangles=True,
            bake_anim=False,path_mode='AUTO',embed_textures=False)
        report['assets'][name]=row
    finally:
        for obj in temporary:
            if obj.name in bpy.data.objects:bpy.data.objects.remove(obj,do_unlink=True)
        seen=set()
        for data in temporary_data:
            try:
                key=data.as_pointer()
                if key in seen:continue
                seen.add(key)
                if data.users==0:
                    if isinstance(data,bpy.types.Mesh):bpy.data.meshes.remove(data)
                    elif isinstance(data,bpy.types.Curve):bpy.data.curves.remove(data)
            except ReferenceError:pass
try:
    export(body,main_mesh)
    for path,objects in parts.items():
        primaries=[o for o in objects if not o.get('export_support',False)]
        assert len(primaries)==1, (path,[o.name for o in primaries])
        export(objects,path.rsplit('/',1)[1],primaries[0].matrix_world.copy())
finally:
    bpy.ops.object.select_all(action='DESELECT')
    for obj in selected:obj.select_set(True)
    bpy.context.view_layer.objects.active=active
assert original_meshes=={o.name:len(o.data.vertices) for o in sources if o.type=='MESH'}
if main_mesh in report['assets']:
    row=report['assets'][main_mesh]
    report['triangles']=row['triangles'];report['min_m']=row['min_m'];report['max_m']=row['max_m']
log=Path('D:/UEProject/ArcheoDig/Saved/BlenderToUE');log.mkdir(parents=True,exist_ok=True)
(log/(model_id.lower()+'_export.json')).write_text(json.dumps(report,indent=2),encoding='utf-8')
result={name:{'objects':len(row['source_objects']),'triangles':row['triangles'],'materials':len(row['materials'])} for name,row in report['assets'].items()}
