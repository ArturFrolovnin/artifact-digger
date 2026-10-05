"""Run in Unreal Editor Python after exporting the current FBX."""
import unreal
import json
from pathlib import Path

base = '/Game/TestLevel/Level_6/Blender'
disk = Path(unreal.Paths.project_content_dir()).resolve() / 'TestLevel/Level_6/Blender'
mesh = unreal.load_asset(base + '/RudyPawnshop/SM_RudyPawnshop')
materials = {str(s.material_slot_name): s.material_interface for s in mesh.static_materials}
options = unreal.FbxImportUI()
options.automated_import_should_detect_type = False
options.import_mesh = True
options.import_as_skeletal = False
options.mesh_type_to_import = unreal.FBXImportType.FBXIT_STATIC_MESH
options.original_import_type = unreal.FBXImportType.FBXIT_STATIC_MESH
options.import_materials = False
options.import_textures = False
options.import_animations = False
options.static_mesh_import_data.combine_meshes = True
task = unreal.AssetImportTask()
task.filename = str(disk / 'RudyPawnshop/Source/SM_RudyPawnshop.fbx')
task.destination_path = base + '/RudyPawnshop'
task.destination_name = 'SM_RudyPawnshop'
task.automated = True
task.replace_existing = True
task.save = False
task.options = options
task.factory = unreal.FbxFactory()
unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
assert task.imported_object_paths, 'No imported mesh'
mesh = unreal.load_asset(base + '/RudyPawnshop/SM_RudyPawnshop')
for i, slot in enumerate(mesh.static_materials):
    name = str(slot.material_slot_name)
    material = materials.get(name) or unreal.load_asset(base + '/RudyPawnshop/Materials/' + name)
    assert material, name
    mesh.set_material(i, material)
dorm = unreal.load_asset(base + '/Dormitory/SM_Dormitory_Blockout')
dorm.get_editor_property('asset_import_data').scripted_add_filename(str(disk / 'Dormitory/Source/SM_Dormitory_Blockout.fbx'), 0, '')
unreal.EditorAssetLibrary.save_loaded_asset(dorm, only_if_is_dirty=False)
unreal.EditorAssetLibrary.save_loaded_asset(mesh, only_if_is_dirty=False)
unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
report = {'mesh': mesh.get_path_name(), 'materials': len(mesh.static_materials), 'triangles': mesh.get_num_triangles(0), 'source': task.filename}
(disk / 'RudyPawnshop/Source/ue_import_report.txt').write_text(json.dumps(report, indent=2), encoding='utf-8')
unreal.log('RUDY_IMPORT_COMPLETE ' + json.dumps(report))
