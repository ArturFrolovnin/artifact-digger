import unreal,json
from pathlib import Path
base='/Game/TestLevel/Level_6/Blender/Museum'
mesh=unreal.load_asset(base+'/SM_Museum_Blockout')
actor=next(a for a in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors() if a.get_actor_label()=='BO_Museum')
assert actor.static_mesh_component.static_mesh==mesh
materials=[s.material_interface.get_path_name() for s in mesh.static_materials]
assert len(materials)==13 and all(p.startswith(base+'/Materials/MUS_') for p in materials)
assert actor.get_actor_scale3d()==unreal.Vector(1,1,1)
assert abs(actor.get_actor_rotation().yaw-90)<.01
unreal.EditorAssetLibrary.save_loaded_asset(mesh)
assert unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
Path('D:/UEProject/ArcheoDig/Content/TestLevel/Level_6/Blender/Museum/Source/final_validation.txt').write_text(json.dumps({'mesh':mesh.get_path_name(),'materials':materials,'triangles':mesh.get_num_triangles(0),'level_saved':True,'actor':actor.get_path_name()},indent=2))
