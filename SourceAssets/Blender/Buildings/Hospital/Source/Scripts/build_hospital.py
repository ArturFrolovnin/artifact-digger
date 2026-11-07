"""Standalone hospital concept blockout. Run in a fresh Blender file only."""
import bpy, math, random, os, json
from mathutils import Vector
from pathlib import Path
BASE = Path(__file__).resolve().parents[2]
SOURCE = BASE / 'Source' / 'Hospital_Blockout.blend'
PREVIEW = BASE / 'Previews'
PREVIEW.mkdir(parents=True, exist_ok=True)
random.seed(12)
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.context.preferences.filepaths.save_version = 0
scene = bpy.context.scene
scene.name = 'Hospital_Blockout'
scene.unit_settings.system = 'METRIC'
scene.unit_settings.scale_length = 1
building = bpy.data.collections.new('BLD_Hospital')
scene.collection.children.link(building)
root = bpy.data.objects.new('Hospital_ROOT', None)
building.objects.link(root)
root['body_footprint_m'] = '20 x 14'
root['storeys'] = 2
root['status'] = 'First prototype; awaiting user review; no UE export'
groups = {}
for name in ['Walls','Roof','Windows','Entrance','Trim','Props','Ambulance_Bay']:
    col = bpy.data.collections.new(name)
    building.children.link(col)
    parent = bpy.data.objects.new('Hospital_'+name, None)
    col.objects.link(parent)
    parent.parent = root
    groups[name] = (col,parent)
stage = bpy.data.collections.new('Presentation')
scene.collection.children.link(stage)
def mat(name,color,rough=.65,metal=0):
    m=bpy.data.materials.new(name); m.diffuse_color=(*color,1); m.use_nodes=True
    p=m.node_tree.nodes.get('Principled BSDF'); p.inputs['Base Color'].default_value=(*color,1)
    p.inputs['Roughness'].default_value=rough; p.inputs['Metallic'].default_value=metal
    return m
plaster=mat('HOS_Warm_Ivory_Plaster',(.70,.62,.46))
stone=mat('HOS_Limestone_Trim',(.81,.73,.57))
brick=mat('HOS_Peach_Stone_Inserts',(.55,.34,.22))
base=mat('HOS_Plinth',(.34,.35,.31))
roofmat=mat('HOS_Terracotta_Base',(.29,.075,.035))
tiles=[mat('HOS_Tile_'+str(i),(.34+i*.022,.105+i*.009,.055+i*.005)) for i in range(5)]
frame=mat('HOS_Painted_Sage_Frames',(.18,.26,.25),.38)
glass=mat('HOS_Blue_Glass',(.075,.18,.22),.2,.28)
warm=mat('HOS_Warm_Interior',(.39,.31,.16),.4)
dark=mat('HOS_Recess_Shadow',(.038,.055,.06))
red=mat('HOS_Medical_Red',(.64,.055,.035),.45)
metal=mat('HOS_Handrail_Steel',(.34,.39,.38),.3,.7)
wood=mat('HOS_Bench_Wood',(.32,.15,.055))
leaf=mat('HOS_Greenery',(.16,.27,.06))
def link(o,group):
    if group=='Presentation': stage.objects.link(o)
    else:
        groups[group][0].objects.link(o); o.parent=groups[group][1]
    return o
def mesh(name,verts,faces,m,group='Roof'):
    d=bpy.data.meshes.new(name); d.from_pydata(verts,[],faces); d.update()
    o=bpy.data.objects.new(name,d); link(o,group)
    if m:d.materials.append(m)
    return o
def box(name,loc,size,m,group='Trim',bevel=.025):
    x,y,z=[v/2 for v in size]
    o=mesh(name,[(-x,-y,-z),(x,-y,-z),(x,y,-z),(-x,y,-z),(-x,-y,z),(x,-y,z),(x,y,z),(-x,y,z)],[(0,3,2,1),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7),(4,5,6,7)],m,group)
    o.location=loc
    if bevel:
        mod=o.modifiers.new('Soft_Edges','BEVEL');mod.width=bevel;mod.segments=2
        mod=o.modifiers.new('Weighted_Normals','WEIGHTED_NORMAL')
    return o
def beam(name,a,b,r,m,group='Trim'):
    a,b=Vector(a),Vector(b)
    o=box(name,(a+b)/2,(r,r,(b-a).length),m,group,r*.2)
    o.rotation_euler=(b-a).to_track_quat('Z','Y').to_euler();return o
def text(name,body,loc,size,m,group='Entrance',rot=(math.pi/2,0,0)):
    d=bpy.data.curves.new(name,'FONT');d.body=body;d.align_x='CENTER';d.align_y='CENTER';d.size=size;d.extrude=.008;d.bevel_depth=.002
    o=bpy.data.objects.new(name,d);link(o,group);o.location=loc;o.rotation_euler=rot;d.materials.append(m);return o
def cross(name,x,y,z,s=1):
    box(name+'_V',(x,y,z),(.28*s,.12,1*s),red,'Entrance')
    box(name+'_H',(x,y-.005,z),(1*s,.13,.28*s),red,'Entrance')
# Main walls have actual openings, with glazing recessed behind their outer face.
def facade(label,length,origin,angle,centers,door=None):
    ca,sa=math.cos(angle),math.sin(angle)
    def pos(u,v,z):return (origin[0]+ca*u-sa*v,origin[1]+sa*u+ca*v,z)
    def fb(n,u,v,z,w,d,h,m,g='Walls',bev=.018):
        o=box(label+'_'+n,pos(u,v,z),(w,d,h),m,g,bev);o.rotation_euler.z=angle;return o
    holes=[]
    for u in centers:
        for z in [2.0,5.1]:holes.append((u- .67,u+.67,z-.98,z+.98,'window'))
    if door:holes.append((door[0]-door[1]/2,door[0]+door[1]/2,.45,2.95,'door'))
    cuts=sorted(set([-length/2,length/2]+[x for h in holes for x in h[:2]]))
    for a,b in zip(cuts,cuts[1:]):
        if b-a<.001:continue
        blocked=sorted([(h[2],h[3]) for h in holes if h[0]<(a+b)/2<h[1]])
        z=.48
        for lo,hi in blocked+[(6.65,6.65)]:
            if lo>z:fb('Wall', (a+b)/2,.19,(z+lo)/2,b-a,.38,lo-z,plaster)
            z=max(z,hi)
    for a,b,lo,hi,kind in holes:
        if kind!='window':continue
        u=(a+b)/2;z=(lo+hi)/2;w=b-a;h=hi-lo
        fb('Interior',u,.32,z,w,.06,h,dark,'Windows')
        fb('Glass',u,.20,z,w-.13,.04,h-.13,warm if random.random()<.22 else glass,'Windows',.005)
        for dx in [-w/2,w/2]:
            fb('Stone_Jamb',u+dx,-.035,z,.16,.22,h+.28,stone,'Windows')
            fb('Sash',u+dx*.88,.07,z,.055,.08,h,frame,'Windows',.008)
        for dz in [-h/2,h/2]:
            fb('Stone_Header',u,-.04,z+dz,w+.25,.24,.15,stone,'Windows')
            fb('Sash',u,.07,z+dz*.93,w,.09,.06,frame,'Windows',.006)
        fb('Transom',u,.065,z+.46,w,.09,.065,frame,'Windows',.006)
        fb('Mullion',u,.065,z-.22,.05,.09,1.42,frame,'Windows',.006)
        fb('Sill',u,-.14,lo-.05,w+.38,.4,.12,stone,'Windows')
    for z,h,dep,m in [(.24,.48,.52,base),(3.43,.23,.56,stone),(6.57,.19,.59,stone)]:
        fb('Belt',0,.16,z,length+.15,dep,h,m,'Trim')
    return fb
front=facade('Front',20,(0,-7),0,[-8,-5.5,5.5,8],(0,2.6))
back=facade('Back',20,(0,7),math.pi,[-8,-5.4,-2.7,0,2.7,5.4],(8,1.4))
right=facade('Right',14,(10,0),math.pi/2,[-4.7,-1.6,1.6,4.7])
left=facade('Left',14,(-10,0),-math.pi/2,[-4.7,-1.6,1.6,4.7])
box('Ground_Floor',(0,0,.45),(19.8,13.8,.15),dark,'Walls')
box('Upper_Floor',(0,0,3.5),(19.8,13.8,.18),dark,'Walls')
box('Ceiling',(0,0,6.55),(19.8,13.8,.16),dark,'Walls')
# Modest warm corner blocks; no classical colonnade.
for x in [-9.78,9.78]:
    for y in [-7.04,7.04]:
        for i in range(12):
            z=.76+i*.49
            if abs(z-3.43)<.22:continue
            box('Corner_Stone',(x,y,z),(.51,.17,.42),brick)
for x in [-10.04,10.04]:
    for y in [-6.78,6.78]:
        for i in range(12):
            z=.76+i*.49
            if abs(z-3.43)>.22:box('Corner_Return',(x,y,z),(.17,.51,.42),brick)
# Low hip roof, a 1.75 m rise. Tile courses are simple editable geometry.
roofverts=[(-10.5,-7.5,6.8),(10.5,-7.5,6.8),(10.5,7.5,6.8),(-10.5,7.5,6.8),(-3,0,8.55),(3,0,8.55)]
mesh('Hipped_Roof',roofverts,[(0,1,5,4),(1,2,5),(2,3,4,5),(3,0,4)],roofmat)
for y in [-7.43,7.43]:box('Eaves',(0,y,6.72),(21,.18,.22),stone,'Roof')
for x in [-10.43,10.43]:box('Eaves',(x,0,6.72),(.18,14.9,.22),stone,'Roof')
def tile_slope(name,A,B,C,D,rows):
    A,B,C,D=map(Vector,(A,B,C,D));vs=[];fs=[]
    for row in range(rows):
        t=row/rows;t2=min(1,(row+1.06)/rows)
        l=A.lerp(D,t);r=B.lerp(C,t);l2=A.lerp(D,t2);r2=B.lerp(C,t2)
        count=max(1,round((r-l).length/.44))
        for j in range(count):
            u=j/count+.005/count;v=(j+1)/count-.005/count
            pts=[l.lerp(r,u),l.lerp(r,(u+v)/2),l.lerp(r,v),l2.lerp(r2,v),l2.lerp(r2,(u+v)/2),l2.lerp(r2,u)]
            for k,p in enumerate(pts):p.z+=.025+(.025 if k in [1,4] else 0)
            n=len(vs);vs.extend(pts);fs.extend([(n,n+1,n+4,n+5),(n+1,n+2,n+3,n+4)])
    o=mesh(name,vs,fs,None)
    for m in tiles:o.data.materials.append(m)
    for p in o.data.polygons:p.material_index=random.randrange(5)
v=roofverts
tile_slope('Front_Tile_Courses',v[0],v[1],v[5],v[4],23)
tile_slope('Back_Tile_Courses',v[2],v[3],v[4],v[5],23)
tile_slope('Right_Tile_Courses',v[1],v[2],v[5],v[5],23)
tile_slope('Left_Tile_Courses',v[3],v[0],v[4],v[4],23)
for a,b in [(v[0],v[4]),(v[1],v[5]),(v[2],v[5]),(v[3],v[4]),(v[4],v[5])]:beam('Hip_Cap',a,b,.12,tiles[2],'Roof')
# Projecting central entrance, two-storey scale and short gable.
box('Entry_Center',(0,-7.26,3.71),(4.1,.6,6.52),plaster,'Walls')
for x in [-1.91,1.91]:
    box('Entry_Pier',(x,-7.62,4.09),(.32,.22,7.05),stone)
    for z in [1,1.55,2.1,2.65,3.2,3.75,4.3,4.85,5.4,5.95,6.5,7.05]:
        box('Entry_Pier_Insert',(x,-7.75,z),(.36,.08,.36),brick)
box('Entry_Upper',(0,-7.27,7.29),(4.1,.6,.78),plaster,'Walls')
mesh('Entry_Gable',[(-2.05,-7.58,7.68),(2.05,-7.58,7.68),(0,-7.58,8.95),(-2.05,-5.8,7.68),(2.05,-5.8,7.68),(0,-5.8,8.95)],[(0,1,2),(3,5,4),(0,3,4,1),(1,4,5,2),(2,5,3,0)],plaster,'Walls')
for s in [-1,1]:
    A=(s*2.25,-7.8,7.73); B=(0,-7.8,9.06); C=(0,-4.7,9.06);D=(s*2.25,-4.7,7.73)
    mesh('Entry_Roof',[A,B,C,D],[(0,1,2,3)],roofmat)
    tile_slope('Entry_Roof_Tiles',A,D,C,B,8)
    beam('Gable_Trim',(s*2.15,-7.69,7.63),(0,-7.69,8.96),.17,stone)
cross('Upper_Medical_Cross',0,-7.69,7.91,.92)
# Tall paired upper lobby windows intentionally distinct from the ward rhythm.
for x in [-.64,.64]:
    box('Lobby_Shadow',(x,-7.58,5.32),(1.12,.08,2.38),dark,'Windows')
    box('Lobby_Glass',(x,-7.64,5.32),(.98,.05,2.22),glass,'Windows')
    for dx in [-.56,.56]:box('Lobby_Jamb',(x+dx,-7.7,5.32),(.12,.16,2.55),stone,'Windows')
    for z in [4.15,6.49]:box('Lobby_Lintel',(x,-7.7,z),(1.22,.16,.13),stone,'Windows')
    for z in [4.9,5.72]:box('Lobby_Transom',(x,-7.7,z),(1.08,.09,.07),frame,'Windows')
box('Entrance_Recess',(0,-7.62,1.79),(2.76,.08,2.72),dark,'Entrance')
for x in [-.63,.63]:
    box('Door_Frame',(x,-7.73,1.71),(1.24,.11,2.5),frame,'Entrance')
    box('Door_Glass',(x,-7.8,1.81),(1.07,.04,2.10),warm,'Entrance')
    box('Door_Kickplate',(x,-7.83,.68),(1.05,.035,.23),metal,'Entrance')
    box('Door_Handle',(x*.2,-7.9,1.57),(.045,.1,.47),metal,'Entrance',.014)
box('Door_Transom',(0,-7.76,3.03),(2.62,.12,.21),glass,'Entrance')
box('Entrance_Landing',(0,-8.47,.225),(5.2,2.25,.45),stone,'Entrance')
for i in range(3):box('Entrance_Step',(0,-9.95+i*.3,.075*(i+1)),(4.1,.32,.15*(i+1)),stone,'Entrance')
for x in [-2.2,2.2]:
    box('Canopy_Square_Post',(x,-9.15,1.95),(.30,.30,3),stone,'Entrance')
box('Canopy_Slab',(0,-8.6,3.44),(5.35,3.15,.25),stone,'Entrance')
box('Canopy_Fascia',(0,-10.13,3.65),(5.4,.19,.54),stone,'Entrance')
box('Canopy_Cap',(0,-8.6,3.95),(5.58,3.32,.10),stone,'Entrance')
text('Hospital_Sign','HOSPITAL',(0,-10.245,3.64),.49,dark)
for x in [-2.2,2.2]:cross('Sign_Cross',x,-10.25,3.65,.34)
# Sideways ramp reaches the landing at x=2.6; unobstructed top landing.
mesh('Accessible_Ramp',[(2.6,-9.35,0),(8.3,-9.35,0),(8.3,-7.85,0),(2.6,-7.85,0),(2.6,-9.35,.45),(8.3,-9.35,.025),(8.3,-7.85,.025),(2.6,-7.85,.45)],[(0,3,2,1),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7),(4,5,6,7)],stone,'Entrance')
for y in [-9.35,-7.85]:
    for x in [2.7,4.05,5.4,6.75,8.2]:
        z=.45-(x-2.6)*.425/5.7
        beam('Ramp_Post',(x,y,z),(x,y,z+.9),.055,metal,'Entrance')
    for h in [.48,.91]:beam('Ramp_Rail',(2.6,y,.45+h),(8.3,y,.025+h),.055,metal,'Entrance')
# Functional side ambulance drop-off with independent canopy.
box('Bay_Paving',(12.2,1.8,.055),(4.4,8.5,.11),base,'Ambulance_Bay')
box('Bay_Canopy',(12.15,1.8,3.45),(4.6,8.7,.25),stone,'Ambulance_Bay')
box('Bay_Roof',(12.15,1.8,3.60),(4.7,8.8,.07),base,'Ambulance_Bay')
for y in [-2.35,5.95]:
    for x in [10.5,14.15]:box('Bay_Post',(x,y,1.73),(.20,.20,3.45),frame,'Ambulance_Bay')
box('Bay_Signboard',(12.15,-2.61,3.43),(4.2,.08,.43),stone,'Ambulance_Bay')
text('Bay_Sign','AMBULANCE',(12.15,-2.67,3.43),.28,red,'Ambulance_Bay')
for y in [-1.7,5.3]:box('Bay_Bollard',(13.65,y,.5),(.12,.12,1),red,'Ambulance_Bay')
# Back access and restrained equipment visible in orthographic views.
box('Service_Door',(-8,7.07,1.28),(1.4,.14,2.5),frame,'Props')
box('Service_Door_Panel',(-8,7.16,1.25),(1.17,.07,2.19),base,'Props')
box('Service_Awning',(-8,7.52,2.77),(2.05,1.13,.15),stone,'Props')
box('HVAC_Platform',(.4,1.6,8.46),(2.2,1.9,.20),base,'Roof')
box('HVAC_Unit',(.4,1.6,8.88),(1.55,1.35,.65),stone,'Roof')
for z in [8.65,8.77,8.89,9.01]:box('HVAC_Louvre',(.4,.906,z),(1.27,.05,.055),frame,'Roof',.005)
for x,y in [(-7,2.5),(7,2.5)]:
    box('Vent_Stack',(x,y,7.91),(.58,.65,1.16),plaster,'Roof')
    box('Vent_Cap',(x,y,8.53),(.76,.81,.13),stone,'Roof')
for x in [-1.7,-1.12]:beam('Back_Ladder',(x,7.25,.2),(x,7.25,7.1),.065,metal,'Props')
for i in range(23):beam('Ladder_Rung',(-1.7,7.25,.35+i*.3),(-1.12,7.25,.35+i*.3),.055,metal,'Props')
# A few large props frame the entrance without crowding the building.
for x,y,sx in [(-3.25,-9,1.1),(3.25,-9.95,1.1),(-8.7,-8.05,1.4),(8.7,-7.9,1.1)]:
    box('Planter',(x,y,.3),(sx,.78,.6),stone,'Props')
    box('Planter_Soil',(x,y,.61),(sx-.14,.64,.08),dark,'Props')
    for dx in [-.26,0,.26]:
        bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1,radius=.39,location=(x+dx,y,.83))
        o=bpy.context.object;o.name='HOS_Planter_Foliage'
        for c in list(o.users_collection):c.objects.unlink(o)
        link(o,'Props');o.data.materials.append(leaf)
for x in [-6.5]:
    for z in [.5,.82,1.04]:box('Bench_Slat',(x,-8.42 if z==.5 else -8.05,z),(2.0,.52 if z==.5 else .09,.13),wood,'Props')
    for dx in [-.75,.75]:box('Bench_Leg',(x+dx,-8.4,.27),(.1,.45,.5),frame,'Props')
# Presentation only: separate from the editable building hierarchy.
ground=mat('Presentation_Ground',(.24,.27,.26))
box('Ground',(0,0,-.16),(200,200,.28),ground,'Presentation',0)
world=bpy.data.worlds.new('Hospital_Daylight');scene.world=world;world.use_nodes=True
world.node_tree.nodes['Background'].inputs[0].default_value=(.57,.68,.82,1)
world.node_tree.nodes['Background'].inputs[1].default_value=.5
def light(name,kind,loc,power,size=5):
    d=bpy.data.lights.new(name,kind);d.energy=power
    if kind=='AREA':d.shape='DISK';d.size=size
    o=bpy.data.objects.new(name,d);stage.objects.link(o);o.location=loc;o.rotation_euler=(Vector((0,0,2))-o.location).to_track_quat('-Z','Y').to_euler();return o
sun=light('Sun','SUN',(-12,-15,24),2);sun.data.angle=math.radians(18)
light('Softbox','AREA',(4,-15,16),1800,12)
light('Back_Fill','AREA',(5,12,16),2200,15)
cameras={}
for name,loc,target,scale in [('Main',(28,-39,23),(1,-.6,3.2),34),('Front',(1,-45,4.4),(1,0,4.4),30),('Side',(45,0,4.6),(0,0,4.6),24),('Back',(1,45,4.5),(1,0,4.5),30),('Top',(1,0,50),(1,0,0),31)]:
    d=bpy.data.cameras.new(name);d.type='ORTHO';d.ortho_scale=scale
    o=bpy.data.objects.new('Camera_'+name,d);stage.objects.link(o);o.location=loc;o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler();cameras[name]=o
scene.camera=cameras['Main'];scene.render.engine='CYCLES';scene.cycles.samples=24
scene.cycles.use_denoising=True
scene.render.resolution_x=1400;scene.render.resolution_y=1000;scene.render.resolution_percentage=100
scene.view_settings.view_transform='AgX'
for a in bpy.context.screen.areas if bpy.context.screen else []:
    if a.type=='VIEW_3D':
        a.spaces.active.region_3d.view_rotation=cameras['Main'].rotation_euler.to_quaternion()
        a.spaces.active.region_3d.view_distance=36;a.spaces.active.region_3d.view_location=(1,0,3)
        a.spaces.active.shading.type='MATERIAL'
        a.spaces.active.overlay.show_overlays=False
bpy.ops.wm.save_as_mainfile(filepath=str(SOURCE),check_existing=False)
report={'source':str(SOURCE),'objects':len(building.all_objects),'body_m':[20,14],'roof_ridge_m':8.55,'entry_peak_m':9.1,'storeys':2,'root_location':list(root.location),'root_scale':list(root.scale),'review':'awaiting user','exported_to_UE':False}
(BASE/'Source'/'validation.txt').write_text(json.dumps(report,indent=2),encoding='utf-8')
for name,camera in cameras.items():
    scene.camera=camera;scene.render.filepath=str(PREVIEW/(name+'.png'))
    bpy.ops.render.render(write_still=True)
