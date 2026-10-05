"""Replace the existing dealership actor, preserving every other actor."""
import unreal, json
from pathlib import Path
disk=Path('D:/UEProject/ArcheoDig/Content/TestLevel/Level_6/Blender/CarDealership')
world=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
assert world.get_name()=='level_6_create_map'
sub=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
actors=sub.get_all_level_actors()
a=next(a for a in actors if a.get_actor_label()=='BO_CarDealer')
plot=next(a for a in actors if a.get_actor_label()=='BO_Plot_CarDealer')
mesh=unreal.load_asset('/Game/TestLevel/Level_6/Blender/CarDealership/SM_CarDealership_Blockout')
assert mesh
def v(p): return [p.x,p.y,p.z]
def state(a):
    t=a.get_actor_transform()
    s={'transform':v(t.translation)+[t.rotation.x,t.rotation.y,t.rotation.z,t.rotation.w]+v(t.scale3d),'label':a.get_actor_label()}
    if isinstance(a,unreal.StaticMeshActor):
        c=a.static_mesh_component
        s['mesh']=c.static_mesh.get_path_name() if c.static_mesh else None
        s['materials']=[m.get_path_name() if m else None for m in c.get_materials()]
    return s
before={o.get_path_name():state(o) for o in actors if o!=a}
old=state(a)
original=next(row for row in json.loads((disk/'Source/placement_before.txt').read_text())['actors'] if row['label']=='BO_CarDealer')
oldc=unreal.Vector(*original['center'])
pc,pe=plot.get_actor_bounds(False)
b=mesh.get_bounding_box();lc=(b.min+b.max)*.5
location=unreal.Vector(oldc.x-lc.x,oldc.y-lc.y,pc.z+pe.z-b.min.z)
entry=next(o for o in actors if o.get_actor_label()=='BO_Entry_CarDealer')
ec,ee=entry.get_actor_bounds(False)
# Keep the existing west-side entry marker clear of the wider coping bounds.
location.x=max(location.x,ec.x+ee.x-b.min.x)
# Blender front -Y becomes UE +Y: faces the main road at Y=-5200.
# Service doors face +X into the open space between dealership and hospital.
with unreal.ScopedEditorTransaction('Import finished car dealership into Level 6'):
    a.modify()
    a.static_mesh_component.set_static_mesh(mesh)
    a.static_mesh_component.set_editor_property('override_materials',[])
    a.set_actor_scale3d(unreal.Vector(1,1,1))
    a.set_actor_rotation(unreal.Rotator(pitch=0,yaw=0,roll=0),False)
    a.set_actor_location(location,False,False)
c,e=a.get_actor_bounds(False)
assert abs(c.z-e.z-(pc.z+pe.z))<.01
assert c.x-e.x>=pc.x-pe.x and c.x+e.x<=pc.x+pe.x
assert c.y-e.y>=pc.y-pe.y and c.y+e.y<=pc.y+pe.y
assert all(state(o)==before[o.get_path_name()] for o in actors if o!=a)
overlaps=[]
for o in actors:
    if o==a or o.get_actor_label()=='SM_SkySphere':continue
    oc,oe=o.get_actor_bounds(False)
    if all(min(v(c+e)[i],v(oc+oe)[i])-max(v(c-e)[i],v(oc-oe)[i])>.1 for i in range(3)):
        overlaps.append(o.get_actor_label())
assert not overlaps,overlaps
assert unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
sub.set_selected_level_actors([])
report={'actor':a.get_path_name(),'old_state':old,'old_center':v(oldc),'location':v(location),'yaw':0,'scale':v(a.get_actor_scale3d()),'dimensions_cm':v(e*2),'bounds_min':v(c-e),'bounds_max':v(c+e),'plot_bounds_min':v(pc-pe),'plot_bounds_max':v(pc+pe),'ground_z':c.z-e.z,'neighbors_unchanged':True,'overlap_actors':overlaps,'front_world':'+Y','service_world':'+X'}
(disk/'Source/placement_report.txt').write_text(json.dumps(report,indent=2))
print(json.dumps(report))
