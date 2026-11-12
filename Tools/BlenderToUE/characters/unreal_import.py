"""Conservative FbxFactory import/reimport, reusing the existing Quinn Skeleton."""
from pathlib import Path
import hashlib

import unreal

from common import compatible, digest, expected_ue_bounds, file_hash, require, validate_bounds, write_json


def dirty_content():
    return {p.get_path_name() for p in unreal.EditorLoadingAndSavingUtils.get_dirty_content_packages()}


def dirty_maps():
    return sorted(p.get_path_name() for p in unreal.EditorLoadingAndSavingUtils.get_dirty_map_packages())


def mesh_bones(mesh):
    modifier = unreal.SkeletonModifier()
    require(modifier.set_skeletal_mesh(mesh), 'Cannot read mesh reference skeleton')
    rows = []
    for n in modifier.get_all_bone_names():
        t = modifier.get_bone_transform(n, False)
        q, v, s = t.rotation, t.translation, t.scale3d
        parent = str(modifier.get_parent_name(n))
        rows.append(dict(name=str(n), parent=None if parent == 'None' else parent,
                         translation=[v.x,v.y,v.z], rotation_xyzw=[q.x,q.y,q.z,q.w], scale=[s.x,s.y,s.z]))
    # Read-only modifier: never call commit_skeleton_to_skeletal_mesh().
    return rows


def skeleton_hash(skeleton):
    return hashlib.sha256(skeleton.get_reference_pose().export_text().encode()).hexdigest()


def package_hash(asset):
    path = Path(unreal.Paths.project_content_dir()) / (asset.get_path_name().split('.')[0].removeprefix('/Game/') + '.uasset')
    require(path.is_file(), 'Reference asset is not saved: ' + str(path))
    return file_hash(path)


def discover_reference(cfg):
    require(unreal.Paths.project_dir().replace('\\','/').rstrip('/').casefold() == cfg['project'].replace('\\','/').rstrip('/').casefold(), 'Wrong Unreal project')
    require(unreal.SystemLibrary.get_engine_version().startswith('5.8.'), 'Expected Unreal Engine 5.8')
    reg = unreal.AssetRegistryHelpers.get_asset_registry()
    matches = [a for a in reg.get_assets_by_path('/Game',recursive=True)
               if str(a.asset_name) == cfg['rig']['reference_mesh_name'] and str(a.asset_class_path.asset_name) == 'SkeletalMesh']
    require(len(matches)==1, 'Expected exactly one original ' + cfg['rig']['reference_mesh_name'])
    mesh = matches[0].get_asset()
    sk = mesh.skeleton
    require(isinstance(sk,unreal.Skeleton), 'Quinn mesh has no Skeleton')
    require(sk.get_path_name().split('.')[0] not in dirty_content(), 'Reference Skeleton has unsaved changes; refusing import')
    reference = dict(mesh=mesh.get_path_name(), skeleton=sk.get_path_name(), bones=mesh_bones(mesh),
                     skeleton_hash=skeleton_hash(sk), skeleton_file_hash=package_hash(sk),
                     quinn_file_hash=package_hash(mesh), dirty_maps=dirty_maps(),
                     reference_fbx_hash=file_hash(Path(cfg['project'])/cfg['rig']['reference_fbx']))
    write_json(Path(cfg['log_dir'])/'reference.json',reference)
    return reference


def slots(mesh):
    return {str(s.material_slot_name): s.material_interface for s in mesh.materials}


def bounds(mesh):
    b = mesh.get_imported_bounds()
    o, e = b.origin, b.box_extent
    return [[o.x-e.x,o.y-e.y,o.z-e.z],[o.x+e.x,o.y+e.y,o.z+e.z]]


def validate_mesh(cfg, mesh, reference, exported):
    require(isinstance(mesh,unreal.SkeletalMesh), 'Target is not a SkeletalMesh')
    require(mesh.get_path_name().split('.')[0] == cfg['unreal_asset'], 'Unexpected asset path')
    require(mesh.skeleton.get_path_name() == reference['skeleton'], 'Imported mesh uses another Skeleton')
    comparison = compatible(mesh_bones(mesh),reference['bones'],cfg['rig'])
    actual = bounds(mesh)
    validate_bounds(actual,expected_ue_bounds(exported['bounds_m']),cfg['bounds_tolerance_cm'])
    names = list(slots(mesh))
    require(len(names)==len(set(names)) and set(names)==set(exported['materials']), 'Material slot set differs: ' + str(names))
    require(all(slots(mesh).values()), 'Unassigned material slots')
    require(mesh.physics_asset is None, 'Unexpected physics asset created')
    return dict(asset=mesh.get_path_name(), skeleton=mesh.skeleton.get_path_name(), bones=len(mesh_bones(mesh)),
                bounds_cm=actual, rest_pose=comparison, materials={n:m.get_path_name() for n,m in slots(mesh).items()})


def make_material(cfg, name, values):
    path = cfg['unreal_materials']+'/'+name
    if unreal.EditorAssetLibrary.does_asset_exist(path):
        mat = unreal.load_asset(path)
        require(isinstance(mat,unreal.MaterialInterface), 'Material path occupied: '+path)
        return mat, False
    mat = unreal.AssetToolsHelpers.get_asset_tools().create_asset(name,cfg['unreal_materials'],unreal.Material,unreal.MaterialFactoryNew())
    require(mat, 'Cannot create material: '+name)
    lib = unreal.MaterialEditingLibrary
    mat.set_editor_property('two_sided',True)
    def constant(value,prop,y):
        n = lib.create_material_expression(mat,unreal.MaterialExpressionConstant,-300,y)
        n.set_editor_property('r',value)
        require(lib.connect_material_property(n,'',prop), 'Material connection failed')
    if values['vertex_color']:
        n = lib.create_material_expression(mat,unreal.MaterialExpressionVertexColor,-300,0)
        lib.connect_material_property(n,'RGB',unreal.MaterialProperty.MP_BASE_COLOR)
    else:
        n = lib.create_material_expression(mat,unreal.MaterialExpressionConstant3Vector,-300,0)
        n.set_editor_property('constant',unreal.LinearColor(*values['color']))
        lib.connect_material_property(n,'',unreal.MaterialProperty.MP_BASE_COLOR)
    constant(values['roughness'],unreal.MaterialProperty.MP_ROUGHNESS,150)
    constant(values['metallic'],unreal.MaterialProperty.MP_METALLIC,250)
    if values['transmission'] > .5:
        mat.set_editor_property('blend_mode',unreal.BlendMode.BLEND_TRANSLUCENT)
        mat.set_editor_property('translucency_lighting_mode',unreal.TranslucencyLightingMode.TLM_SURFACE_PER_PIXEL_LIGHTING)
        constant(.10,unreal.MaterialProperty.MP_OPACITY,350)
    lib.recompile_material(mat)
    return mat, True


def execute(cfg, reference, exported, require_existing=False):
    target = cfg['unreal_asset']
    require(target not in {reference['mesh'].split('.')[0],reference['skeleton'].split('.')[0]}, 'Target is a protected reference asset')
    sk = unreal.load_asset(reference['skeleton'])
    require(skeleton_hash(sk)==reference['skeleton_hash'] and package_hash(sk)==reference['skeleton_file_hash'], 'Skeleton changed since preflight')
    require(file_hash(cfg['fbx'])==exported['fbx_sha256'], 'Stale or changed FBX')
    require(exported['config_hash']==digest(cfg) and exported['reference_hash']==reference['skeleton_hash'], 'Stale export manifest')
    compatible(exported['bones'],reference['bones'],cfg['rig'])
    existed = unreal.EditorAssetLibrary.does_asset_exist(target)
    require(not require_existing or existed, 'Reimport requested, but target does not exist')
    mesh = unreal.load_asset(target) if existed else None
    require(not existed or isinstance(mesh,unreal.SkeletalMesh), 'Target path occupied by another asset type')
    require(target not in dirty_content(), 'Target has unsaved edits; refusing overwrite')
    if existed:
        require(mesh.skeleton==sk, 'Existing target uses another Skeleton')
        prior=mesh.get_editor_property('asset_import_data')
        require(isinstance(prior,unreal.FbxSkeletalMeshImportData), 'Existing target does not use the configured FBX import path')
        require(not prior.get_editor_property('update_skeleton_reference_pose') and not prior.get_editor_property('use_t0_as_ref_pose'), 'Existing import settings would update the protected reference pose')
        require(mesh.physics_asset is None, 'Existing PhysicsAsset binding needs a separate configured workflow')
    old_slots = slots(mesh) if existed else {}
    require(not existed or all(old_slots.values()), 'Existing mesh has empty material assignments; resolve before reimport')
    old_order = [str(s.material_slot_name) for s in mesh.materials] if existed else []
    # Material additions/removals need explicit configuration/review; never silently remap sections.
    require(not existed or set(old_order)==set(exported['materials']), 'Material slot set changed; refusing destructive reimport')
    original_dirty = dirty_content()
    original_maps = dirty_maps()
    reg = unreal.AssetRegistryHelpers.get_asset_registry()
    asset_paths = lambda:{str(a.package_name) for a in reg.get_all_assets()}
    before_assets = asset_paths()
    cv = 'Interchange.FeatureFlags.Import.FBX'
    old_cv = unreal.SystemLibrary.get_console_variable_int_value(cv)
    created = []
    try:
        unreal.SystemLibrary.execute_console_command(None,cv+' 0')
        options = unreal.FbxImportUI()
        options.automated_import_should_detect_type=False
        options.import_mesh=True
        options.import_as_skeletal=True
        options.mesh_type_to_import=unreal.FBXImportType.FBXIT_SKELETAL_MESH
        options.original_import_type=unreal.FBXImportType.FBXIT_SKELETAL_MESH
        options.skeleton=sk
        options.import_materials=False
        options.import_textures=False
        options.import_animations=False
        options.create_physics_asset=False
        options.override_full_name=True
        options.reset_to_fbx_on_material_conflict=False
        data=options.skeletal_mesh_import_data
        data.set_editor_properties(dict(
            update_skeleton_reference_pose=False, use_t0_as_ref_pose=False,
            import_morph_targets=False, import_mesh_lods=False, import_meshes_in_bone_hierarchy=True,
            import_uniform_scale=1, import_translation=unreal.Vector(0,0,0), import_rotation=unreal.Rotator(0,0,0),
            convert_scene=True, convert_scene_unit=True, force_front_x_axis=False,
            reorder_material_to_fbx_order=False, keep_sections_separate=False,
            vertex_color_import_option=unreal.VertexColorImportOption.REPLACE,
            normal_import_method=unreal.FBXNormalImportMethod.FBXNIM_IMPORT_NORMALS))
        require(not data.get_editor_property('update_skeleton_reference_pose') and not data.get_editor_property('use_t0_as_ref_pose'),
                'Cannot disable Skeleton reference-pose updates')
        task=unreal.AssetImportTask()
        task.filename=cfg['fbx']
        task.destination_path=target.rsplit('/',1)[0]
        task.destination_name=target.rsplit('/',1)[1]
        task.automated=True
        task.async_=False
        task.replace_existing=existed
        task.replace_existing_settings=False
        task.save=False
        task.options=options
        task.factory=unreal.FbxFactory()
        unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
        require(task.imported_object_paths and all(p.split('.')[0]==target for p in task.imported_object_paths), 'Importer created unexpected assets: '+str(task.imported_object_paths))
        mesh=unreal.load_asset(target)
        require(isinstance(mesh,unreal.SkeletalMesh) and mesh.skeleton==sk, 'Import did not produce the expected skeletal mesh')
        require(skeleton_hash(sk)==reference['skeleton_hash'], 'STOP: importer changed Skeleton reference pose')
        require(package_hash(sk)==reference['skeleton_file_hash'], 'STOP: Skeleton file changed')
        require(set(slots(mesh))==set(exported['materials']), 'FBX material slot names differ from manifest')
        if existed:
            # Preserve both exact slot order and every user-authored material assignment.
            require([str(s.material_slot_name) for s in mesh.materials]==old_order, 'Importer changed material slot order; target left unsaved')
        assigned=list(mesh.materials)
        for s in assigned:
            name=str(s.material_slot_name)
            if existed:
                s.material_interface=old_slots[name]
            else:
                mat,new=make_material(cfg,name,exported['materials'][name])
                s.material_interface=mat
                if new:created.append(mat)
        mesh.set_editor_property('materials',assigned)
        result=validate_mesh(cfg,mesh,reference,exported)
        require(skeleton_hash(sk)==reference['skeleton_hash'] and package_hash(sk)==reference['skeleton_file_hash'], 'STOP: protected Skeleton changed')
        require(package_hash(unreal.load_asset(reference['mesh']))==reference['quinn_file_hash'], 'Quinn asset file changed')
        require(file_hash(Path(cfg['project'])/cfg['rig']['reference_fbx'])==reference['reference_fbx_hash'], 'Original Quinn FBX changed')
        allowed={target}|{m.get_path_name().split('.')[0] for m in created}
        require((asset_paths()-before_assets)<=allowed, 'Unexpected assets created; nothing saved')
        require((dirty_content()-original_dirty)<=allowed, 'Unexpected package dirtied; nothing saved')
        require(dirty_maps()==original_maps, 'Map dirty state changed; nothing saved')
        for mat in created:
            require(unreal.EditorAssetLibrary.save_loaded_asset(mat,only_if_is_dirty=True), 'Cannot save material')
        require(unreal.EditorAssetLibrary.save_loaded_asset(mesh,only_if_is_dirty=True), 'Cannot save mesh')
        require(package_hash(sk)==reference['skeleton_file_hash'] and skeleton_hash(sk)==reference['skeleton_hash'], 'Protected Skeleton changed after save')
        result.update(status='SUCCESS',operation='REIMPORT' if existed else 'IMPORT',
                      changed_assets=sorted(allowed),skeleton_unchanged=True,maps_unchanged=True,
                      fbx_sha256=exported['fbx_sha256'],scene_hash=exported['scene_hash'],
                      config_hash=exported['config_hash'],skeleton_hash=reference['skeleton_hash'],
                      asset_file_hash=package_hash(mesh),
                      material_approximations='Base PBR constants + complexion vertex colour; Blender procedural textures are not baked')
        write_json(Path(cfg['log_dir'])/'import.json',result)
        return result
    finally:
        unreal.SystemLibrary.execute_console_command(None,cv+' '+str(old_cv))
