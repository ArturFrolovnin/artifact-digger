"""Configured variant of the proven FBX asset-task workflow. Never edits maps.

Called by finish_ue_import.py with IMPORT_CONFIG; names, parts and material values
come from the model configuration and manifests, not hard-coded model geometry.
"""
import unreal,json,re,traceback
from pathlib import Path

project=Path(unreal.Paths.project_dir()).resolve()
cfg=IMPORT_CONFIG
source=project/Path(cfg['source_blend']).parent
log=project/'Saved/BlenderToUE';log.mkdir(parents=True,exist_ok=True)
model=cfg['model_id'].lower()
base=cfg['unreal_asset'].rsplit('/',1)[0]
manifest=json.loads((source/cfg.get('material_manifest','material_manifest.json')).read_text(encoding='utf-8'))
expected=json.loads((log/(model+'_export.json')).read_text(encoding='utf-8'))['assets']
assets=unreal.AssetToolsHelpers.get_asset_tools();lib=unreal.MaterialEditingLibrary
sub=unreal.get_editor_subsystem(unreal.StaticMeshEditorSubsystem)
def key(name):return re.sub(r'[^A-Za-z0-9_]','_',str(name))
def maps():return sorted(p.get_path_name() for p in unreal.EditorLoadingAndSavingUtils.get_dirty_map_packages())
def instances(mesh):
    return sorted((a.get_path_name(),re.sub(r'0x[0-9A-Fa-f]+','PTR',str(a.get_actor_transform())),str([[m.get_path_name() if m else None for m in c.get_editor_property('override_materials')] for c in a.get_components_by_class(unreal.StaticMeshComponent) if c.static_mesh==mesh])) for a in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors() if any(c.static_mesh==mesh for c in a.get_components_by_class(unreal.StaticMeshComponent)))
def scalar(mat,value,prop,y):
    n=lib.create_material_expression(mat,unreal.MaterialExpressionConstant,-300,y);n.set_editor_property('r',value);assert lib.connect_material_property(n,'',prop)
def color(mat,value,prop,y):
    n=lib.create_material_expression(mat,unreal.MaterialExpressionConstant3Vector,-300,y);n.set_editor_property('constant',unreal.LinearColor(*value));assert lib.connect_material_property(n,'',prop)
def configure_complex_collision(mesh):
    body=mesh.get_editor_property('body_setup')
    if sub.get_simple_collision_count(mesh):
        assert cfg.get('remove_generated_simple_collision',False),'Unexpected simple collision; refusing to delete it'
        geom=json.loads(unreal.ToolsetLibrary.get_object_properties(body,['aggGeom']))['aggGeom']
        shapes=[s for group in geom.values() if isinstance(group,list) for s in group]
        assert shapes and all(s.get('bIsGenerated',False) for s in shapes),'Authored collision found; refusing to delete it'
    body.set_editor_property('collision_trace_flag',unreal.CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE)
    # Recook and refresh components; changing the flag alone may leave old hulls.
    assert sub.remove_collisions(mesh),'Failed to refresh complex collision'
    assert sub.get_simple_collision_count(mesh)==0
    assert sub.get_collision_complexity(mesh)==unreal.CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE

def material(name,old):
    # Keep authored assignments; WorldGrid/DefaultMaterial are missing materials.
    previous=old.get(key(name))
    if previous and previous.get_path_name().startswith('/Game/'):return previous
    # Rudy's manifest describes only its new interior materials.
    existing=unreal.load_asset(cfg['unreal_materials']+'/'+key(name))
    if existing:return existing
    values=next((p for n,p in manifest.items() if key(n)==key(name)),None)
    assert values is not None,'Missing material manifest: '+name
    path=values.get('unreal_material',cfg['unreal_materials']+'/'+key(name))
    mat=unreal.load_asset(path)
    if mat:return mat
    mat=assets.create_asset(key(name),cfg['unreal_materials'],unreal.Material,unreal.MaterialFactoryNew());assert mat
    mat.set_editor_property('two_sided',True)
    color(mat,values['color'],unreal.MaterialProperty.MP_BASE_COLOR,0)
    scalar(mat,values['roughness'],unreal.MaterialProperty.MP_ROUGHNESS,130)
    scalar(mat,values['metallic'],unreal.MaterialProperty.MP_METALLIC,230)
    if values.get('transmission',0)>.5:
        mat.set_editor_property('blend_mode',unreal.BlendMode.BLEND_TRANSLUCENT)
        mat.set_editor_property('translucency_lighting_mode',unreal.TranslucencyLightingMode.TLM_SURFACE_PER_PIXEL_LIGHTING)
        scalar(mat,values.get('opacity',.12),unreal.MaterialProperty.MP_OPACITY,330)
        # Flat architectural panes: no screen-space refraction distortion.
        scalar(mat,1,unreal.MaterialProperty.MP_REFRACTION,430)
    if values.get('emission_strength',0)>0:
        ec=values.get('emission_color',values['color']);strength=values['emission_strength']
        color(mat,[ec[i]*strength for i in range(3)]+[1],unreal.MaterialProperty.MP_EMISSIVE_COLOR,530)
    lib.recompile_material(mat);assert unreal.EditorAssetLibrary.save_loaded_asset(mat,only_if_is_dirty=False)
    return mat

main=unreal.load_asset(cfg['unreal_asset']);assert isinstance(main,unreal.StaticMesh)
before_maps=maps();before_instances=instances(main)
old_materials={key(s.material_slot_name):s.material_interface for s in main.static_materials}
targets=[cfg['unreal_asset']]+[p['unreal_asset'] for p in cfg.get('parts',[])]
# Check every file and material before mutating the first mesh.
for target in targets:
    name=target.rsplit('/',1)[1]
    assert target==cfg['unreal_asset'] or target.rsplit('/',1)[0]==cfg['unreal_parts']
    assert name in expected and (source/(name+'.fbx')).is_file(),name
    existing=unreal.load_asset(target)
    assigned={key(s.material_slot_name):s.material_interface for s in existing.static_materials} if existing else old_materials
    for slot in expected[name]['materials']:
        assert assigned.get(key(slot)) or unreal.load_asset(cfg['unreal_materials']+'/'+key(slot)) or any(key(n)==key(slot) for n in manifest),'Missing material: '+slot
rows=[]
# Force FbxFactory so FbxImportUI options cannot silently be ignored by Interchange.
# The previous CVar value is restored even when an import fails.
cvar='Interchange.FeatureFlags.Import.FBX'
previous=unreal.SystemLibrary.get_console_variable_int_value(cvar)
try:
    unreal.SystemLibrary.execute_console_command(None,cvar+' 0')
    for target in targets:
        name=target.rsplit('/',1)[1];directory=target.rsplit('/',1)[0]
        assert target==cfg['unreal_asset'] or directory==cfg['unreal_parts']
        assert name in expected
        existing=unreal.load_asset(target)
        previous_materials={key(s.material_slot_name):s.material_interface for s in existing.static_materials} if existing else old_materials
        previous_settings=existing.get_editor_property('nanite_settings') if existing else None
        previous_slots=[str(s.material_slot_name) for s in existing.static_materials] if existing else []
        options=unreal.FbxImportUI();options.automated_import_should_detect_type=False
        options.import_mesh=True;options.import_as_skeletal=False
        options.mesh_type_to_import=unreal.FBXImportType.FBXIT_STATIC_MESH
        options.original_import_type=unreal.FBXImportType.FBXIT_STATIC_MESH
        options.import_materials=False;options.import_textures=False;options.import_animations=False
        imp=options.static_mesh_import_data;imp.combine_meshes=True;imp.import_uniform_scale=1
        imp.normal_import_method=unreal.FBXNormalImportMethod.FBXNIM_IMPORT_NORMALS
        imp.auto_generate_collision=False;imp.generate_lightmap_u_vs=False
        unreal.EditorAssetLibrary.make_directory(directory)
        task=unreal.AssetImportTask();task.filename=str(source/(name+'.fbx'));task.destination_path=directory;task.destination_name=name
        task.automated=True;task.async_=False;task.replace_existing=bool(existing);task.replace_existing_settings=False;task.save=False
        task.options=options;task.factory=unreal.FbxFactory()
        assets.import_asset_tasks([task])
        assert task.imported_object_paths,'Import produced no assets: '+target
        assert all(p==target or p==target+'.'+name for p in task.imported_object_paths),list(task.imported_object_paths)
        mesh=unreal.load_asset(target);assert isinstance(mesh,unreal.StaticMesh),target
        assert mesh.get_path_name()==target+'.'+name
        wanted={key(n) for n in expected[name]['materials']}
        assigned=[];slots=list(mesh.static_materials)
        for i,s in enumerate(slots):
            slot=str(s.material_slot_name)
            mat=material(slot,previous_materials);s.material_interface=mat
            assigned.append({'slot':slot,'material':mat.get_path_name()})
        mesh.set_editor_property('static_materials',slots)
        assert wanted.issubset({key(s.material_slot_name) for s in mesh.static_materials}),(name,wanted)
        assert [str(s.material_slot_name) for s in mesh.static_materials][:len(previous_slots)]==previous_slots,'Existing material slot order changed: '+target
        if previous_settings is not None:mesh.set_editor_property('nanite_settings',previous_settings)
        if target==cfg['unreal_asset'] and cfg.get('use_complex_collision'):
            configure_complex_collision(mesh)
        elif target!=cfg['unreal_asset'] and sub.get_simple_collision_count(mesh)==0:
            sub.add_simple_collisions(mesh,unreal.ScriptCollisionShapeType.BOX)
        b=mesh.get_bounding_box();bounds=[[b.min.x,b.min.y,b.min.z],[b.max.x,b.max.y,b.max.z]]
        # FBX handedness conversion: Blender X is retained and Y is mirrored.
        lo=expected[name]['min_m'];hi=expected[name]['max_m']
        expected_bounds=[[lo[0]*100,-hi[1]*100,lo[2]*100],[hi[0]*100,-lo[1]*100,hi[2]*100]]
        assert all(abs(a-b)<.11 for row,ex in zip(bounds,expected_bounds) for a,b in zip(row,ex)),(name,bounds,expected_bounds)
        assert maps()==before_maps
        assert instances(main)==before_instances
        assert unreal.EditorAssetLibrary.save_loaded_asset(mesh,only_if_is_dirty=False)
        rows.append({'asset':mesh.get_path_name(),'triangles':mesh.get_num_triangles(0),'source_triangles':expected[name]['triangles'],'bounds_cm':bounds,'materials':assigned,'collision':str(sub.get_collision_complexity(mesh)),'simple_collisions':sub.get_simple_collision_count(mesh),'source_files':list(mesh.get_editor_property('asset_import_data').extract_filenames())})
    assert maps()==before_maps and instances(main)==before_instances
    report={'status':'SUCCESS','assets':rows,'maps_saved':False,'instances_unchanged':True,'dirty_maps':before_maps}
    (log/(model+'_import.json')).write_text(json.dumps(report,indent=2),encoding='utf-8')
    error_log=log/(model+'_import_error.txt')
    if error_log.exists():error_log.unlink()
    unreal.log(model.upper()+'_IMPORT_OK')
except Exception:
    (log/(model+'_import_error.txt')).write_text(traceback.format_exc(),encoding='utf-8');raise
finally:
    unreal.SystemLibrary.execute_console_command(None,cvar+' '+str(previous))
