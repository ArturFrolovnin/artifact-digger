import bpy, math, json
from mathutils import Vector
from pathlib import Path
coll=bpy.data.collections['BLD_Dormitory']; root=bpy.data.objects['Dormitory_ROOT']
source=Path('D:/UEProject/ArcheoDig/Content/TestLevel/Level_6/Blender/Dormitory/Source/Scripts/build_dormitory.py').read_text(encoding='utf-8-sig')
exec(source[source.index('groups = {}'):source.index('facades = [')])
materials=[bpy.data.materials[n] for n in ['DORM_Pale_Stone','DORM_Blue_Glass','DORM_Painted_Frame']]
for side in (-1,1):
    x=side*13.07; z=11.45
    rod('Gable_Oculi',(x,0,z),(x+side*.035,0,z),.47,1,24)
    vv,ff,mm=meshgroup('Gable_Oculi')
    for i in range(24):
        a=i*math.tau/24; b=(i+1)*math.tau/24; n=len(vv)
        vv.extend([(x+side*.065,r*math.cos(t),z+r*math.sin(t)) for r,t in [(.46,a),(.46,b),(.61,b),(.61,a)]]); ff.append((n,n+1,n+2,n+3)); mm.append(0)
    box('Gable_Oculi',(x+side*.08,0,z),(.09,.91,.065),2)
    box('Gable_Oculi',(x+side*.08,0,z),(.09,.065,.91),2)
for name,(vv,ff,mm) in groups.items():
    mesh=bpy.data.meshes.new('DORM_35_'+name); mesh.from_pydata(vv,[],ff); mesh.update()
    for m in materials: mesh.materials.append(m)
    for p,i in zip(mesh.polygons,mm): p.material_index=i
    obj=bpy.data.objects.new('DORM_35_'+name,mesh); coll.objects.link(obj); obj.parent=root
meshes=[o for o in coll.objects if o.type=='MESH']
bpy.context.view_layer.update()
pts=[o.matrix_world@Vector(c) for o in meshes for c in o.bound_box]
report=json.loads(root['validation'])
report['mesh_objects']=len(meshes); report['triangles']=sum(len(p.vertices)-2 for o in meshes for p in o.data.polygons)
report['total_dimensions_m']=[max(p[i] for p in pts)-min(p[i] for p in pts) for i in range(3)]
report['all_parented_to_root']=all(o.parent==root for o in meshes)
root['validation']=json.dumps(report)
Path('D:/UEProject/ArcheoDig/Saved/BlenderDormitory/validation.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
for a in bpy.context.screen.areas:
    if a.type=='VIEW_3D':
        a.spaces.active.region_3d.view_rotation=Vector((-1.3,2,1.15)).to_track_quat('Z','Y')
        a.tag_redraw()
result=report
