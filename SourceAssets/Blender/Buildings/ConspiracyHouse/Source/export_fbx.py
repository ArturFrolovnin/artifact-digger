"""Export the existing editable Conspiracy house; never rebuild or save temporary geometry."""
import bpy, bmesh, json, math
from pathlib import Path

out = Path(__file__).resolve().parent
root = bpy.data.objects['ConspiracyHouse_ROOT']
building = bpy.data.collections['BLD_ConspiracyHouse']
assert bpy.data.filepath == str(out / 'ConspiracyHouse_Blockout.blend').replace('/', '\\') or Path(bpy.data.filepath) == out / 'ConspiracyHouse_Blockout.blend'
assert root.location.length < 1e-6 and all(abs(s-1)<1e-6 for s in root.scale)
assert bpy.context.scene.unit_settings.scale_length == 1
assert bpy.context.mode == 'OBJECT'
groups = {'Blockout': [], 'Equipment': [], 'Fence': [], 'Garden': [], 'Props': [], 'Pathways': []}
for obj in building.all_objects:
    if obj.type not in {'MESH', 'CURVE', 'FONT'}:
        continue
    names = {c.name for c in obj.users_collection}
    key = 'Equipment' if names & {'Antennas', 'Telescope', 'ExperimentalDevices'} or obj.name in {'Coax_To_Workshop', 'Secondary_Coax', 'Electrical_Junction'} else 'Fence' if 'Fence' in names else 'Pathways' if 'Pathways' in names else 'Garden' if 'Garden' in names else 'Props' if 'ExteriorProps' in names else 'Blockout'
    groups[key].append(obj)
selected = list(bpy.context.selected_objects)
active = bpy.context.view_layer.objects.active
report = {'source_unchanged': True, 'units': 'metres', 'axis_forward': '-Y', 'axis_up': 'Z', 'groups': {}}
manifest = {}
dg = bpy.context.evaluated_depsgraph_get()
for key, originals in groups.items():
    temporary = []
    removed = 0
    try:
        bpy.ops.object.select_all(action='DESELECT')
        for src in originals:
            me = bpy.data.meshes.new_from_object(src.evaluated_get(dg), depsgraph=dg)
            me.transform(src.matrix_world)
            obj = bpy.data.objects.new('EXPORT_' + src.name, me)
            bpy.context.scene.collection.objects.link(obj)
            temporary.append(obj)
            bm = bmesh.new(); bm.from_mesh(me)
            bad = [f for f in bm.faces if f.calc_area() < 1e-12]
            removed += len(bad)
            if bad: bmesh.ops.delete(bm, geom=bad, context='FACES')
            bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
            bm.to_mesh(me); bm.free(); me.update()
            if not me.uv_layers:
                uv = me.uv_layers.new(name='UVMap')
                for face in me.polygons:
                    axes = [i for i in range(3) if i != max(range(3), key=lambda i: abs(face.normal[i]))]
                    for li in face.loop_indices:
                        co = me.vertices[me.loops[li].vertex_index].co
                        uv.data[li].uv = (co[axes[0]], co[axes[1]])
            for mat in me.materials:
                if mat and mat.name not in manifest:
                    node = next(n for n in mat.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
                    manifest[mat.name] = {k: list(node.inputs[v].default_value) if k in {'color','emission'} else node.inputs[v].default_value for k,v in {'color':'Base Color','roughness':'Roughness','metallic':'Metallic','alpha':'Alpha','transmission':'Transmission Weight','emission':'Emission Color','emission_strength':'Emission Strength'}.items()}
            obj.select_set(True)
        bpy.context.view_layer.objects.active = temporary[0]
        pts = [v.co for o in temporary for v in o.data.vertices]
        lo = [min(v[i] for v in pts) for i in range(3)]
        hi = [max(v[i] for v in pts) for i in range(3)]
        assert all(math.isfinite(v) for p in pts for v in p)
        triangles = sum(len(p.vertices)-2 for o in temporary for p in o.data.polygons)
        bpy.ops.export_scene.fbx(filepath=str(out / ('SM_ConspiracyHouse_' + key + '.fbx')), use_selection=True, object_types={'MESH'}, global_scale=1., apply_unit_scale=True, apply_scale_options='FBX_SCALE_NONE', axis_forward='-Y', axis_up='Z', use_space_transform=True, bake_space_transform=False, use_mesh_modifiers=True, mesh_smooth_type='FACE', use_triangles=True, bake_anim=False, path_mode='AUTO')
        report['groups'][key] = {'objects':len(originals),'min_m':lo,'max_m':hi,'dimensions_m':[hi[i]-lo[i] for i in range(3)],'triangles':triangles,'zero_area_removed':removed}
    finally:
        for obj in temporary:
            me = obj.data
            bpy.data.objects.remove(obj, do_unlink=True)
            bpy.data.meshes.remove(me)
for obj in selected: obj.select_set(True)
bpy.context.view_layer.objects.active = active
(out / 'export_validation.txt').write_text(json.dumps(report, indent=2), encoding='utf-8')
(out / 'material_manifest.txt').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
result = report
