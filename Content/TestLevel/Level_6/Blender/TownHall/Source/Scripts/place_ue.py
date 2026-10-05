"""Place the exported Town Hall in the existing administration actor."""
import unreal, json, traceback
from pathlib import Path
disk=Path('D:/UEProject/ArcheoDig/Content/TestLevel/Level_6/Blender/TownHall')
def v(p): return [p.x,p.y,p.z]
def state(a):
    t=a.get_actor_transform()
    s={'transform':v(t.translation)+[t.rotation.x,t.rotation.y,t.rotation.z,t.rotation.w]+v(t.scale3d),'label':a.get_actor_label()}
    if isinstance(a,unreal.StaticMeshActor):
        c=a.static_mesh_component
        s['mesh']=c.static_mesh.get_path_name() if c.static_mesh else None
        s['materials']=[m.get_path_name() if m else None for m in c.get_materials()]
    return s
try:
    world=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    assert world.get_name()=='level_6_create_map'
    sub=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    actors=sub.get_all_level_actors()
    a=next(a for a in actors if a.get_actor_label()=='BO_Administration')
    plot=next(a for a in actors if a.get_actor_label()=='BO_Plot_Administration')
    mesh=unreal.load_asset('/Game/TestLevel/Level_6/Blender/TownHall/SM_TownHall_Blockout')
    assert mesh
    before={o.get_path_name():state(o) for o in actors if o!=a}
    old=state(a)
    oldc,olde=a.get_actor_bounds(False)
    pc,pe=plot.get_actor_bounds(False)
    b=mesh.get_bounding_box()
    # FBX converts Blender front -Y to UE +Y. Yaw +90 points west, to the entry marker.
    rot=unreal.Rotator(pitch=0,yaw=90,roll=0)
    local_center=(b.min+b.max)*.5
    lc=unreal.Vector(-local_center.y,local_center.x,local_center.z)
    location=unreal.Vector(oldc.x-lc.x,oldc.y-lc.y,pc.z+pe.z-b.min.z)
    with unreal.ScopedEditorTransaction('Place existing Town Hall on administration plot'):
        a.modify()
        a.static_mesh_component.set_static_mesh(mesh)
        a.static_mesh_component.set_editor_property('override_materials',[])
        a.set_actor_scale3d(unreal.Vector(1,1,1))
        a.set_actor_rotation(rot,False)
        a.set_actor_location(location,False,False)
    c,e=a.get_actor_bounds(False)
    assert abs(c.z-e.z-(pc.z+pe.z))<.01
    assert c.x-e.x>=pc.x-pe.x-.01 and c.x+e.x<=pc.x+pe.x+.01
    assert c.y-e.y>=pc.y-pe.y-.01 and c.y+e.y<=pc.y+pe.y+.01
    assert all(state(o)==before[o.get_path_name()] for o in actors if o!=a)
    overlaps=[]
    for o in actors:
        if o==a or o.get_actor_label()=='SM_SkySphere':continue
        oc,oe=o.get_actor_bounds(False)
        depth=[min(v(c+e)[i],v(oc+oe)[i])-max(v(c-e)[i],v(oc-oe)[i]) for i in range(3)]
        if all(x>.1 for x in depth):overlaps.append({'label':o.get_actor_label(),'depth_cm':depth})
    assert all(o['label']=='BO_Entry_Administration' for o in overlaps),overlaps
    assert unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
    sub.set_selected_level_actors([])
    report={'actor':a.get_path_name(),'old_state':old,'old_center':v(oldc),'location':v(location),'yaw':90,'scale':v(a.get_actor_scale3d()),'local_dimensions_cm':v(b.max-b.min),'world_dimensions_cm':v(e*2),'bounds_min':v(c-e),'bounds_max':v(c+e),'plot_bounds_min':v(pc-pe),'plot_bounds_max':v(pc+pe),'ground_z':c.z-e.z,'neighbors_unchanged':True,'aabb_overlaps':overlaps,'front_world':'-X'}
    (disk/'Source/placement_report.txt').write_text(json.dumps(report,indent=2))
except Exception:
    (disk/'Source/placement_error.txt').write_text(traceback.format_exc())
    raise
