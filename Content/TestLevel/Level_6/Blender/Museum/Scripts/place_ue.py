"""Run only after successful mesh/material import and inspection of import report."""
import unreal,json
from pathlib import Path
disk=Path('D:/UEProject/ArcheoDig/Content/TestLevel/Level_6/Blender/Museum')
base='/Game/TestLevel/Level_6/Blender/Museum'
world=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
assert world.get_name()=='level_6_create_map'
sub=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
actors=sub.get_all_level_actors()
museum=next(a for a in actors if a.get_actor_label()=='BO_Museum')
plot=next(a for a in actors if a.get_actor_label()=='BO_Plot_Museum')
mesh=unreal.load_asset(base+'/SM_Museum_Blockout');assert mesh
b=mesh.get_bounding_box()
assert abs((b.max.x-b.min.x)-3107.596)<2 and abs((b.max.z-b.min.z)-1248)<2
assert abs(b.min.z)<.01
def transform_values(a):
    t=a.get_actor_transform(); return [t.translation.x,t.translation.y,t.translation.z,t.rotation.x,t.rotation.y,t.rotation.z,t.rotation.w,t.scale3d.x,t.scale3d.y,t.scale3d.z]
before={a.get_name():transform_values(a) for a in actors if a!=museum}
pc,pe=plot.get_actor_bounds(False)
with unreal.ScopedEditorTransaction('Replace museum blockout with Blender museum'):
    comp=museum.static_mesh_component
    comp.set_static_mesh(mesh)
    comp.set_editor_property('override_materials',[])
    museum.set_actor_scale3d(unreal.Vector(1,1,1))
    museum.set_actor_rotation(unreal.Rotator(pitch=0,yaw=90,roll=0),False)
    museum.set_actor_location(unreal.Vector(pc.x,pc.y,pc.z+pe.z),False,False)
assert all(transform_values(a)==before[a.get_name()] for a in actors if a!=museum)
c,e=museum.get_actor_bounds(False)
report={'actor':museum.get_path_name(),'location':[pc.x,pc.y,pc.z+pe.z],'yaw':90,'scale':[1,1,1],'ground_min_z':c.z-e.z,'bounds_min':[c.x-e.x,c.y-e.y,c.z-e.z],'bounds_max':[c.x+e.x,c.y+e.y,c.z+e.z],'neighbor_transforms_unchanged':True}
assert abs(report['ground_min_z']-24)<.1
unreal.EditorAssetLibrary.save_loaded_asset(mesh)
assert unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
(disk/'Source/placement_report.txt').write_text(json.dumps(report,indent=2))


