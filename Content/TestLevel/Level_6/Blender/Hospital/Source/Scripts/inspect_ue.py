import unreal, json
from pathlib import Path
sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
actors = sub.get_all_level_actors()
hospital = next(a for a in actors if a.get_actor_label() == 'BO_Hospital')
def v(p): return [p.x, p.y, p.z]
c, e = hospital.get_actor_bounds(False)
rows = []
for a in actors:
    ac, ae = a.get_actor_bounds(False)
    if 'Hospital' in a.get_actor_label() or (abs(ac.x-c.x)<6500 and abs(ac.y-c.y)<6500):
        rows.append(dict(label=a.get_actor_label(), path=a.get_path_name(), location=v(a.get_actor_location()), rotation=str(a.get_actor_rotation()), scale=v(a.get_actor_scale3d()), center=v(ac), extent=v(ae)))
report = {'world':unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world().get_path_name(),'actors':rows}
Path('D:/UEProject/ArcheoDig/Content/TestLevel/Level_6/Blender/Hospital/Source/placement_before.txt').write_text(json.dumps(report,indent=2))
print(json.dumps(report))
