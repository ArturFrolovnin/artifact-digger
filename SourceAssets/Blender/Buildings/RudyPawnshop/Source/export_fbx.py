"""Run in the open RudyPawnshop Blender scene; preserve editable lettering."""
import bpy
from pathlib import Path

out = Path(bpy.data.filepath).parent
collection = bpy.data.collections['BLD_RudyPawnshop']
objects = [o for o in collection.all_objects if o.type in {'MESH', 'FONT'}]
selected = list(bpy.context.selected_objects)
active = bpy.context.view_layer.objects.active
temporary = []
try:
    for o in selected:
        o.select_set(False)
    for original in objects:
        copy = original.copy()
        copy.data = original.data.copy()
        collection.objects.link(copy)
        temporary.append(copy)
        copy.select_set(True)
    bpy.context.view_layer.objects.active = temporary[0]
    bpy.ops.object.convert(target='MESH')
    for o in temporary:
        uv = o.data.uv_layers.active or o.data.uv_layers.new(name='UVMap')
        for face in o.data.polygons:
            dominant = max(range(3), key=lambda i: abs(face.normal[i]))
            axes = [i for i in range(3) if i != dominant]
            for index in face.loop_indices:
                co = o.data.vertices[o.data.loops[index].vertex_index].co
                uv.data[index].uv = (co[axes[0]], co[axes[1]])
    bpy.ops.export_scene.fbx(
        filepath=str(out / 'SM_RudyPawnshop.fbx'), use_selection=True,
        object_types={'MESH'}, global_scale=1.0, apply_unit_scale=True,
        apply_scale_options='FBX_SCALE_NONE', axis_forward='-Y', axis_up='Z',
        use_space_transform=True, bake_space_transform=False,
        use_mesh_modifiers=True, mesh_smooth_type='FACE', use_triangles=True,
        bake_anim=False, path_mode='AUTO')
finally:
    for o in temporary:
        bpy.data.objects.remove(o, do_unlink=True)
    for o in selected:
        o.select_set(True)
    bpy.context.view_layer.objects.active = active
result = {'fbx': str(out / 'SM_RudyPawnshop.fbx'), 'objects': len(objects)}
