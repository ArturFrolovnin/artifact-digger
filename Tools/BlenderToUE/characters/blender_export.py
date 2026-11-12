"""Validate the live Blender scene; export disposable centimetre copies only."""
import hashlib
import json
import math
from pathlib import Path

import bpy
from mathutils import Matrix

from common import compatible, digest, file_hash, material_key, require, write_json


def skeleton_rows(arm, unit, root_name='root'):
    flip = Matrix.Diagonal((1, -1, 1, 1))
    worlds = {}
    for bone in arm.data.bones:
        location, rotation, scale = (arm.matrix_world @ bone.matrix_local).decompose()
        # FBX float roundtrip produces ~1.7e-5 axis noise on Quinn's ik_foot_r.
        require(max(scale)-min(scale) < 1e-4, 'Non-uniform armature/bone scale: %s %s' % (bone.name,list(scale)))
        m = rotation.to_matrix().to_4x4()
        m.translation = location * (100*unit)
        worlds[bone.name] = flip @ m @ flip
    rows = [dict(name=root_name, parent=None, translation=[0, 0, 0], rotation_xyzw=[0, 0, 0, 1], scale=[1, 1, 1])]
    for bone in arm.data.bones:
        matrix = worlds[bone.parent.name].inverted() @ worlds[bone.name] if bone.parent else worlds[bone.name]
        loc, q, scale = matrix.decompose()
        rows.append(dict(name=bone.name, parent=bone.parent.name if bone.parent else root_name,
                         translation=list(loc), rotation_xyzw=[q.x, q.y, q.z, q.w], scale=list(scale)))
    return rows


def material_values(mat):
    p = next((n for n in mat.node_tree.nodes if n.type == 'BSDF_PRINCIPLED'), None) if mat.use_nodes else None
    value = lambda n, default: p.inputs[n].default_value if p and n in p.inputs else default
    return dict(source_name=mat.name, color=list(value('Base Color', mat.diffuse_color)),
                roughness=float(value('Roughness', .6)), metallic=float(value('Metallic', 0)),
                transmission=float(value('Transmission Weight', 0)),
                vertex_color=bool(p and p.inputs['Base Color'].is_linked and any(n.type == 'VERTEX_COLOR' for n in mat.node_tree.nodes)))


def validate(cfg, reference):
    require(bpy.app.version[:3] == (5, 2, 2), 'Expected Blender 5.2.2, found ' + bpy.app.version_string)
    require(Path(bpy.data.filepath).resolve() == (Path(cfg['project'])/cfg['source_blend']).resolve(), 'Wrong open blend file; refusing to open/overwrite it')
    scene = bpy.context.scene
    require(scene.unit_settings.system == 'METRIC' and abs(scene.unit_settings.scale_length-1) < 1e-8, 'Source scene must use metres')
    arm = bpy.data.objects.get(cfg['armature'])
    require(arm and arm.type == 'ARMATURE', 'Missing configured armature')
    require(cfg['rig']['root_bone'] not in arm.data.bones, 'This profile expects the FBX root represented by the armature object, not a duplicate root bone')
    require(not arm.constraints and not arm.animation_data, 'Armature has constraints/animation/drivers; neutral static export required')
    for pb in arm.pose.bones:
        require(not pb.constraints, 'Bone constraints: ' + pb.name)
        require(max(abs(pb.matrix_basis[i][j] - (1 if i == j else 0)) for i in range(4) for j in range(4)) < 1e-5, 'Non-neutral pose: ' + pb.name)
    require(arm.data.pose_position == 'POSE', 'Use neutral POSE display, not a hidden pose behind REST display')
    loc, rot, scale = arm.matrix_world.decompose()
    require(loc.length < 1e-6 and rot.angle < 1e-5, 'Armature world origin/orientation differs')
    bones = skeleton_rows(arm, scene.unit_settings.scale_length, cfg['rig']['root_bone'])
    comparison = compatible(bones, reference['bones'], cfg['rig'])
    meshes = set()
    for name in cfg['collections']:
        require(name in bpy.data.collections, 'Missing collection: ' + name)
        meshes.update(o for o in bpy.data.collections[name].all_objects if o.type == 'MESH' and not o.hide_render)
    excluded = {o for name in cfg['exclude_collections'] if name in bpy.data.collections for o in bpy.data.collections[name].all_objects}
    meshes = sorted(meshes-excluded, key=lambda o:o.name)
    require(meshes, 'No renderable character meshes selected')
    materials = {}
    fingerprint = hashlib.sha256()
    for ob in meshes:
        mods = [m for m in ob.modifiers if m.type == 'ARMATURE']
        require(len(mods) == 1 and mods[0].object == arm and mods[0].show_viewport and mods[0].show_render, 'Invalid Armature Modifier: ' + ob.name)
        require(mods[0].use_vertex_groups and not mods[0].use_bone_envelopes, 'Vertex weights required: ' + ob.name)
        require(all(m.show_render == m.show_viewport for m in ob.modifiers), 'Viewport/render modifier mismatch: ' + ob.name)
        for v in ob.data.vertices:
            weights = [(ob.vertex_groups[g.group].name, g.weight) for g in v.groups if g.weight > 1e-7]
            require(weights and abs(sum(w for n,w in weights)-1) < .002, 'Unweighted/unnormalized vertex %s:%s' % (ob.name,v.index))
            require(len(weights) <= cfg['max_influences'] and all(n in arm.data.bones for n,w in weights), 'Invalid bone influences: ' + ob.name)
        require(ob.data.polygons, 'Empty geometry: ' + ob.name)
        for slot in ob.material_slots:
            require(slot.material is not None, 'Empty material slot: ' + ob.name)
            mat = slot.material
            key = material_key(mat.name)
            require(key not in materials or materials[key]['source_name'] == mat.name, 'Sanitized material name collision: ' + key)
            materials[key] = material_values(mat)
        fingerprint.update(ob.name.encode())
        fingerprint.update(str([tuple(r) for r in ob.matrix_world]).encode())
        fingerprint.update(str([(m.type, getattr(m, 'levels', None)) for m in ob.modifiers]).encode())
        fingerprint.update(str([(tuple(v.co),[(g.group,g.weight) for g in v.groups]) for v in ob.data.vertices]).encode())
        fingerprint.update(str([tuple(p.vertices) for p in ob.data.polygons]).encode())
        fingerprint.update(str([material_key(s.material.name) for s in ob.material_slots]).encode())
        ev=ob.evaluated_get(bpy.context.evaluated_depsgraph_get())
        evaluated=ev.to_mesh(preserve_all_data_layers=True,depsgraph=bpy.context.evaluated_depsgraph_get())
        try:
            fingerprint.update(str([tuple(v.co) for v in evaluated.vertices]).encode())
            fingerprint.update(str([(tuple(p.vertices),p.material_index,tuple(p.normal)) for p in evaluated.polygons]).encode())
        finally:
            ev.to_mesh_clear()
        # Includes shader edits and complexion colour edits, not just geometry.
        for attr in ob.data.color_attributes:
            fingerprint.update(str([tuple(x.color) for x in attr.data]).encode())
    fingerprint.update(digest(materials).encode())
    fingerprint.update(digest(bones).encode())
    return arm, meshes, dict(status='VALID', bones=bones, comparison=comparison, materials=materials,
                              objects=[o.name for o in meshes], source_scene_dirty=bpy.data.is_dirty,
                              source_file_sha256=file_hash(bpy.data.filepath), scene_hash=fingerprint.hexdigest())


def execute(cfg, reference, export=True):
    window = bpy.context.window
    original_scene = window.scene
    original_active = bpy.context.view_layer.objects.active
    selected = list(bpy.context.selected_objects)
    mode = original_active.mode if original_active else 'OBJECT'
    # Track all temporary datablocks, including those created by FBX roundtrip validation.
    kinds = ('objects','meshes','armatures','materials','images','collections','scenes','actions')
    before = {k:set(getattr(bpy.data,k)) for k in kinds}
    temp = None
    try:
        if mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')
        arm, meshes, report = validate(cfg, reference)
        if not export:
            return report
        temp = bpy.data.scenes.new('__CharacterExport')
        temp.unit_settings.system = 'METRIC'
        temp.unit_settings.scale_length = .01
        window.scene = temp
        # Bake world transforms into *copies* in centimetres, leaving root scale at one.
        rig = arm.copy()
        rig.data = arm.data.copy()
        rig.parent = None
        rig.animation_data_clear()
        rig.matrix_world = Matrix.Identity(4)
        rig.data.transform(Matrix.Scale(100,4) @ arm.matrix_world)
        temp.collection.objects.link(rig)
        copies = []
        mats = {}
        lo = [float('inf')]*3
        hi = [-float('inf')]*3
        deg = bpy.context.evaluated_depsgraph_get()
        # Source objects are evaluated in their own original view layer.
        with bpy.context.temp_override(scene=original_scene, view_layer=original_scene.view_layers[0]):
            deg = bpy.context.evaluated_depsgraph_get()
            for ob in meshes:
                ev = ob.evaluated_get(deg)
                data = bpy.data.meshes.new_from_object(ev, preserve_all_data_layers=True, depsgraph=deg)
                data.transform(Matrix.Scale(100,4) @ ob.matrix_world)
                cp = bpy.data.objects.new('__CharacterPart',data)
                temp.collection.objects.link(cp)
                for group in ob.vertex_groups:
                    cp.vertex_groups.new(name=group.name)
                for vertex in data.vertices:
                    weights=[g for g in vertex.groups if g.weight > 1e-7]
                    require(weights and len(weights) <= cfg['max_influences'], 'Evaluated modifier lost/exceeded influences: ' + ob.name)
                    require(abs(sum(g.weight for g in weights)-1) < .002, 'Evaluated weights are not normalized: ' + ob.name)
                    require(all(cp.vertex_groups[g.group].name in rig.data.bones for g in weights), 'Evaluated weights target an unknown bone: ' + ob.name)
                for i, slot in enumerate(ob.material_slots):
                    key = material_key(slot.material.name)
                    if key not in mats:
                        mats[key] = bpy.data.materials.new(key)
                        mats[key].diffuse_color = report['materials'][key]['color']
                    data.materials[i] = mats[key]
                # UVs are technical box projections on copies when an authored UV is absent.
                if not data.uv_layers:
                    uv = data.uv_layers.new(name='UVMap')
                    for poly in data.polygons:
                        axis = max(range(3),key=lambda i:abs(poly.normal[i]))
                        dims = [i for i in range(3) if i != axis]
                        for loop in poly.loop_indices:
                            v = data.vertices[data.loops[loop].vertex_index].co
                            uv.data[loop].uv = (v[dims[0]]*.01,v[dims[1]]*.01)
                for v in data.vertices:
                    require(all(math.isfinite(x) for x in v.co), 'Non-finite evaluated vertex')
                    for i in range(3):lo[i]=min(lo[i],v.co[i]/100);hi[i]=max(hi[i],v.co[i]/100)
                require(all(p.area > 1e-14 for p in data.polygons), 'Degenerate evaluated polygons: ' + ob.name)
                modifier = cp.modifiers.new('Skin','ARMATURE')
                modifier.object = rig
                cp.parent = rig
                cp.matrix_world = Matrix.Identity(4)
                copies.append(cp)
        height = (hi[2]-lo[2])*100
        require(cfg['height_range_cm'][0] <= height <= cfg['height_range_cm'][1], 'Unexpected character height: %.3f cm' % height)
        bpy.context.view_layer.update()
        bpy.ops.object.select_all(action='DESELECT')
        for cp in copies:cp.select_set(True)
        bpy.context.view_layer.objects.active = copies[0]
        bpy.ops.object.join()
        combined = copies[0]
        combined.name = cfg['unreal_asset'].rsplit('/',1)[1]
        rig.select_set(True)
        # Blender IDs are globally unique, even across scenes. Override *only* the
        # disposable root's serialized FBX name; do not rename the source armature.
        from io_scene_fbx import fbx_utils, parse_fbx
        old_name = fbx_utils.get_blenderID_name
        def export_name(value):
            return cfg['rig']['root_bone'] if value == rig else old_name(value)
        fbx_utils.get_blenderID_name = export_name
        try:
            bpy.ops.export_scene.fbx(filepath=cfg['fbx'], use_selection=True, object_types={'ARMATURE','MESH'},
                global_scale=1, apply_unit_scale=True, apply_scale_options='FBX_SCALE_NONE', axis_forward='-Y', axis_up='Z',
                use_space_transform=True, bake_space_transform=False, use_mesh_modifiers=True, use_triangles=True,
                mesh_smooth_type='FACE', add_leaf_bones=False, use_armature_deform_only=False,
                primary_bone_axis='Y', secondary_bone_axis='X', armature_nodetype='ROOT', bake_anim=False,
                path_mode='STRIP', use_custom_props=False)
        finally:
            fbx_utils.get_blenderID_name = old_name
        root, version = parse_fbx.parse(cfg['fbx'])
        nodes = next(e for e in root.elems if e.id == b'Objects')
        models = [e for e in nodes.elems if e.id == b'Model']
        model_names = [e.props[1].split(b'\x00')[0].decode() for e in models]
        require(cfg['rig']['root_bone'] in model_names and len(models)==len(report['bones'])+1, 'Unexpected FBX objects/root; refusing import: '+str(model_names))
        require(not any(e.id == b'AnimationStack' for e in nodes.elems), 'Animation unexpectedly exported')
        # Re-read our own FBX in a disposable scene before Unreal is allowed to import.
        for ob in list(temp.objects):bpy.data.objects.remove(ob,do_unlink=True)
        bpy.ops.import_scene.fbx(filepath=cfg['fbx'],use_anim=False,use_image_search=False,automatic_bone_orientation=False)
        roundtrip = [o for o in temp.objects if o.type=='ARMATURE']
        require(len(roundtrip)==1, 'Export roundtrip produced multiple skeletons')
        roundtrip_check = compatible(skeleton_rows(roundtrip[0], .01, cfg['rig']['root_bone']),reference['bones'],cfg['rig'])
        report.update(status='EXPORTED', fbx=cfg['fbx'], fbx_sha256=file_hash(cfg['fbx']),
                      bounds_m=[lo,hi], height_cm=height, roundtrip=roundtrip_check,
                      config_hash=digest(cfg), reference_hash=reference['skeleton_hash'])
        write_json(Path(cfg['log_dir'])/'export.json', report)
        return report
    finally:
        window.scene = original_scene
        for kind in kinds:
            pool = getattr(bpy.data,kind)
            for item in list(pool):
                if item not in before[kind]:
                    pool.remove(item,do_unlink=True)
        bpy.ops.object.select_all(action='DESELECT')
        for ob in selected:ob.select_set(True)
        bpy.context.view_layer.objects.active = original_active
        if original_active and mode != 'OBJECT':bpy.ops.object.mode_set(mode=mode)
        require(all(set(getattr(bpy.data,k)) == before[k] for k in kinds), 'Export leaked temporary Blender datablocks')
        if 'report' in locals():
            _, _, after = validate(cfg, reference)
            require(after['scene_hash']==report['scene_hash'] and after['source_file_sha256']==report['source_file_sha256'],
                    'Source geometry/rig/materials or blend file changed during export')
            report['source_unchanged']=True
            if export and report.get('status')=='EXPORTED':
                write_json(Path(cfg['log_dir'])/'export.json',report)
