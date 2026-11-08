"""Add the reference-inspired interior to the existing Dormitory, once.

Does not rebuild or modify any existing exterior object. No UE/level operations.
Coordinates are metres: entry faces +Y, reception +X, stairs -X.
"""
import bpy, math, json, hashlib, random
from pathlib import Path
from mathutils import Vector, Matrix

BASE=Path('D:/UEProject/ArcheoDig')
SOURCE=BASE/'SourceAssets/Blender/Buildings/Dormitory/Source'
LOG=BASE/'Saved/BlenderToUE'
assert Path(bpy.data.filepath)==SOURCE/'Dormitory_Blockout.blend'
assert bpy.context.mode=='OBJECT'
assert not any(o.name.startswith('DORM_INT_') for o in bpy.data.objects), 'Interior already exists'
root=bpy.data.objects['Dormitory_ROOT']
building=bpy.data.collections['BLD_Dormitory']
interior=bpy.data.collections.new('Dormitory_Interior');building.children.link(interior)
architecture=bpy.data.collections.new('Dormitory_Interior_Architecture');interior.children.link(architecture)
furniture=bpy.data.collections.new('Dormitory_Interior_Furnishings');interior.children.link(furniture)
doors_coll=bpy.data.collections.new('Dormitory_Interior_Doors');interior.children.link(doors_coll)
lights_coll=bpy.data.collections.new('Dormitory_Interior_Lighting');interior.children.link(lights_coll)
assetbase='/Game/Art/Models/Buildings/Dormitory/Parts/'
rng=random.Random(731)

def fingerprint(o):
    value={'vertices':[list(v.co) for v in o.data.vertices], 'faces':[(list(p.vertices),p.material_index,p.use_smooth) for p in o.data.polygons], 'materials':[m.name if m else None for m in o.data.materials], 'matrix':[list(r) for r in o.matrix_world]}
    return hashlib.sha256(json.dumps(value,sort_keys=True).encode()).hexdigest()
originals={o.name:fingerprint(o) for o in building.all_objects if o.type=='MESH'}
manifest={}
def material(name,color,rough=.6,metal=0,emission=0):
    name='DORM_INT_'+name
    assert name not in bpy.data.materials
    m=bpy.data.materials.new(name);m.diffuse_color=(*color,1);m.use_nodes=True
    bsdf=next((n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED'),None)
    if bsdf is None:
        bsdf=m.node_tree.nodes.new('ShaderNodeBsdfPrincipled')
        output=next((n for n in m.node_tree.nodes if n.type=='OUTPUT_MATERIAL'),None) or m.node_tree.nodes.new('ShaderNodeOutputMaterial')
        m.node_tree.links.new(bsdf.outputs['BSDF'],output.inputs['Surface'])
    bsdf.inputs['Base Color'].default_value=(*color,1)
    bsdf.inputs['Roughness'].default_value=rough;bsdf.inputs['Metallic'].default_value=metal
    if emission:
        bsdf.inputs['Emission Color'].default_value=(*color,1)
        bsdf.inputs['Emission Strength'].default_value=emission
    manifest[name]={'color':list(color),'roughness':rough,'metallic':metal,'emission_strength':emission}
    return m
plaster=material('Cream_Plaster',(.76,.665,.52),.88)
oak=material('Honey_Oak',(.37,.19,.075),.45)
walnut=material('Walnut_Trim',(.155,.067,.025),.43)
tile_a=material('Slate_Tile',(.235,.295,.315),.5)
tile_b=material('Stone_Tile',(.32,.345,.34),.55)
grout=material('Grout',(.12,.16,.17),.9)
fabric=material('Sage_Fabric',(.27,.36,.145),.94)
rug=material('Blue_Wool',(.09,.17,.205),.96)
brass=material('Brushed_Brass',(.62,.39,.13),.3,.72)
paper=material('Ivory_Paper',(.86,.77,.59),.85)
glow=material('Warm_Glass', (1,.64,.29),.35,0,3.0)
leaf_light=material('Leaf_Light',(.34,.46,.12),.75)
stone=bpy.data.materials['DORM_Pale_Stone']
green=bpy.data.materials['DORM_Porch_Plant']
dark=bpy.data.materials['DORM_Graphite_Metal']
soil=bpy.data.materials['DORM_Campus_Mortar']

class Mesh:
    def __init__(self):self.v=[];self.f=[];self.mi=[];self.mats=[]
    def add(self,verts,faces,mat):
        if mat not in self.mats:self.mats.append(mat)
        offset=len(self.v);self.v.extend([tuple(v) for v in verts])
        self.f.extend([tuple(offset+i for i in f) for f in faces]);self.mi.extend([self.mats.index(mat)]*len(faces))
    def box(self,c,s,mat,rot=0):
        cs=math.cos(rot);sn=math.sin(rot)
        vs=[]
        for x,y,z in [(-1,-1,-1),(1,-1,-1),(1,1,-1),(-1,1,-1),(-1,-1,1),(1,-1,1),(1,1,1),(-1,1,1)]:
            x*=s[0]/2;y*=s[1]/2;z*=s[2]/2
            vs.append((c[0]+x*cs-y*sn,c[1]+x*sn+y*cs,c[2]+z))
        self.add(vs,[(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)],mat)
    def rod(self,a,b,r,mat,n=10,r2=None):
        a=Vector(a);b=Vector(b);axis=(b-a).normalized()
        u=axis.cross(Vector((0,0,1)) if abs(axis.z)<.95 else Vector((0,1,0))).normalized();v=axis.cross(u)
        vs=[p+(u*math.cos(2*math.pi*i/n)+v*math.sin(2*math.pi*i/n))*radius for p,radius in [(a,r),(b,r if r2 is None else r2)] for i in range(n)]
        faces=[tuple(reversed(range(n))),tuple(range(n,2*n))]+[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
        self.add(vs,faces,mat)
    def ring(self,c,r,thick,mat,n=12,k=5,plane='XY'):
        vs=[]
        for i in range(n):
            a=2*math.pi*i/n
            for j in range(k):
                b=2*math.pi*j/k;x=(r+thick*math.cos(b))*math.cos(a);y=(r+thick*math.cos(b))*math.sin(a);z=thick*math.sin(b)
                if plane=='XZ':y,z=z,y
                vs.append((c[0]+x,c[1]+y,c[2]+z))
        self.add(vs,[(i*k+j,((i+1)%n)*k+j,((i+1)%n)*k+(j+1)%k,i*k+(j+1)%k) for i in range(n) for j in range(k)],mat)
    def leaf(self,a,b,w,mat):
        a=Vector(a);b=Vector(b);d=b-a
        u=d.cross(Vector((0,0,1)) if abs(d.normalized().z)<.95 else Vector((0,1,0))).normalized()*w
        mid=a+d*.48;ridge=mid+Vector((0,0,.035))
        self.add([a,mid+u,b,mid-u,ridge,ridge-Vector((0,0,.009))],[(0,1,4),(1,2,4),(2,3,4),(3,0,4),(1,0,5),(2,1,5),(3,2,5),(0,3,5)],mat)
    def object(self,name,coll,part=None,bevel=0):
        data=bpy.data.meshes.new(name+'_Mesh');data.from_pydata(self.v,[],self.f);data.update()
        for m in self.mats:data.materials.append(m)
        for p,i in zip(data.polygons,self.mi):p.material_index=i
        uv=data.uv_layers.new(name='UVMap')
        for face in data.polygons:
            dominant=max(range(3),key=lambda i:abs(face.normal[i]));axes=[i for i in range(3) if i!=dominant]
            for loop in face.loop_indices:
                co=data.vertices[data.loops[loop].vertex_index].co;uv.data[loop].uv=(co[axes[0]],co[axes[1]])
        obj=bpy.data.objects.new(name,data);coll.objects.link(obj);obj.parent=root
        obj['interior_scope']='First-floor hall, corridor and second-floor landing'
        if part:obj['export_separately']=True;obj['unreal_asset']=assetbase+part
        if bevel:
            mod=obj.modifiers.new('Soft stylized edges','BEVEL');mod.width=bevel;mod.segments=2;mod.limit_method='ANGLE'
        return obj

shell=Mesh();floors=Mesh();trim=Mesh();stair=Mesh();reception=Mesh();waiting=Mesh();decor=Mesh();fixtures=Mesh()
groups={'shell':shell,'floors':floors,'trim':trim,'stair':stair,'reception':reception,'waiting':waiting,'decor':decor,'fixtures':fixtures}
font=bpy.data.fonts.load('C:/Windows/Fonts/georgia.ttf',check_existing=True)
labels=[]
def label(body,location,size,mat,rotation=(math.pi/2,0,0),part=None,name=None):
    data=bpy.data.curves.new('Interior lettering','FONT');data.body=body;data.size=size;data.align_x='CENTER';data.align_y='CENTER';data.font=font;data.extrude=.0005;data.resolution_u=3;data.materials.append(mat)
    obj=bpy.data.objects.new('DORM_INT_Label_'+(name or body),data);furniture.objects.link(obj);obj.parent=root;obj.location=location;obj.rotation_euler=rotation
    if part:obj['export_separately']=True;obj['unreal_asset']=assetbase+part;obj['export_support']=True
    labels.append(obj)
    return obj

def wall(axis,pos,u0,u1,z0,z1,holes=(),thick=.16):
    us=sorted(set([u0,u1]+[max(u0,min(u1,h[i])) for h in holes for i in [0,1]]))
    zs=sorted(set([z0,z1]+[max(z0,min(z1,h[i])) for h in holes for i in [2,3]]))
    for a,b in zip(us,us[1:]):
        for c,d in zip(zs,zs[1:]):
            if b-a<.001 or d-c<.001 or any(h[0]<(a+b)/2<h[1] and h[2]<(c+d)/2<h[3] for h in holes):continue
            center=((a+b)/2,pos,(c+d)/2) if axis=='X' else (pos,(a+b)/2,(c+d)/2)
            size=(b-a,thick,d-c) if axis=='X' else (thick,b-a,d-c)
            shell.box(center,size,plaster)

def panel_run(axis,pos,u0,u1,z=.45,holes=()):
    cuts=sorted(set([u0,u1]+[max(u0,min(u1,h[i])) for h in holes for i in [0,1]]))
    def box(u,zz,w,h,depth,mat):
        trim.box((u,pos,zz) if axis=='X' else (pos,u,zz),(w,depth,h) if axis=='X' else (depth,w,h),mat)
    for a,b in zip(cuts,cuts[1:]):
        if b-a<.08 or any(h[0]<(a+b)/2<h[1] and h[2]<z+1.02 and h[3]>z for h in holes):continue
        box((a+b)/2,z+.49,b-a,.98,.042,oak)
        box((a+b)/2,z+.07,b-a,.14,.075,walnut)
        box((a+b)/2,z+1.02,b-a,.075,.09,walnut)
        n=max(1,round((b-a)/.85));w=(b-a)/n
        for i in range(n):
            u=a+(i+.5)*w
            box(u,z+.52,w-.11,.68,.056,walnut)
            box(u,z+.52,w-.16,.62,.066,oak)
            box(a+i*w+.025,z+.53,.055,.91,.076,walnut)
        box(b-.025,z+.53,.055,.91,.076,walnut)

def floor_region(x0,x1,y0,y1):
    floors.box(((x0+x1)/2,(y0+y1)/2,.375),(x1-x0,y1-y0,.10),grout)
    nx=math.ceil((x1-x0)/.62);ny=math.ceil((y1-y0)/.62);sx=(x1-x0)/nx;sy=(y1-y0)/ny
    for i in range(nx):
        for j in range(ny):floors.box((x0+(i+.5)*sx,y0+(j+.5)*sy,.438),(sx-.009,sy-.009,.024),tile_a if rng.random()<.7 else tile_b)
floor_region(-6.2,6.2,-8.68,-2.55)
floor_region(-1.65,1.65,-2.55,7.45)
# Structural second floor: four slabs around a genuine open atrium/stairwell.
for x0,x1,y0,y1 in [(-12.65,-6.2,-8.65,8.65),(6.2,12.65,-8.65,8.65),(-6.2,6.2,-2.55,8.65)]:
    shell.box(((x0+x1)/2,(y0+y1)/2,2.77),(x1-x0,y1-y0,.16),plaster)
shell.box((0,0,5.175),(25.3,17.3,.15),plaster)
floors.box((0,-1.82,2.867),(12.4,1.46,.034),oak)
floors.box((0,.26,2.867),(3.3,2.7,.034),oak)

front_holes=[(-1.15,1.15,.45,2.91),(-1.2,1.2,3.075,5.1)]
for xc in [-3.7,3.7]:
    for dz in [0,2.4]:front_holes.append((xc-.89,xc+.89,.74+dz,2.595+dz))
wall('X',-8.64,-6.2,6.2,.45,5.1,front_holes,.08)
panel_run('X',-8.57,-6.2,6.2,holes=front_holes)
for xc in [-3.7,3.7]:
    trim.box((xc,-8.56,.59),(1.78,.075,.28),oak)
    trim.box((xc,-8.54,.75),(1.9,.22,.07),walnut)
for side in [-1,1]:
    wall('Y',side*6.18,-8.6,-2.47,.45,5.1)
    panel_run('Y',side*6.075,-8.6,-2.55)
    wall('X',-2.47,-6.2 if side<0 else 1.65,-1.65 if side<0 else 6.2,.45,2.69)
    panel_run('X',-2.575,-6.2 if side<0 else 1.65,-1.65 if side<0 else 6.2)

door_centers=[-.65,2.1,4.85]
door_holes=[(y-.52,y+.52,.45,2.55) for y in door_centers]
for side in [-1,1]:
    wall('Y',side*1.74,-2.55,7.53,.45,2.69,door_holes,.18)
    panel_run('Y',side*1.625,-2.55,7.45,holes=door_holes)
wall('X',7.53,-1.65,1.65,.45,2.69,[(-.52,.52,.45,2.55)])
panel_run('X',7.425,-1.65,1.65,holes=[(-.52,.52,.45,2.55)])
# Second-floor gallery and a short real circulation landing, ending at a closed door.
for a,b in [(-6.2,-1.65),(1.65,6.2)]:wall('X',-1.0,a,b,2.884,5.1)
for side in [-1,1]:
    wall('Y',side*1.74,-1.0,1.69,2.884,5.1,thick=.18)
    panel_run('Y',side*1.625,-1,1.6,z=2.884)
wall('X',1.69,-1.65,1.65,2.884,5.1,[(-.52,.52,2.884,4.984)])
for y in [-7.5,-4.45]:trim.box((0,y,4.98),(12.35,.20,.24),stone)
trim.box((0,-2.65,2.62),(12.4,.20,.14),stone)
for x in [-1.85,1.85]:trim.box((x,-2.64,1.565),(.19,.18,2.23),stone)

# 14 comfortable risers, 300 mm treads, 1.65 m usable stair width.
stair_x=-4.88;y0=-6.75;run=.30;rise=(2.884-.45)/14
for i in range(14):
    top=.45+(i+1)*rise;yc=y0+(i+.5)*run
    stair.box((stair_x,yc,(top+.45)/2),(1.65,run,top-.45),stone)
    stair.box((stair_x,yc-.014,top-.016),(1.69,run+.035,.032),tile_b)
for x in [stair_x-.87,stair_x+.87]:
    for i in range(15):
        y=y0+i*run;z=.45+min(i+1,14)*rise
        stair.box((x,y,z+.49),(.065,.065,.98),walnut)
        if i%4==0 or i==14:
            stair.box((x,y,z+.50),(.13,.13,1.0),oak)
            stair.box((x,y,z+1.01),(.17,.17,.055),walnut)
    stair.rod((x,y0,.45+rise+1.035),(x,-2.55,2.884+1.035),.052,oak,10)
    stair.rod((x,y0,.45+rise+.17),(x,-2.55,2.884+.17),.035,walnut,8)
# Gallery railing leaves the full stair exit open.
for a,b in [(-6.08,-5.82),(-3.94,6.08)]:
    stair.box(((a+b)/2,-2.57,3.87),(b-a,.14,.09),oak)
    stair.box(((a+b)/2,-2.57,3.02),(b-a,.09,.10),walnut)
    n=max(1,math.ceil((b-a)/.22))
    for i in range(n+1):
        x=a+(b-a)*i/n;stair.box((x,-2.57,3.43),(.058,.058,.80),oak)
    for x in [a,b]:
        stair.box((x,-2.57,3.39),(.17,.17,1.02),walnut)
        stair.box((x,-2.57,3.92),(.22,.22,.06),oak)

def room_frame(axis,pos,u,bottom,number):
    def box(t,z,w,h,dep,mat):trim.box((t,pos,z) if axis=='X' else (pos,t,z),(w,dep,h) if axis=='X' else (dep,w,h),mat)
    for t in [u-.585,u+.585]:box(t,bottom+1.07,.13,2.14,.14,walnut)
    box(u,bottom+2.17,1.30,.14,.17,oak)
    box(u,bottom+2.17,.29,.09,.19,brass)
    if axis=='X':loc=(u,pos-.101,bottom+2.17);rot=(math.pi/2,0,0)
    elif pos>0:loc=(pos-.101,u,bottom+2.17);rot=(math.pi/2,0,-math.pi/2)
    else:loc=(pos+.101,u,bottom+2.17);rot=(math.pi/2,0,math.pi/2)
    label(number,loc,.068,walnut,rot,name='Room_'+number)

leaf=Mesh();leaf.box((.5,0,1.04),(1,.075,2.08),oak)
for sign in [-1,1]:
    for z,h in [(.49,.68),(1.49,.82)]:
        leaf.box((.5,sign*.043,z),(.80,.022,h),walnut)
        leaf.box((.5,sign*.057,z),(.73,.012,h-.07),oak)
    leaf.box((.86,sign*.063,1.02),(.07,.025,.20),brass)
    leaf.rod((.86,sign*.075,1.05),(.86,sign*.13,1.05),.022,brass,10)
    leaf.rod((.86,sign*.13,1.05),(.73,sign*.13,1.05),.018,brass,10)
template=leaf.object('DORM_INT_Door_101',doors_coll,'SM_Dormitory_InteriorDoor',.003)
door_placements=[];idx=0
for side in [-1,1]:
    for j,y in enumerate(door_centers):
        number=str(101+j*2+(1 if side>0 else 0))
        obj=template if idx==0 else template.copy()
        if idx:doors_coll.objects.link(obj);obj['export_instance']=True
        obj.name='DORM_INT_Door_'+number;obj.location=(side*1.74,y-.5,.46);obj.rotation_euler.z=math.pi/2
        obj['hinge_axis']='Local +Z';obj['room_number']=number
        room_frame('Y',side*1.635,y,.45,number)
        door_placements.append(obj);idx+=1
for number,y,z in [('107',7.53,.46),('201',1.69,2.894)]:
    obj=template.copy();doors_coll.objects.link(obj);obj.name='DORM_INT_Door_'+number;obj['export_instance']=True;obj['room_number']=number
    obj.location=(-.5,y,z);obj.rotation_euler.z=0;door_placements.append(obj)
    room_frame('X',y-.095,0,z-.01,number)

def chair(g,x,y,z,upholstery=fabric,wide=.68):
    for dx in [-wide*.38,wide*.38]:
        for dy in [-.25,.25]:g.box((x+dx,y+dy,z+.23),(.065,.065,.46),walnut)
    g.box((x,y,z+.43),(wide,.65,.13),oak)
    g.box((x,y-.02,z+.51),(wide-.08,.58,.13),upholstery)
    g.box((x,y+.27,z+.83),(wide-.03,.14,.59),walnut)
    g.box((x,y+.185,z+.85),(wide-.11,.09,.46),upholstery)
    for dx in [-wide/2,wide/2]:
        g.box((x+dx,y,z+.68),(.075,.69,.09),oak)
        g.box((x+dx,y-.23,z+.56),(.055,.055,.25),walnut)

def book(g,x,y,z,w=.12,h=.25,mat=fabric):
    g.box((x,y,z+h/2),(w,.18,h),mat);g.box((x,y-.002,z+h/2),(w-.016,.184,h-.025),paper)
    g.box((x,y-.098,z+h/2),(w,.018,h),mat)
    g.box((x,y-.109,z+h*.75),(w*.65,.004,.012),brass)

# Concierge's L-shaped paneled counter and working side.
for c,s in [((3.9,-4.72,.96),(3.35,.70,1.02)),((5.35,-3.91,.96),(.45,1.65,1.02))]:reception.box(c,s,oak)
reception.box((3.9,-4.72,1.51),(3.58,.89,.13),walnut)
reception.box((5.35,-3.89,1.51),(.68,1.67,.13),walnut)
reception.box((3.9,-4.72,.53),(3.52,.82,.16),walnut)
for x in [2.63,3.47,4.31,5.15]:
    reception.box((x,-5.083,1.01),(.69,.035,.73),walnut)
    reception.box((x,-5.105,1.01),(.61,.024,.65),oak)
    reception.box((x-.39,-5.10,1.0),(.055,.07,.91),walnut)
reception.box((3.85,-3.97,1.19),(2.45,.58,.08),oak)
chair(reception,4.0,-3.08,.45,rug,.65)
for i in range(4):book(reception,2.65+i*.13,-4.72,1.575,.105,.22+(i%2)*.05,[fabric,walnut,rug,oak][i])
reception.box((4.35,-4.77,1.59),(.46,.32,.025),paper)
reception.box((4.35,-4.77,1.607),(.016,.31,.009),walnut)
reception.rod((4.75,-4.8,1.58),(4.75,-4.8,1.72),.05,stone,12)
reception.ring((4.81,-4.8,1.66),.04,.009,stone,10,5,'XZ')
reception.box((3.9,-5.13,1.64),(.67,.06,.16),brass)
label('CONCIERGE',(3.9,-5.166,1.64),.075,walnut,part='SM_Dormitory_Reception')

# Key pigeonholes and noticeboard sit behind the counter, as in the references.
reception.box((5.18,-2.66,1.93),(1.52,.14,1.34),walnut)
for i in range(5):reception.box((4.42+i*.38,-2.79,1.93),(.035,.29,1.34),oak)
for j in range(4):reception.box((5.18,-2.79,1.26+j*.445),(1.55,.29,.036),oak)
for row in range(3):
    for col in range(4):
        x=4.61+col*.38;z=1.47+row*.445
        reception.ring((x,-2.824,z+.065),.032,.007,brass,8,4,'XZ')
        reception.rod((x,-2.824,z+.034),(x,-2.824,z-.055),.009,brass,6)
        reception.box((x+.015,-2.824,z-.04),(.04,.018,.012),brass)
        reception.box((x,-2.95,z-.12),(.14,.025,.06),brass)
        label(str(101+row*4+col),(x,-2.967,z-.12),.039,walnut,part='SM_Dormitory_Reception',name='Key_'+str(row*4+col))
reception.box((3.16,-2.68,1.96),(1.82,.12,1.30),walnut)
reception.box((3.16,-2.756,1.96),(1.68,.04,1.16),oak)
label('DORMITORY',(3.16,-2.787,2.43),.13,paper,part='SM_Dormitory_Reception')
for i in range(7):
    x=2.60+(i%3)*.52;z=2.14-(i//3)*.31
    reception.box((x,-2.79,z),(.38,.009,.25),paper,rot=0)
    reception.rod((x,-2.80,z+.10),(x,-2.814,z+.10),.013,brass,7)
    for k in range(3):reception.box((x,-2.797,z+.045-k*.04),(.25-k*.035,.004,.008),walnut)

def banker_lamp(g,x,y,z):
    g.rod((x,y,z),(x,y,z+.035),.14,brass,16)
    g.rod((x,y,z+.035),(x,y,z+.37),.019,brass,10)
    g.rod((x-.18,y,z+.36),(x+.18,y,z+.36),.013,brass,10)
    n=12;vs=[]
    for yy in [-.11,.11]:
        for i in range(n+1):
            a=math.pi*i/n;vs.append((x+.25*math.cos(a),y+yy,z+.38+.13*math.sin(a)))
    g.add(vs,[(i,i+1,n+2+i,n+1+i) for i in range(n)],fabric)
    g.box((x,y,z+.385),(.45,.19,.014),glow)
banker_lamp(reception,3.22,-4.72,1.58)

# Waiting nook: two padded armchairs, low table, books and a shaded reading lamp.
chair(waiting,-3.20,-4.43,.45);chair(waiting,-2.20,-4.43,.45)
waiting.box((-2.70,-5.45,.91),(1.48,.65,.10),walnut)
for x in [-3.28,-2.12]:
    for y in [-5.68,-5.22]:waiting.box((x,y,.68),(.07,.07,.46),oak)
waiting.box((-2.70,-5.45,.62),(1.30,.52,.055),oak)
waiting.box((-2.96,-5.40,.975),(.37,.26,.045),fabric)
waiting.box((-2.96,-5.40,1.006),(.32,.24,.018),paper)
waiting.rod((-2.32,-5.4,.96),(-2.32,-5.4,1.07),.047,stone,12)
waiting.ring((-2.26,-5.4,1.025),.033,.008,stone,10,4,'XZ')
waiting.rod((-3.73,-4.43,.45),(-3.73,-4.43,.50),.19,brass,14)
waiting.rod((-3.73,-4.43,.50),(-3.73,-4.43,1.78),.022,brass,10)
waiting.rod((-3.73,-4.43,1.65),(-3.73,-4.43,1.97),.25,paper,14,.13)
waiting.rod((-3.73,-4.43,1.642),(-3.73,-4.43,1.649),.21,glow,14)

def carpet(x,y,w,d):
    decor.box((x,y,.455),(w,d,.010),rug)
    for inset,thick in [(.07,.028),(.15,.012)]:
        for yy in [y-d/2+inset,y+d/2-inset]:decor.box((x,yy,.461),(w-2*inset,thick,.002),stone)
        for xx in [x-w/2+inset,x+w/2-inset]:decor.box((xx,y,.461),(thick,d-2*inset,.002),stone)
carpet(0,-6.55,3.15,2.25);carpet(-2.82,-4.95,2.55,2.14);carpet(0,2.36,1.55,8.9)
# Woven-looking crest made from a few flat geometric leaves and a building emblem.
for side in [-1,1]:
    for i in range(8):
        a=-.95+i*.22;x=side*(.56+.10*math.cos(a));y=-6.55+.63*math.sin(a)
        decor.leaf((x,y,.463),(x-side*.14,y+.12,.464),.038,stone)
decor.box((0,-6.55,.464),(.62,.025,.002),stone)
decor.box((0,-6.43,.464),(.025,.25,.002),stone)
for x in [-.24,.24]:decor.box((x,-6.43,.464),(.025,.25,.002),stone)
decor.add([(-.35,-6.29,.465),(.35,-6.29,.465),(0,-6.10,.465)],[(0,1,2)],stone)
for x in [-.16,0,.16]:decor.box((x,-6.42,.465),(.045,.06,.002),stone)

def plant(x,y,z,scale=1):
    decor.rod((x,y,z),(x,y,z+.39*scale),.17*scale,stone,12,.23*scale)
    decor.ring((x,y,z+.39*scale),.225*scale,.028*scale,stone,12,5)
    decor.rod((x,y,z+.375*scale),(x,y,z+.385*scale),.20*scale,soil,12)
    for stem in range(3):
        a=stem*2.1;bx=x+.08*scale*math.cos(a);by=y+.08*scale*math.sin(a)
        height=(.90+stem*.15)*scale
        decor.rod((x,y,z+.38*scale),(bx,by,z+height),.012*scale,walnut,6)
        for j in range(7):
            angle=a+j*2.35;h=z+(.48+j*.075)*scale;radius=(.26+.10*math.sin(j))*scale
            start=(bx,by,h);tip=(bx+radius*math.cos(angle),by+radius*math.sin(angle),h+.12*scale)
            decor.leaf(start,tip,.095*scale,green if (j+stem)%2 else leaf_light)
for p in [(5.65,-6.8,.45,1.15),(-5.84,-7.75,.45,.92),(1.22,-2.88,.45,.85),(-1.18,6.9,.45,.8),(5.7,-1.65,2.884,.9)]:plant(*p)

def picture(axis,pos,u,z,w=.63,h=.76):
    def box(uu,zz,ww,hh,dep,mat):decor.box((uu,pos,zz) if axis=='X' else (pos,uu,zz),(ww,dep,hh) if axis=='X' else (dep,ww,hh),mat)
    box(u,z,w,h,.055,walnut);box(u,z,w-.07,h-.07,.065,stone);box(u,z,w-.12,h-.12,.070,tile_a)
    # Small raised geometric landscape, shared palette.
    box(u,z-h*.19,w-.15,h*.24,.074,fabric)
    for j in [-1,0,1]:box(u+j*w*.20,z-.03,.035,h*.31,.079,walnut)
for side in [-1,1]:
    for y in [.7,3.48,6.25]:picture('Y',side*1.60,y,1.98,.53,.64)
for y in [-6.55,-3.4]:picture('Y',6.065,y,2.25,.74,.92)
picture('X',-2.58,-2.6,1.97,.78,.83)

def sconce(axis,pos,u,z):
    c=(u,pos,z) if axis=='X' else (pos,u,z)
    fixtures.box(c,(.18,.09,.40) if axis=='X' else (.09,.18,.40),walnut)
    fixtures.box(c,(.13,.14,.29) if axis=='X' else (.14,.13,.29),glow)
    for dz in [-.16,.16]:fixtures.box((c[0],c[1],z+dz),(.20,.18,.045) if axis=='X' else (.18,.20,.045),brass)
    return c
light_specs=[]
for side in [-1,1]:
    for y in [-7.25,-3.3]:
        c=sconce('Y',side*6.02,y,2.50);light_specs.append((f'Hall_Wall_{side}_{y}',(c[0]-side*.18,c[1],c[2]),75,.45))
    for y in [.7,3.48,6.25]:
        c=sconce('Y',side*1.57,y,2.05);light_specs.append((f'Corridor_Wall_{side}_{y}',(c[0]-side*.12,c[1],c[2]),35,.25))
def ceiling_lamp(x,y,top,r,drop):
    fixtures.rod((x,y,top-.035),(x,y,top),r*.43,brass,16)
    if drop>.2:fixtures.rod((x,y,top-drop+.15),(x,y,top-.035),.023,brass,10)
    z=top-drop
    fixtures.rod((x,y,z),(x,y,z+.13),r,glow,20)
    for zz in [z,z+.13]:fixtures.ring((x,y,zz),r,.025,brass,20,5)
    for i in range(6):
        a=i*math.pi/3;fixtures.rod((x+r*math.cos(a),y+r*math.sin(a),z),(x+r*math.cos(a),y+r*math.sin(a),z+.13),.011,brass,6)
    light_specs.append(('Ceiling_'+str(y),(x,y,z-.06),180 if drop>.2 else 65,.65 if drop>.2 else .3))
for y in [-7.1,-4.2]:ceiling_lamp(0,y,4.86,.38,.37)
for y in [-.6,2.7,5.9]:ceiling_lamp(0,y,2.69,.22,.14)
ceiling_lamp(0,-1.75,5.10,.28,.16)
light_specs.extend([('Banker',(3.22,-4.72,1.95),22,.18),('Reading',(-3.73,-4.43,1.68),35,.22)])
for name,location,power,radius in light_specs:
    data=bpy.data.lights.new('DORM_INT_'+name,'POINT');data.energy=power;data.color=(1,.74,.43);data.shadow_soft_size=radius
    obj=bpy.data.objects.new('DORM_INT_'+name,data);lights_coll.objects.link(obj);obj.parent=root;obj.location=location
    obj['export_helper']=True

created=[]
created.append(shell.object('DORM_INT_Architecture',architecture))
created.append(floors.object('DORM_INT_Floors',architecture))
created.append(trim.object('DORM_INT_Wall_Panelling',architecture,None,.003))
created.append(stair.object('DORM_INT_Stairs_Gallery_Rails',architecture,None,.004))
created.append(reception.object('DORM_INT_Reception',furniture,'SM_Dormitory_Reception',.006))
created.append(waiting.object('DORM_INT_WaitingArea',furniture,'SM_Dormitory_WaitingArea',.008))
created.append(decor.object('DORM_INT_InteriorDecor',furniture,'SM_Dormitory_InteriorDecor'))
created.append(fixtures.object('DORM_INT_InteriorLights',furniture,'SM_Dormitory_InteriorLights'))
bpy.context.view_layer.update()
for name,digest in originals.items():assert fingerprint(bpy.data.objects[name])==digest, 'Exterior changed: '+name
assert all(p.area>1e-12 for o in created+[template] for p in o.data.polygons), 'Degenerate interior polygon'
for obj in created+door_placements:
    pts=[obj.matrix_world@v.co for v in obj.data.vertices]
    assert all(-12.651<=p.x<=12.651 and -8.681<=p.y<=8.651 and .30<=p.z<=5.251 for p in pts), 'Interior outside envelope: '+obj.name
manifest_path=SOURCE/'interior_materials.json';manifest_path.write_text(json.dumps(manifest,indent=2),encoding='utf-8')
placement={'assets':[], 'doors':[],'floor_levels_m':[.45,2.884],'stair_risers':14,'stair_rise_m':rise,'stair_tread_m':.3,'exterior_objects_preserved':len(originals),'original_hashes':originals}
for obj in created:
    placement['assets'].append({'object':obj.name,'asset':obj.get('unreal_asset','/Game/Art/Models/Buildings/Dormitory/SM_Dormitory_Blockout'),'location_m':list(obj.location)})
for obj in door_placements:
    placement['doors'].append({'object':obj.name,'asset':obj['unreal_asset'],'location_blender_m':list(obj.location),'rotation_blender_deg':[math.degrees(a) for a in obj.rotation_euler]})
(SOURCE/'interior_layout.json').write_text(json.dumps(placement,indent=2),encoding='utf-8')
(LOG/'dormitory_interior_build.json').write_text(json.dumps({'fixed_mesh_groups':4,'furnishing_mesh_groups':4,'door_instances':len(door_placements),'shared_door_meshes':1,'new_materials':len(manifest),'editable_texts':len(labels),'blender_lights':len(light_specs),'exterior_unchanged':len(originals)},indent=2),encoding='utf-8')
result={'fixed_mesh_groups':4,'furnishing_mesh_groups':4,'door_instances':len(door_placements),'shared_door_meshes':1,'new_materials':len(manifest),'editable_texts':len(labels),'blender_lights':len(light_specs),'exterior_unchanged':len(originals)}
