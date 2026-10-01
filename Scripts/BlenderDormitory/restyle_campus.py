"""Restyle the existing dormitory in place. No copy, save, merge or export."""
import bpy, bmesh, math, json, random
from pathlib import Path
from mathutils import Vector
coll=bpy.data.collections.get('DORMITORY_Blockout')
assert coll and not bpy.data.collections.get('BLD_Dormitory'), 'Expected original building once'
root=bpy.data.objects['DORMITORY_ROOT__ground_pivot']
assert root.location.length<1e-6
preserved={o.name:o.as_pointer() for o in coll.objects if o.name.startswith(('DORM_02_','DORM_03_'))}
coll.name='BLD_Dormitory'
root.name='Dormitory_ROOT'
# Remove only replaced dormitory assemblies, with no archive or backup.
remove_prefixes=('DORM_04_','DORM_05_Stair_Bay','DORM_06_','DORM_07_','DORM_08_','DORM_09_','DORM_10_','DORM_11_','DORM_13_','DORM_17_','DORM_18_')
for o in list(coll.objects):
    if o.name.startswith(remove_prefixes):
        mesh=o.data
        bpy.data.objects.remove(o,do_unlink=True)
        if mesh.users==0: bpy.data.meshes.remove(mesh)
# Reuse the geometry utilities, not the old scene-building code.
source=Path('D:/UEProject/ArcheoDig/Scripts/BlenderDormitory/build_dormitory.py').read_text(encoding='utf-8-sig')
exec(source[source.index('groups = {}'):source.index('facades = [')])
materials=[]
def mat(name,color):
    m=bpy.data.materials.get('DORM_'+name) or bpy.data.materials.new('DORM_'+name)
    m.diffuse_color=(*color,1)
    m.use_nodes=True
    p=next(n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED')
    p.inputs['Base Color'].default_value=(*color,1)
    p.inputs['Metallic'].default_value=0
    p.inputs['Roughness'].default_value=.77
    materials.append(m)
    return len(materials)-1
STONE=mat('Pale_Stone',(.83,.72,.52))
mat('Painted_Frame',(.78,.63,.39))
mat('Warm_Limestone',(.31,.22,.15))
mat('Terracotta',(.32,.22,.15))
mat('Basalt_Plinth',(.66,.57,.43))
mat('Blue_Glass',(.07,.25,.29))
mat('Blue_Glass_Light',(.10,.29,.32))
mat('Entry_Teal',(.24,.115,.047))
SLATE=mat('Campus_Slate',(.105,.135,.19))
SLATE2=mat('Campus_Slate_Light',(.15,.19,.255))
SLATE3=mat('Campus_Slate_Mid',(.125,.16,.22))
BRICKS=[mat('Campus_Brick_'+str(i),c) for i,c in enumerate([(.59,.255,.115),(.65,.30,.14),(.55,.215,.085),(.62,.27,.12),(.69,.325,.155)])]
MORTAR=mat('Campus_Mortar',(.33,.24,.17))
WOOD=mat('Campus_Oak',(.29,.135,.06))
METAL=mat('Graphite_Metal',(.10,.12,.125))
LEAF=mat('Porch_Plant',(.19,.30,.10))

def face(group,pts,material):
    vv,ff,mm=meshgroup(group)
    n=len(vv); vv.extend(pts); ff.append(tuple(range(n,n+len(pts)))); mm.append(material)

facades=[('Front',26,lambda u,v,z:(u,-9-v,z),lambda p:(p.x,-p.y-9,p.z)),('Right',18,lambda u,v,z:(13+v,u,z),lambda p:(p.y,p.x-13,p.z)),('Rear',26,lambda u,v,z:(-u,9+v,z),lambda p:(-p.x,p.y-9,p.z)),('Left',18,lambda u,v,z:(-13-v,-u,z),lambda p:(-p.y,-p.x-13,p.z))]
rng=random.Random(18)
# Geometry bricks: lightweight quads clipped to existing wall panels, keeping openings intact.
for name,length,mapper,inverse in facades:
    for o in [o for o in coll.objects if o.name.startswith('DORM_02_'+name)]:
        rects=[]
        for p in o.data.polygons:
            coords=[inverse(o.data.vertices[v].co) for v in p.vertices]
            if not all(abs(v[1])<1e-5 for v in coords): continue
            u0,u1=min(v[0] for v in coords),max(v[0] for v in coords)
            z0,z1=min(v[2] for v in coords),max(v[2] for v in coords)
            for row in range(math.floor(z0/.245),math.ceil(z1/.245)):
                bot,top=max(z0,row*.245+.013),min(z1,(row+1)*.245-.013)
                if top-bot<.015: continue
                offset=(row%2)*.31
                for col in range(math.floor((u0-offset)/.62),math.ceil((u1-offset)/.62)):
                    left,right=max(u0,col*.62+offset+.013),min(u1,(col+1)*.62+offset-.013)
                    if right-left<.02: continue
                    face('20_Brick_'+name,[mapper(left,.022,bot),mapper(right,.022,bot),mapper(right,.022,top),mapper(left,.022,top)],rng.choice(BRICKS))
    # Pale continuous floor strings and a stronger base course.
    for z in (.47,2.85,5.25,7.65,10.02):
        box('21_Stone_Strings',(0,.08,z),(length,.23,.13 if z>1 else .21),STONE,mapper)
    # Alternating corner quoins, deliberately simpler than the university.
    for u in (-length/2,length/2):
        for row in range(23):
            w=.66 if row%2==0 else .43
            center=u+(w/2 if u<0 else -w/2)
            box('22_Corner_Quoins',(center,.085,.72+row*.40),(w,.20,.34),STONE,mapper)
# Clean cream vertical borders of the central stair bay, no orange modern panel.
front=facades[0][2]
for u in (-1.26,1.26):
    box('23_Entry_Bay_Stone',(u,.07,5.22),(.17,.23,9.35),STONE,front)
# Stone plinth joints.
for name,length,mapper,inverse in facades:
    for u in range(-int(length/2)+1,int(length/2)):
        box('24_Plinth_Joints',(u,.005,.20),(.016,.025,.34),MORTAR,mapper)
# Retain cornice height and mass; replace the flat roof with a dark pitched roof.
eave=10.19; ridge=13.48; halfdepth=9.52; halfwidth=13.50
for sign in (-1,1):
    face('25_Pitched_Roof',[(-halfwidth,0,ridge),(halfwidth,0,ridge),(halfwidth,sign*halfdepth,eave),(-halfwidth,sign*halfdepth,eave)],SLATE)
    # Sparse staggered slate courses, no texture dependency.
    for row in range(16):
        ya=row*halfdepth/16+.015; yb=(row+1)*halfdepth/16-.018
        offset=(row%2)*.52
        for col in range(-14,14):
            xa=max(-halfwidth,col*1.04+offset+.015); xb=min(halfwidth,(col+1)*1.04+offset-.015)
            if xb<=xa: continue
            za=ridge-(ridge-eave)*ya/halfdepth+.014
            zb=ridge-(ridge-eave)*yb/halfdepth+.014
            face('26_Slate_Courses',[(xa,sign*ya,za),(xb,sign*ya,za),(xb,sign*yb,zb),(xa,sign*yb,zb)],rng.choices([SLATE,SLATE2,SLATE3],[5,1,3])[0])
# Gable infills; stone barge boards following slopes.
for side in (-1,1):
    x=side*13
    face('27_Gable_Brick',[(x,-9,10.05),(x,9,10.05),(x,0,13.30)],BRICKS[1])
    # Horizontal brick courses clipped to the triangular end wall.
    for row in range(13):
        z0=10.07+row*.245; z1=min(13.30,z0+.22)
        span0=9*(13.30-z0)/3.25; span1=9*(13.30-z1)/3.25
        for col in range(-15,15):
            a=col*.62+(row%2)*.31+.015; b=a+.59
            la,ra=max(a,-span0),min(b,span0); lb,rb=max(a,-span1),min(b,span1)
            if ra>la and rb>lb:
                face('27_Gable_Brick',[(x+side*.025,la,z0),(x+side*.025,ra,z0),(x+side*.025,rb,z1),(x+side*.025,lb,z1)],rng.choice(BRICKS))
    for sign in (-1,1):
        rod('28_Stone_Bargeboards',(side*13.49,0,13.48),(side*13.49,sign*9.54,10.18),.12,STONE,4)
for y in (-9.40,9.40):
    box('28_Stone_Bargeboards',(0,y,10.13),(27.1,.24,.22),STONE)
rod('29_Ridge_Cap',(-13.5,0,13.52),(13.5,0,13.52),.085,SLATE3,6)
# Only two small traditional brick chimneys instead of technical roof equipment.
for x in (-7.6,7.6):
    box('30_Brick_Chimneys',(x,1.8,13.25),(.80,.85,1.80),BRICKS[1])
    box('30_Brick_Chimneys',(x,1.8,14.14),(1.02,1.07,.17),STONE)
    box('30_Brick_Chimneys',(x,1.8,14.235),(.66,.71,.025),METAL)
    for z in (12.75,13.03,13.31,13.59,13.87):
        box('30_Brick_Chimneys',(x,1.8,z),(.81,.86,.025),MORTAR)
# Smaller welcoming porch: timber posts, cream feet, a modest pitched pediment.
for x in (-2.43,2.43):
    box('31_Porch_Posts',(x,-10.65,1.69),(.22,.22,2.48),WOOD)
    box('31_Porch_Posts',(x,-10.65,.63),(.37,.37,.36),STONE)
    box('31_Porch_Posts',(x,-10.65,2.87),(.40,.40,.18),STONE)
box('31_Porch_Posts',(0,-10.62,2.98),(5.65,.25,.20),STONE)
for s in (-1,1):
    face('32_Porch_Roof',[(0,-8.92,3.82),(0,-11.1,3.82),(s*2.98,-11.1,3.04),(s*2.98,-8.92,3.04)],SLATE)
    rod('33_Porch_Trim',(0,-11.11,3.82),(s*2.98,-11.11,3.04),.095,STONE,4)
face('33_Porch_Trim',[(-2.9,-11.04,3.05),(2.9,-11.04,3.05),(0,-11.04,3.78)],BRICKS[1])
box('33_Porch_Trim',(0,-11.10,3.03),(6.02,.16,.14),STONE)
# Small planters frame the entrance without creating separate landscaping assets.
for x in (-3.45,3.45):
    box('34_Porch_Planters',(x,-9.9,.33),(.62,.62,.66),STONE)
    box('34_Porch_Planters',(x,-9.9,.66),(.67,.67,.12),STONE)
    box('34_Porch_Planters',(x,-9.9,.74),(.48,.48,.09),MORTAR)
    for z,rad in [(1.01,.31),(1.30,.24),(1.52,.16)]:
        rod('34_Porch_Planters',(x,-9.9,z-.17),(x,-9.9,z+.17),rad,LEAF,7)
# Create new replacement assemblies as separate meshes, parented to the original renamed root.
for name,(vertices,faces,indices) in groups.items():
    mesh=bpy.data.meshes.new('DORM_'+name)
    mesh.from_pydata(vertices,[],faces)
    mesh.update()
    for m in materials: mesh.materials.append(m)
    for p,i in zip(mesh.polygons,indices): p.material_index=i
    obj=bpy.data.objects.new('DORM_'+name,mesh)
    coll.objects.link(obj); obj.parent=root
    obj['assembly']=name
for obj in coll.objects:
    if obj==root: continue
    obj.parent=root
    if obj.type=='MESH':
        bm=bmesh.new(); bm.from_mesh(obj.data)
        bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
        bm.to_mesh(obj.data); bm.free(); obj.data.update()
# Roof top normals explicitly upward on open roof surfaces.
for obj in coll.objects:
    if obj.type=='MESH' and obj.name.startswith(('DORM_25_','DORM_26_','DORM_32_')):
        bm=bmesh.new(); bm.from_mesh(obj.data)
        for f in bm.faces:
            if f.normal.z<0: f.normal_flip()
        bm.to_mesh(obj.data); bm.free()
root.location=(0,0,0)
root['style']='Warm brick campus; limestone trim; dark slate pitched roof; exterior only'
root['body_dimensions_m']=[26,18,10.05]
root['source']='User campus screenshot; Level6_University_Detail.md. Requested StyleGuide.md and Dormitory.md absent.'
root['export_note']='Separate editable assemblies, common ground-centre pivot. Not merged or exported.'
for o in bpy.context.selected_objects: o.select_set(False)
root.select_set(True); bpy.context.view_layer.objects.active=root
bpy.context.view_layer.update()
for a in bpy.context.screen.areas:
    if a.type=='VIEW_3D':
        s=a.spaces.active; s.shading.color_type='MATERIAL'; s.show_gizmo=False
        s.region_3d.view_rotation=Vector((1.3,-2,1.15)).to_track_quat('Z','Y')
        s.region_3d.view_location=(0,-.3,6.7); s.region_3d.view_distance=44
        a.tag_redraw()
meshes=[o for o in coll.objects if o.type=='MESH']
pts=[o.matrix_world@Vector(v) for o in meshes for v in o.bound_box]
lo=[min(v[i] for v in pts) for i in range(3)]; hi=[max(v[i] for v in pts) for i in range(3)]
result={'collection':coll.name,'root':root.name,'root_location':list(root.location),'preserved_existing_walls_and_windows':all(bpy.data.objects[n].as_pointer()==ptr for n,ptr in preserved.items()),'body_footprint_m':[26,18],'total_dimensions_m':[hi[i]-lo[i] for i in range(3)],'mesh_objects':len(meshes),'triangles':sum(len(p.vertices)-2 for o in meshes for p in o.data.polygons),'all_parented_to_root':all(o.parent==root for o in meshes),'degenerate_faces':sum(p.area<1e-10 for o in meshes for p in o.data.polygons),'saved':False,'exported':False}
root['validation']=json.dumps(result)
Path('D:/UEProject/ArcheoDig/Saved/BlenderDormitory/validation.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
