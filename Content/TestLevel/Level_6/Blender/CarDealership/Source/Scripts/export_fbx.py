"""Export the current finished car dealership without rebuilding its editable geometry."""
import bpy, bmesh, json
from pathlib import Path
out = Path('D:/UEProject/ArcheoDig/Content/TestLevel/Level_6/Blender/CarDealership/Source')
root = bpy.data.objects['CarDealership_ROOT']
assert root.location.length < 1e-6
assert all(abs(s-1)<1e-6 for s in root.scale)
assert bpy.context.scene.unit_settings.scale_length == 1
originals = [o for o in root.children_recursive if o.type in {'MESH','CURVE','FONT'}]
assert len(originals) == 169
assert all(all(abs(s-1)<1e-6 for s in o.scale) for o in originals)
selected = list(bpy.context.selected_objects)
active = bpy.context.view_layer.objects.active
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=str(out/'CarDealership_Blockout.blend'))
temporary = []
report = {'objects':len(originals), 'zero_area_removed':0, 'source_geometry_unchanged':True}
materials = {}
try:
    bpy.ops.object.select_all(action='DESELECT')
    dg = bpy.context.evaluated_depsgraph_get()
    for src in originals:
        me = bpy.data.meshes.new_from_object(src.evaluated_get(dg),depsgraph=dg)
        o = bpy.data.objects.new('EXPORT_'+src.name,me)
        bpy.context.scene.collection.objects.link(o)
        temporary.append(o)
        me.transform(src.matrix_world)
        bm=bmesh.new(); bm.from_mesh(me)
        bad=[f for f in bm.faces if f.calc_area()<1e-12]
        report['zero_area_removed']+=len(bad)
        if bad: bmesh.ops.delete(bm,geom=bad,context='FACES')
        bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
        bm.to_mesh(me); bm.free(); me.update()
        uv=me.uv_layers.active or me.uv_layers.new(name='UVMap')
        for f in me.polygons:
            axes=[i for i in range(3) if i!=max(range(3),key=lambda i:abs(f.normal[i]))]
            for li in f.loop_indices:
                co=me.vertices[me.loops[li].vertex_index].co
                uv.data[li].uv=(co[axes[0]],co[axes[1]])
        for m in me.materials:
            if m:
                p=next(n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED')
                materials[m.name]={'color':list(p.inputs['Base Color'].default_value),'roughness':p.inputs['Roughness'].default_value,'metallic':p.inputs['Metallic'].default_value}
        o.select_set(True)
    bpy.context.view_layer.objects.active=temporary[0]
    pts=[v.co for o in temporary for v in o.data.vertices]
    report['min_m']=[min(p[i] for p in pts) for i in range(3)]
    report['max_m']=[max(p[i] for p in pts) for i in range(3)]
    report['dimensions_m']=[report['max_m'][i]-report['min_m'][i] for i in range(3)]
    report['zero_area_remaining']=sum(p.area<1e-12 for o in temporary for p in o.data.polygons)
    assert report['zero_area_remaining']==0 and abs(report['min_m'][2])<1e-6
    bpy.ops.export_scene.fbx(filepath=str(out/'SM_CarDealership_Blockout.fbx'),use_selection=True,object_types={'MESH'},global_scale=1.,apply_unit_scale=True,apply_scale_options='FBX_SCALE_NONE',axis_forward='-Y',axis_up='Z',use_space_transform=True,bake_space_transform=False,use_mesh_modifiers=True,mesh_smooth_type='FACE',use_triangles=True,bake_anim=False,path_mode='AUTO')
finally:
    for o in temporary:
        me=o.data; bpy.data.objects.remove(o,do_unlink=True); bpy.data.meshes.remove(me)
    for o in selected:o.select_set(True)
    bpy.context.view_layer.objects.active=active
(out/'export_validation.txt').write_text(json.dumps(report,indent=2))
(out/'material_manifest.txt').write_text(json.dumps(materials,indent=2))
result=report

