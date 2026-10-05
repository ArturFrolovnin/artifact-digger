import unreal,json
from pathlib import Path
actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()
def v(x):return [x.x,x.y,x.z]
data=[]
for a in actors:
    c,e=a.get_actor_bounds(False)
    if 'Museum' in a.get_actor_label() or (abs(c.x-2300)<4000 and abs(c.y-600)<4000):
        data.append(dict(name=a.get_name(),label=a.get_actor_label(),location=v(a.get_actor_location()),rotation=str(a.get_actor_rotation()),scale=v(a.get_actor_scale3d()),center=v(c),extent=v(e)))
Path('D:/UEProject/ArcheoDig/Content/TestLevel/Level_6/Blender/Museum/Source/placement_before.txt').write_text(json.dumps(data,indent=2))

