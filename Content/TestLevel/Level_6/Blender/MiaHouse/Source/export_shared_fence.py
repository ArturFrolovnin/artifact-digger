"""Placement variant: retain the player's shared fence; omit Mia's duplicate side."""
import bpy, bmesh, json
from pathlib import Path
out = Path(__file__).resolve().parent
assert Path(bpy.data.filepath) == out / 'MiaHouse_Blockout.blend'
assert bpy.context.mode == 'OBJECT'
originals = [o for o in bpy.data.collections['Fence'].all_objects if o.type == 'MESH' and not o.name.startswith('LeftBoundary_')]
selected = list(bpy.context.selected_objects)
active = bpy.context.view_layer.objects.active
temporary = []
try:
    bpy.ops.object.select_all(action='DESELECT')
    dg = bpy.context.evaluated_depsgraph_get()
    for src in originals:
        me = bpy.data.meshes.new_from_object(src.evaluated_get(dg), depsgraph=dg)
        me.transform(src.matrix_world)
        obj = bpy.data.objects.new('EXPORT_' + src.name, me)
        bpy.context.scene.collection.objects.link(obj)
        temporary.append(obj)
        bm = bmesh.new(); bm.from_mesh(me)
        bad = [f for f in bm.faces if f.calc_area() < 1e-12]
        if bad: bmesh.ops.delete(bm, geom=bad, context='FACES')
        bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
        bm.to_mesh(me); bm.free(); me.update()
        if not me.uv_layers:
            uv = me.uv_layers.new(name='UVMap')
            for f in me.polygons:
                axes = [i for i in range(3) if i != max(range(3), key=lambda i: abs(f.normal[i]))]
                for li in f.loop_indices:
                    p = me.vertices[me.loops[li].vertex_index].co
                    uv.data[li].uv = (p[axes[0]], p[axes[1]])
        obj.select_set(True)
    bpy.context.view_layer.objects.active = temporary[0]
    bpy.ops.export_scene.fbx(filepath=str(out/'SM_MiaHouse_Fence_SharedBoundary.fbx'), use_selection=True, object_types={'MESH'}, global_scale=1., apply_unit_scale=True, apply_scale_options='FBX_SCALE_NONE', axis_forward='-Y', axis_up='Z', use_space_transform=True, bake_space_transform=False, use_mesh_modifiers=True, mesh_smooth_type='FACE', use_triangles=True, bake_anim=False, path_mode='AUTO')
finally:
    for obj in temporary:
        me = obj.data
        bpy.data.objects.remove(obj, do_unlink=True)
        bpy.data.meshes.remove(me)
    for obj in selected: obj.select_set(True)
    bpy.context.view_layer.objects.active = active
result = {'objects':len(originals),'omitted':'LeftBoundary_* only','source_unchanged':True}
