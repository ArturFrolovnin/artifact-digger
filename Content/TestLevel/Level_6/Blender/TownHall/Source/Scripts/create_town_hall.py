"""Independent Town Hall first-pass model. Run in a fresh/background Blender process."""
import bpy, math, random, json
from pathlib import Path
from mathutils import Vector

BASE = Path(__file__).resolve().parents[2]
random.seed(24)
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.name = 'TownHall_Blockout'
scene.unit_settings.system = 'METRIC'
scene.unit_settings.scale_length = 1.0
main = bpy.data.collections.new('BLD_TownHall')
scene.collection.children.link(main)
root = bpy.data.objects.new('TownHall_ROOT', None)
main.objects.link(root)
root['body_dimensions_m'] = '16 x 12; two floors; ridge 9.5'
root['status'] = 'First review / dimensions not locked / no UE export'
groups = {}
for name in ['Walls','Roof','Windows','Entrance','Columns_Trim','Signage','Flag','Props']:
    c = bpy.data.collections.new(name)
    main.children.link(c)
    groups[name] = c
pres = bpy.data.collections.new('Presentation_NOT_EXPORT')
scene.collection.children.link(pres)

def mat(name, color, rough=.75, metal=0):
    m=bpy.data.materials.new('TH_'+name); m.diffuse_color=(*color,1); m.use_nodes=True
    p=m.node_tree.nodes.get('Principled BSDF'); p.inputs['Base Color'].default_value=(*color,1)
    p.inputs['Roughness'].default_value=rough; p.inputs['Metallic'].default_value=metal
    return m
plaster=mat('Warm_Lime_Plaster',(.68,.55,.37))
stone=mat('Limestone',(.78,.67,.48))
stone2=mat('Limestone_Shadow',(.52,.43,.30))
roofmat=mat('Slate',(.055,.073,.095))
slates=[mat('Slate_Variant_'+str(i),(.057+i*.005,.071+i*.006,.090+i*.007)) for i in range(5)]
wood=mat('Oak',(.19,.085,.035)); woodlight=mat('Oak_Panels',(.27,.13,.057))
frame=mat('Window_Painted_Wood',(.17,.20,.17))
glass=mat('Window_Blue_Grey',(.055,.115,.15),.28,.18)
dark=mat('Recess_Shadow',(.021,.029,.030))
iron=mat('Iron',(.055,.064,.061),.48,.55)
gold=mat('Old_Brass',(.57,.36,.12),.43,.5)
green=[mat('Leaves_'+str(i),c) for i,c in enumerate([(.13,.23,.055),(.23,.34,.075),(.085,.18,.045)])]
flowers=[mat('Flowers_'+str(i),c) for i,c in enumerate([(.80,.49,.12),(.71,.20,.12),(.81,.72,.43)])]
blue=mat('Civic_Blue',(.045,.12,.23))
ground=mat('Presentation_Sand',(.34,.32,.27))

def link(o, name, material, group):
    o.name='TH_'+name
    for c in list(o.users_collection): c.objects.unlink(o)
    (pres if group=='Presentation' else groups[group]).objects.link(o)
    if group!='Presentation': o.parent=root
    if material: o.data.materials.append(material)
    return o
def bevel(o,w=.025):
    if w:
        m=o.modifiers.new('Soft stone edges','BEVEL'); m.width=w; m.segments=3
        n=o.modifiers.new('Weighted normals','WEIGHTED_NORMAL')
    return o
def box(name,loc,size,material,group='Columns_Trim',b=.025):
    bpy.ops.mesh.primitive_cube_add(size=1,location=loc)
    o=link(bpy.context.object,name,material,group)
    o.dimensions=size; bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    return bevel(o,b)
def mesh(name,verts,faces,material,group,b=0):
    m=bpy.data.meshes.new('TH_'+name); m.from_pydata(verts,[],faces); m.update()
    o=bpy.data.objects.new('TH_'+name,m); groups[group].objects.link(o); o.parent=root
    m.materials.append(material); return bevel(o,b)
def rod(name,a,b,r,material,group='Columns_Trim',r2=None):
    d=Vector(b)-Vector(a)
    bpy.ops.mesh.primitive_cone_add(vertices=24,radius1=r,radius2=r if r2 is None else r2,depth=d.length,location=(Vector(a)+Vector(b))/2)
    o=link(bpy.context.object,name,material,group); o.rotation_euler=d.to_track_quat('Z','Y').to_euler()
    for p in o.data.polygons:p.use_smooth=True
    return bevel(o,.008)
def ball(name,loc,size,material,group='Props'):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=12,ring_count=8,radius=1,location=loc)
    o=link(bpy.context.object,name,material,group); o.scale=size
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    for p in o.data.polygons:p.use_smooth=True
    return o
def beam(name,a,b,width,depth,material,group='Columns_Trim'):
    d=Vector(b)-Vector(a); o=box(name,(Vector(a)+Vector(b))/2,(width,depth,d.length),material,group,.015)
    o.rotation_euler=d.to_track_quat('Z','Y').to_euler(); return o
def coord(face,u,v,z):
    return {'Front':(u,-6-v,z),'Back':(-u,6+v,z),'Right':(8+v,u,z),'Left':(-8-v,-u,z)}[face]
def fb(face,name,u,v,z,w,d,h,material,group='Columns_Trim',b=.018):
    o=box(face+'_'+name,coord(face,u,v,z),(w,d,h),material,group,b)
    o.rotation_euler.z={'Front':0,'Right':math.pi/2,'Back':math.pi,'Left':-math.pi/2}[face]
    return o

# Real window apertures, built as wall strips; no imported building geometry.
for face,width,positions in [('Front',16,[-5.5,-3,3,5.5]),('Back',16,[-5.5,-3,3,5.5]),('Right',12,[-3.8,0,3.8]),('Left',12,[-3.8,0,3.8])]:
    openings=[(u-.56,u+.56,z,z+2) for u in positions for z in (1.2,4.45)]
    if face in ('Front','Back'):openings.append((-1.0,1.0,.6,3.3))
    xs=sorted(set([-width/2,width/2]+[p for op in openings for p in op[:2]]))
    for i,(x1,x2) in enumerate(zip(xs,xs[1:])):
        holes=sorted([(a,b) for l,r,a,b in openings if l<(x1+x2)/2<r]); last=.6
        for j,(lo,hi) in enumerate(holes+[(7.0,7.0)]):
            if lo>last:fb(face,'Wall_%s_%s'%(i,j),(x1+x2)/2,-.18,(last+lo)/2,x2-x1,.36,lo-last,plaster,'Walls',.008)
            last=hi
    for z,h,v,d,m in [(.30,.60,.01,.43,stone2),(.64,.14,.06,.49,stone),(3.85,.14,.035,.43,stone),(6.94,.20,.13,.65,stone),(7.10,.16,.21,.80,stone)]:
        fb(face,'Continuous_course',0,v,z,width+.08,d,h,m)
    for u in [-width/2+.19,width/2-.19]:
        for i in range(13):
            fb(face,'Corner_quoin',u,.055,.92+i*.46,.48 if i%2 else .64,.17,.41,stone)
    for u in positions:
        for z in (1.2,4.45):
            label='Window_%s_%s'%(u,z)
            fb(face,label+'_shadow',u,-.28,z+1,1.12,.035,2,dark,'Windows',0)
            fb(face,label+'_glass',u,-.12,z+1,1.02,.035,1.90,glass,'Windows',.006)
            for x in (-.53,.53):fb(face,label+'_jamb',u+x,-.035,z+1,.09,.12,2,frame,'Windows',.01)
            for zz in (.045,1.96):fb(face,label+'_frame',u,-.03,z+zz,1.12,.13,.08,frame,'Windows',.01)
            fb(face,label+'_mullion',u,-.005,z+1,.05,.12,1.9,frame,'Windows',.007)
            for zz in (.69,1.35):fb(face,label+'_crossbar',u,-.005,z+zz,1.06,.12,.045,frame,'Windows',.007)
            for x in (-.67,.67):
                fb(face,label+'_stone_jamb',u+x,.075,z+1,.19,.24,2.12,stone)
            fb(face,label+'_lintel',u,.075,z+2.09,1.52,.27,.20,stone)
            fb(face,label+'_keystone',u,.135,z+2.12,.23,.30,.31,stone)
            fb(face,label+'_sill',u,.16,z-.045,1.60,.46,.16,stone)
            if z>4 and (face=='Front' or (face in ('Right','Left') and u==0)):
                fb(face,label+'_flowerbox',u,.39,z-.20,1.35,.40,.28,wood,'Props')
                for j in range(7):
                    p=coord(face,u-.55+j*.18,.43,z+.015)
                    ball('Window_leaves',p,(.21,.19,.17),green[j%3])
                    p=coord(face,u-.53+j*.18,.46,z+.16+(j%2)*.025)
                    ball('Window_blossoms',p,(.065,.065,.06),flowers[j%3])

# Enclosed shell roof: hipped, continuous on all four elevations.
verts=[(-8.48,-6.48,7.22),(8.48,-6.48,7.22),(8.48,6.48,7.22),(-8.48,6.48,7.22),(-2.5,0,9.5),(2.5,0,9.5)]
o=mesh('Hipped_Roof',verts,[(0,1,5,4),(1,2,5),(2,3,4,5),(3,0,4),(3,2,1,0)],roofmat,'Roof')
# Quiet slate courses, one editable mesh per slope, no production textures.
for side in range(4):
    vv=[]; ff=[]
    for row in range(18):
        t0=row/18; t1=(row+.94)/18
        if side<2:
            def point(t,s):
                half=8.48+(2.5-8.48)*t
                return (-half+2*half*s,(-1 if side==0 else 1)*6.48*(1-t),7.235+2.28*t)
            span=2*(8.48+(2.5-8.48)*(t0+t1)/2)
        else:
            def point(t,s):
                half=6.48*(1-t)
                return ((1 if side==2 else -1)*(8.48-5.98*t),-half+2*half*s,7.235+2.28*t)
            span=12.96*(1-(t0+t1)/2)
        count=max(1,round(span/.63))
        for j in range(count):
            s0=(j+.015)/count;s1=(j+.985)/count;k=len(vv)
            vv += [point(t0,s0),point(t0,s1),point(t1,s1),point(t1,s0)]
            ff.append((k,k+1,k+2,k+3))
    o=mesh('Slate_courses_'+str(side),vv,ff,slates[0],'Roof')
    for m in slates[1:]:o.data.materials.append(m)
    for p in o.data.polygons:p.material_index=random.randrange(5)
    sol=o.modifiers.new('Slate thickness','SOLIDIFY');sol.thickness=.018
for a,b in [(verts[0],verts[4]),(verts[1],verts[5]),(verts[2],verts[5]),(verts[3],verts[4]),(verts[4],verts[5])]:
    beam('Roof_hip_cap',Vector(a)+Vector((0,0,.04)),Vector(b)+Vector((0,0,.04)),.15,.15,roofmat,'Roof')
for x in (-6.4,6.4):
    box('Chimney',(x,2.3,8.58),(.58,.62,1.45),stone,'Roof')
    box('Chimney_cap',(x,2.3,9.30),(.78,.80,.17),stone,'Roof')
    box('Chimney_dark_top',(x,2.3,9.39),(.43,.44,.025),dark,'Roof',0)

def pediment(name,half,yfront,yback,zbase,zpeak,material,group):
    vs=[(-half,yfront,zbase),(half,yfront,zbase),(0,yfront,zpeak),(-half,yback,zbase),(half,yback,zbase),(0,yback,zpeak)]
    return mesh(name,vs,[(0,2,1),(3,4,5),(0,1,4,3),(1,2,5,4),(2,0,3,5)],material,group,.018)
# Small raised central heraldic bay, not a monumental tower.
box('Central_Upper_Bay',(0,-6.13,5.8),(3.05,.42,2.6),plaster,'Walls')
for x in (-1.46,1.46):
    box('Upper_Bay_Pilaster',(x,-6.40,5.82),(.20,.17,2.68),stone)
    box('Upper_Bay_Capital',(x,-6.43,7.10),(.37,.25,.20),stone)
pediment('Central_Gable',1.83,-6.50,-5.65,7.16,8.42,stone,'Columns_Trim')
pediment('Central_Gable_Inset',1.48,-6.535,-6.49,7.27,8.18,plaster,'Columns_Trim')
for x in (-1.94,1.94):beam('Central_Raking_Cornice',(x,-6.54,7.13),(0,-6.54,8.48),.16,.23,stone)
box('Central_Gable_Base',(0,-6.51,7.16),(3.94,.35,.17),stone)
# Shield and modest town emblem: gate, three battlements, river.
shield=[(-.51,6.78),(.51,6.78),(.48,5.92),(0,5.58),(-.48,5.92)]
def plaque(name,poly,y,depth,material,group='Signage'):
    n=len(poly);vs=[(x,y,z) for x,z in poly]+[(x,y+depth,z) for x,z in poly]
    fs=[tuple(reversed(range(n))),tuple(range(n,2*n))]+[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
    return mesh(name,vs,fs,material,group,.012)
plaque('Civic_Shield_Stone',[(x*1.14,(z-6.18)*1.12+6.18) for x,z in shield],-6.44,.11,stone)
plaque('Civic_Shield',shield,-6.515,.06,blue)
box('Crest_Gate',(0,-6.56,6.22),(.49,.045,.36),gold,'Signage',.008)
for x in (-.19,0,.19):box('Crest_Battlement',(x,-6.56,6.45),(.11,.045,.12),gold,'Signage',.005)
box('Crest_Door',(0,-6.59,6.15),(.12,.02,.21),blue,'Signage',.006)
for z in (5.96,5.86):box('Crest_River',(0,-6.56,z),(.41,.04,.035),gold,'Signage',.005)

# Entrance: four low risers, recessed oak double door, two simple columns.
for i in range(4):
    length=2.80-i*.30
    box('Entry_Step_%02d'%i,(0,-6-length/2,.075+i*.15),(4.25,length,.15),stone,'Entrance',.022)
for face in ('Front','Back'):
    fb(face,'Door_Shadow',0,-.21,1.95,2,.04,2.7,dark,'Entrance')
    fb(face,'Oak_Double_Door',0,-.12,1.95,1.91,.12,2.68,wood,'Entrance')
    for u in (-.47,.47):
        for z in (1.05,1.94,2.80):
            fb(face,'Raised_Door_Panel',u,-.027,z,.68,.06,.65,woodlight,'Entrance',.025)
        fb(face,'Door_Handle',u*.25,.028,1.72,.035,.075,.24,gold,'Entrance',.009)
    for u in (-1.12,1.12):fb(face,'Door_Stone_Jamb',u,.07,1.95,.23,.29,2.83,stone,'Entrance')
    fb(face,'Door_Lintel',0,.07,3.36,2.5,.30,.23,stone,'Entrance')
box('Rear_Step',(0,6.45,.15),(2.65,.9,.30),stone,'Entrance')
box('Rear_Upper_Step',(0,6.25,.45),(2.4,.5,.30),stone,'Entrance')
for x in (-1.63,1.63):
    box('Column_Plinth',(x,-7.78,.78),(.60,.60,.36),stone,'Entrance')
    rod('Porch_Column',(x,-7.78,.96),(x,-7.78,3.48),.20,stone,'Entrance',.17)
    rod('Column_Base',(x,-7.78,.94),(x,-7.78,1.06),.25,stone,'Entrance')
    box('Column_Capital',(x,-7.78,3.48),(.54,.54,.20),stone,'Entrance')
box('Porch_Entablature',(0,-7.01,3.72),(4.14,2.30,.38),stone,'Entrance')
box('Porch_Frieze_Front',(0,-8.18,3.73),(3.94,.12,.29),stone,'Entrance')
pediment('Porch_Pediment',2.17,-8.24,-5.92,3.96,5.04,stone,'Entrance')
pediment('Porch_Pediment_Inset',1.80,-8.27,-8.24,4.06,4.86,plaster,'Entrance')
for x in (-2.22,2.22):
    beam('Porch_Raking_Trim',(x,-8.29,3.93),(0,-8.29,5.10),.13,.18,stone,'Entrance')
    mesh('Porch_Slate',[(x,-8.30,4.01),(0,-8.30,5.13),(0,-5.84,5.13),(x,-5.84,4.01)],[(0,1,2,3)],roofmat,'Roof')
box('Porch_Cornice',(0,-8.25,3.94),(4.5,.26,.13),stone,'Entrance')
font=bpy.data.curves.new('TH_TownHall_Lettering','FONT');font.body='TOWN HALL';font.align_x='CENTER';font.align_y='CENTER';font.size=.29;font.space_character=1.12;font.extrude=.006;font.bevel_depth=.001
o=bpy.data.objects.new('TH_TOWN_HALL',font);groups['Signage'].objects.link(o);o.parent=root;o.location=(0,-8.251,3.73);o.rotation_euler=(math.pi/2,0,0);font.materials.append(wood)
for x in (-2.0,2.0):
    for y,z in [(-8.59,.72),(-7.98,1.02)]:rod('Entry_Rail_Post',(x,y,z-.42),(x,y,z+.45),.025,iron,'Entrance')
    rod('Entry_Handrail',(x,-8.62,1.14),(x,-7.95,1.48),.031,iron,'Entrance')
# Lanterns attached beside the door, warm opaque fill rather than an interior.
lamp=mat('Lantern_Warm',(.95,.60,.24))
for x in (-1.50,1.50):
    box('Lantern_Bracket',(x,-6.51,2.66),(.06,.48,.07),iron,'Props')
    box('Lantern_Glass',(x,-6.76,2.84),(.21,.20,.36),lamp,'Props',.015)
    for z in (2.62,3.06):box('Lantern_Cap',(x,-6.76,z),(.30,.29,.08),iron,'Props')
    for dx in (-.115,.115):rod('Lantern_Frame',(x+dx,-6.865,2.65),(x+dx,-6.865,3.03),.012,iron,'Props')

# Restrained decoration: two low beds and an entrance-side civic flag.
for x in (-4.80,4.80):
    box('Facade_Planter',(x,-6.85,.24),(3.52,.95,.48),stone,'Props',.045)
    box('Planter_Soil',(x,-6.85,.49),(3.30,.75,.055),dark,'Props',.02)
    for i in range(12):
        xx=x+random.uniform(-1.42,1.42); yy=-6.85+random.uniform(-.24,.24)
        ball('Low_Shrub',(xx,yy,.68+random.uniform(0,.10)),(.28,.26,.30),green[i%3])
        if i%2==0:ball('Bed_Flower',(xx,yy,.96),(.08,.08,.07),flowers[i%3])
for x in (-2.64,2.64):
    box('Entry_Pot',(x,-8.0,.29),(.58,.58,.58),stone,'Props',.05)
    ball('Entry_Topiary',(x,-8.0,.94),(.37,.36,.63),green[0])
px,py=6.7,-7.7
box('Flag_Base',(px,py,.18),(.54,.54,.36),stone,'Flag')
rod('Flagpole',(px,py,.32),(px,py,7.20),.045,iron,'Flag',.028)
ball('Flag_Finial',(px,py,7.25),(.09,.09,.09),gold,'Flag')
rod('Flag_Crossbar',(px,py,6.98),(px+1.15,py,6.98),.025,gold,'Flag')
def flagpoint(u,v):return (px+.05+u*1.05,py+.09*math.sin(u*8+v*3)*u,6.94-v*1.85)
vs=[flagpoint(i/16,j/20) for j in range(21) for i in range(17)]
fs=[]
for j in range(20):
    for i in range(16):k=j*17+i;fs.append((k,k+1,k+18,k+17))
o=mesh('City_Flag',vs,fs,blue,'Flag');sol=o.modifiers.new('Cloth_thickness','SOLIDIFY');sol.thickness=.009
for p in o.data.polygons:p.use_smooth=True
for u in (.045,.96):
    for j in range(20):rod('Flag_Gold_Edge',Vector(flagpoint(u,j/20))+Vector((0,-.015,0)),Vector(flagpoint(u,(j+1)/20))+Vector((0,-.015,0)),.018,gold,'Flag')
# Small gold gate symbol carried on the banner.
for u,w,z,h in [(.5,.42,6.10,.34),(.34,.09,6.35,.16),(.5,.09,6.35,.16),(.66,.09,6.35,.16)]:
    box('Flag_Gate_Emblem',(px+.05+u*1.05,py-.13,z),(w,.015,h),gold,'Flag',.004)

# Separate presentation rig, excluded from building bounds and root.
box('Ground',(0,0,-.16),(200,200,.30),ground,'Presentation',.0)
world=bpy.data.worlds.new('TH_Studio_World');scene.world=world;world.use_nodes=True
world.node_tree.nodes['Background'].inputs[0].default_value=(.60,.69,.80,1)
world.node_tree.nodes['Background'].inputs[1].default_value=.40
def area(name,loc,power,size,color):
    d=bpy.data.lights.new(name,'AREA');d.energy=power;d.shape='DISK';d.size=size;d.color=color
    o=bpy.data.objects.new(name,d);pres.objects.link(o);o.location=loc;o.rotation_euler=(Vector((0,0,3))-o.location).to_track_quat('-Z','Y').to_euler()
area('TH_Key',(-12,-16,23),2500,11,(1,.85,.65))
area('TH_Fill',(13,-3,16),1700,10,(.72,.84,1))
area('TH_Back',(-5,13,18),2000,9,(1,.91,.75))
d=bpy.data.lights.new('TH_Sun','SUN');d.energy=2;d.angle=math.radians(18)
o=bpy.data.objects.new('TH_Sun',d);pres.objects.link(o);o.rotation_euler=(math.radians(25),math.radians(-25),math.radians(-30))
views=[('Perspective',(23,-32,19),(0,-.7,4.1),27),('Front',(0,-36,4.65),(0,0,4.65),21),('Side',(35,0,4.65),(0,0,4.65),20),('Back',(0,36,4.65),(0,0,4.65),21),('Top',(0,0,40),(0,0,0),22)]
for name,loc,target,scale in views:
    d=bpy.data.cameras.new('TH_'+name);d.type='ORTHO';d.ortho_scale=scale;d.lens=45
    o=bpy.data.objects.new('TH_Camera_'+name,d);pres.objects.link(o);o.location=loc;o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler()
scene.render.engine='CYCLES';scene.cycles.samples=32;scene.cycles.use_denoising=True
scene.render.resolution_x=1400;scene.render.resolution_y=1100;scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG'
scene.view_settings.view_transform='AgX'
scene.camera=bpy.data.objects['TH_Camera_Perspective']
for obj in bpy.context.selected_objects:obj.select_set(False)
root.select_set(True);bpy.context.view_layer.objects.active=root
bpy.context.view_layer.update()
from mathutils import Vector
pts=[o.matrix_world@Vector(v) for o in main.all_objects if o.type=='MESH' for v in o.bound_box]
report={'body_m':[16,12], 'ridge_m':9.5,'floors':2,'root_location':list(root.location),'root_scale':list(root.scale),'objects':len(main.all_objects),'mesh_objects':sum(o.type=='MESH' for o in main.all_objects),'bounds_min':[min(v[i] for v in pts) for i in range(3)],'bounds_max':[max(v[i] for v in pts) for i in range(3)],'groups':list(groups),'external_geometry_reused':False,'exported_to_UE':False}
(BASE/'Source'/'validation.txt').write_text(json.dumps(report,indent=2),encoding='utf-8')
bpy.ops.wm.save_as_mainfile(filepath=str(BASE/'Source'/'TownHall_Blockout.blend'))
for name,*_ in views:
    scene.camera=bpy.data.objects['TH_Camera_'+name]
    scene.render.filepath=str(BASE/'Previews'/('TownHall_'+name+'.png'))
    bpy.ops.render.render(write_still=True)
print('TOWNHALL_COMPLETE',json.dumps(report))
