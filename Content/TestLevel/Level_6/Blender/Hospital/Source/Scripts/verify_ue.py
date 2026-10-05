import unreal,json
from pathlib import Path
disk=Path('D:/UEProject/ArcheoDig/Content/TestLevel/Level_6/Blender/Hospital')
actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()
a=next(a for a in actors if a.get_actor_label()=='BO_Hospital')
c,e=a.get_actor_bounds(False)
nearby=[]; overlaps=[]
for n in actors:
    if n==a:continue
    nc,ne=n.get_actor_bounds(False)
    dx=max(0,abs(nc.x-c.x)-ne.x-e.x)
    dy=max(0,abs(nc.y-c.y)-ne.y-e.y)
    if dx<1500 and dy<1500:
        row={'label':n.get_actor_label(),'center':[nc.x,nc.y,nc.z],'extent':[ne.x,ne.y,ne.z],'xy_gap_cm':[dx,dy]}
        nearby.append(row)
        if dx==0 and dy==0 and nc.z+ne.z>c.z-e.z+.1 and nc.z-ne.z<c.z+e.z:
            overlaps.append(row)
mesh=a.static_mesh_component.static_mesh
report={'nearby':nearby,'aabb_overlap_candidates':overlaps,
        'mesh':mesh.get_path_name(),'material_paths':[s.material_interface.get_path_name() for s in mesh.static_materials],
        'scale':str(a.get_actor_scale3d()),'rotation':str(a.get_actor_rotation()),
        'import_settings':str(mesh.get_editor_property('asset_import_data'))}
assert all('/Hospital/Materials/HOSP_' in p for p in report['material_paths'])
(disk/'Source/ue_validation.txt').write_text(json.dumps(report,indent=2))
