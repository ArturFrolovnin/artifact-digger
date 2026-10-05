"""Replace only the hospital and retire its two obsolete rooftop cross markers."""
import unreal,json,math
from pathlib import Path
disk=Path('D:/UEProject/ArcheoDig/Content/TestLevel/Level_6/Blender/Hospital')
base='/Game/TestLevel/Level_6/Blender/Hospital'
world=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
assert world.get_name()=='level_6_create_map'
sub=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
actors=sub.get_all_level_actors()
hospital=next(a for a in actors if a.get_actor_label()=='BO_Hospital')
plot=next(a for a in actors if a.get_actor_label()=='BO_Plot_Hospital')
mesh=unreal.load_asset(base+'/SM_Hospital_Blockout');assert mesh
validated=json.loads((disk/'Source/ue_import_report.txt').read_text())
b=mesh.get_bounding_box()
assert abs(b.min.z)<.01
def v(p):return [p.x,p.y,p.z]
def state(a):
    t=a.get_actor_transform()
    return v(t.translation)+[t.rotation.x,t.rotation.y,t.rotation.z,t.rotation.w]+v(t.scale3d)
before={a.get_name():state(a) for a in actors if a!=hospital}
original=next(row for row in json.loads((disk/'Source/placement_before.txt').read_text())['actors'] if row['label']=='BO_Hospital')
old_center=unreal.Vector(*original['center'])
pc,pe=plot.get_actor_bounds(False)
# Yaw -90 maps imported +Y (Blender entry -Y) to the actual street at +X.
# Center full footprint on the old block so every foot stays on the plot.
local_center=(b.min+b.max)*.5
location=unreal.Vector(old_center.x-local_center.y,old_center.y+local_center.x,pc.z+pe.z)
with unreal.ScopedEditorTransaction('Replace hospital blockout with finished Blender hospital'):
    hospital.modify()
    comp=hospital.static_mesh_component
    comp.set_static_mesh(mesh);comp.set_editor_property('override_materials',[])
    hospital.set_actor_scale3d(unreal.Vector(1,1,1))
    hospital.set_actor_rotation(unreal.Rotator(pitch=0,yaw=-90,roll=0),False)
    hospital.set_actor_location(location,False,False)
    retired=[]
    for a in actors:
        if a.get_actor_label() in {'BO_Hospital_CrossH','BO_Hospital_CrossV'}:
            a.modify()
            a.static_mesh_component.set_visibility(False)
            a.set_actor_hidden_in_game(True)
            a.set_actor_enable_collision(False)
            retired.append(a.get_actor_label())
assert all(state(a)==before[a.get_name()] for a in actors if a!=hospital)
c,e=hospital.get_actor_bounds(False)
assert abs((c.z-e.z)-(pc.z+pe.z))<.1
assert c.x-e.x>=pc.x-pe.x-.1 and c.x+e.x<=pc.x+pe.x+.1
assert c.y-e.y>=pc.y-pe.y-.1 and c.y+e.y<=pc.y+pe.y+.1
report={'actor':hospital.get_path_name(),'location':v(location),'yaw':-90,'scale':[1,1,1],
        'old_block_center':v(old_center),'world_dimensions_cm':v(e*2),'ground_min_z':c.z-e.z,
        'bounds_min':v(c-e),'bounds_max':v(c+e),'fully_inside_plot':True,
        'neighbor_transforms_unchanged':True,'retired_hospital_markers':retired}
assert unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
(disk/'Source/placement_report.txt').write_text(json.dumps(report,indent=2))
sub.set_selected_level_actors([])
print(json.dumps(report))
