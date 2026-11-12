"""Add the approved ground-floor interior to the CURRENT Rudy source, once.

Never loads/regenerates the building, saves maps, or changes exterior materials.
Construction openings remain editable Boolean modifiers. Export uses export_fbx.py.
"""
import bpy, math, random, json, hashlib
from mathutils import Vector, Matrix
from pathlib import Path
random.seed(71)
assert Path(bpy.data.filepath).name == 'RudyPawnshop.blend'
assert bpy.context.mode == 'OBJECT'
assert not bpy.data.collections.get('RUDY_Interior'), 'Interior already present'
building=bpy.data.collections['BLD_RudyPawnshop']
root=bpy.data.objects['RudyPawnshop_ROOT']
interior=bpy.data.collections.new('RUDY_Interior');building.children.link(interior)
cutters=bpy.data.collections.new('RUDY_Construction_Cutters');bpy.context.scene.collection.children.link(cutters)
cutters.hide_render=True
originals={o.name:hashlib.sha256(bytes(str([(tuple(v.co)) for v in o.data.vertices]),'utf8')).hexdigest() for o in building.all_objects if o.type=='MESH'}
def material(name,color,rough=.55,metal=0,trans=0,emission=0):
 m=bpy.data.materials.new(name);m.diffuse_color=(*color,1);m.use_nodes=True
 p=next(n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED');p.inputs['Base Color'].default_value=(*color,1);p.inputs['Roughness'].default_value=rough;p.inputs['Metallic'].default_value=metal
 p.inputs['Transmission Weight'].default_value=trans
 if emission:p.inputs['Emission Color'].default_value=(*color,1);p.inputs['Emission Strength'].default_value=emission
 return m
glass=material('RUDY_INT_Clear_Glass',(.72,.84,.79),.12,0,1)
glass.diffuse_color=(.72,.84,.79,.18)
next(n for n in glass.node_tree.nodes if n.type=='BSDF_PRINCIPLED').inputs['Alpha'].default_value=.18
brass=material('RUDY_INT_Aged_Brass',(.34,.20,.075),.32,.78)
red=material('RUDY_INT_Burgundy',(.23,.035,.045),.86)
plaster=material('RUDY_INT_Warm_Plaster',(.72,.66,.53),.9)
paper=material('RUDY_INT_Paper',(.83,.76,.58),.88)
bulb=material('RUDY_INT_Amber_Light',(1,.55,.16),.28,0,0,5)
wood=bpy.data.materials['RUDY_Oak'];edge=bpy.data.materials['RUDY_Oak_Edge'];dark=bpy.data.materials['RUDY_Dark_Timber'];iron=bpy.data.materials['RUDY_Blackened_Iron'];green=bpy.data.materials['RUDY_Canvas_Olive'];teal=bpy.data.materials['RUDY_Painted_Teal']
class Geo:
 def __init__(self,name):self.name=name;self.v=[];self.f=[];self.mi=[];self.m=[]
 def add(self,vs,fs,mat):
  offset=len(self.v);self.v.extend(vs)
  if mat not in self.m:self.m.append(mat)
  self.f.extend(tuple(offset+i for i in f) for f in fs);self.mi.extend([self.m.index(mat)]*len(fs))
 def box(self,p,s,mat,rot=0):
  c=math.cos(rot);q=math.sin(rot);vs=[]
  for x,y,z in [(-1,-1,-1),(1,-1,-1),(1,1,-1),(-1,1,-1),(-1,-1,1),(1,-1,1),(1,1,1),(-1,1,1)]:
   x*=s[0]/2;y*=s[1]/2;z*=s[2]/2;vs.append((p[0]+x*c-y*q,p[1]+x*q+y*c,p[2]+z))
  self.add(vs,[(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)],mat)
 def rod(self,a,b,r,mat,n=12,r2=None):
  a=Vector(a);b=Vector(b);d=(b-a).normalized();u=d.cross(Vector((0,0,1)))
  if u.length<.1:u=d.cross(Vector((0,1,0)))
  u.normalize();v=d.cross(u);r2=r if r2 is None else r2
  vs=[tuple(p+rr*(math.cos(i*math.tau/n)*u+math.sin(i*math.tau/n)*v)) for p,rr in [(a,r),(b,r2)] for i in range(n)]
  self.add(vs,[tuple(reversed(range(n))),tuple(range(n,2*n))]+[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)],mat)
 def ring(self,p,r,t,mat,vertical=False):
  vs=[];n=20;k=6
  for i in range(n):
   a=i*math.tau/n
   for j in range(k):
    b=j*math.tau/k;x=(r+t*math.cos(b))*math.cos(a);y=(r+t*math.cos(b))*math.sin(a);z=t*math.sin(b)
    vs.append((p[0]+x,p[1]+(z if vertical else y),p[2]+(y if vertical else z)))
  self.add(vs,[(i*k+j,((i+1)%n)*k+j,((i+1)%n)*k+(j+1)%k,i*k+(j+1)%k) for i in range(n) for j in range(k)],mat)
 def finish(self,bevel=.006):
  if self.name in {'RUDY_INT_BackOffice','RUDY_INT_Desk_Details','RUDY_INT_Signs','RUDY_INT_Plants'}:bevel=0
  me=bpy.data.meshes.new(self.name);me.from_pydata(self.v,[],self.f);me.update()
  for m in self.m:me.materials.append(m)
  for p,i in zip(me.polygons,self.mi):p.material_index=i
  o=bpy.data.objects.new(self.name,me);interior.objects.link(o);o.parent=root
  if bevel:
   b=o.modifiers.new('Soft crafted edges','BEVEL');b.width=bevel;b.segments=1
  return o
def cut(name,center,size,targets):
 g=Geo(name);g.box(center,size,dark);o=g.finish(0);interior.objects.unlink(o);cutters.objects.link(o);o.display_type='WIRE';o.hide_render=True;o.hide_set(True)
 for target in targets:
  b=bpy.data.objects[target].modifiers.new(name,'BOOLEAN');b.operation='DIFFERENCE';b.solver='EXACT';b.object=o
 return o
def text(name,body,p,size,mat,rot=(math.pi/2,0,0)):
 cu=bpy.data.curves.new(name,'FONT');cu.body=body;cu.size=size;cu.align_x='CENTER';cu.extrude=.001;cu.resolution_u=3
 o=bpy.data.objects.new(name,cu);interior.objects.link(o);o.parent=root;o.location=p;o.rotation_euler=rot;cu.materials.append(mat);return o
# Hollow only the ground floor and the new stairwell. Outside dimensions remain fixed.
cut('INT_Cut_Room',(0,0,1.82),(9.5,7.5,2.96),['RUDY_01_Ground_Mass'])
cut('INT_Cut_Entrance',(1.38,-3.98,1.48),(1.24,.65,2.44),['RUDY_01_Ground_Mass','RUDY_03_Lower_Brick_Front','RUDY_02_Stone_Base'])
for i,(x,w) in enumerate([(-3.37,2.18),(-.78,2.18),(3.33,2.15)]):
 # Cut each backing panel, retaining all mullions and the perimeter woodwork.
 cut('INT_Cut_Window_'+str(i),(x,-3.90,1.55),(w-.11,.60,1.92),['RUDY_01_Ground_Mass','RUDY_03_Lower_Brick_Front','RUDY_10_Shopfront'])
cut('INT_Cut_Stairwell',(3.92,1.08,4.04),(1.64,5.34,3.12),['RUDY_01_Ground_Mass','RUDY_01_Upper_House','RUDY_02_Stone_Courses'])
# Open the existing door as one intact authored assembly, including its lettering.
hinge=Vector((.785,-4.1,0));transform=Matrix.Translation(hinge) @ Matrix.Rotation(math.radians(-102),4,'Z') @ Matrix.Translation(-hinge)
for name in ['RUDY_12_Shop_Door','RUDY_41_Door_Open']:
 o=bpy.data.objects[name];o.matrix_world=transform @ o.matrix_world
g=Geo('RUDY_INT_Window_Panes')
for x,w in [(-3.37,2.18),(-.78,2.18),(3.33,2.15)]:g.box((x,-4.01,1.55),(w-.12,.012,1.91),glass)
g.finish(0)
# Continuous planked floor with staggered joints; no overlapping coplanar faces.
g=Geo('RUDY_INT_Floor')
for row in range(32):
 y=-3.72+row*.235
 x=-4.74
 while x<4.73:
  length=min(1.15 if x==-4.74 and row%2 else 1.88,4.74-x)
  g.box((x+length/2,y,.354),(length-.008,.227,.028),wood if (row+int(x*4))%3 else edge);x+=length
g.finish(.002)
g=Geo('RUDY_INT_Wall_Finish')
g.box((-4.731,0,1.83),(.022,7.45,2.9),plaster);g.box((0,3.731,1.83),(9.45,.022,2.9),plaster)
g.box((4.731,-2.72,1.83),(.022,2.0,2.9),plaster)
for y in [-3.71,3.71]:
 if y>0:g.box((0,y,.66),(9.4,.055,.58),wood)
g.box((-4.70,0,.66),(.055,7.4,.58),wood)
for z in [.4,.96,3.12]:
 g.box((-4.66,0,z),(.1,7.4,.07),edge);g.box((0,3.66,z),(9.3,.1,.07),edge)
g.finish()
g=Geo('RUDY_INT_Ceiling_Beams')
for y in [-3.2,-.9,1.4,3.45]:g.box((-.8,y,3.19),(7.8,.14,.16),dark)
for x in [-4.55,-1.3,2.8]:g.box((x,0,3.22),(.12,7.4,.12),wood)
g.finish()
# Straight stair: 18 risers, 17.5 cm rise, 27 cm going, 1.45 m wide.
g=Geo('RUDY_INT_Stairs')
for i in range(18):
 top=.36+(i+1)*.175;y=-2.6+i*.27
 g.box((3.92,y,(top+.36)/2),(1.45,.27,top-.36),wood)
 g.box((3.92,y-.012,top-.015),(1.48,.29,.03),edge)
 for x in [3.23,4.61]:
  if i%2==0:g.rod((x,y,top),(x,y,top+.88),.022,brass,8)
for x in [3.23,4.61]:g.rod((x,-2.6,1.415),(x,1.99,4.39),.038,dark)
g.box((3.92,2.88,3.43),(1.48,1.52,.16),wood)
g.finish()
# A closed apartment door terminates the landing; no residential fit-out.
g=Geo('RUDY_INT_Landing_Door');g.box((3.115,2.85,4.54),(.06,1.08,2.04),wood)
for y in [2.29,3.41]:g.box((3.075,y,4.56),(.12,.08,2.16),edge)
g.box((3.075,2.85,5.63),(.12,1.2,.08),edge);g.rod((3.04,2.48,4.48),(2.99,2.48,4.48),.045,brass);g.finish()
# Main counter, glass display and two solid work wings.
g=Geo('RUDY_INT_Counter')
g.box((-.85,1.15,.70),(4.65,.86,.64),wood);g.box((-.85,1.15,.41),(4.8,.96,.1),dark)
for x in [-3.05,-1.95,-.85,.25,1.35]:g.box((x,.7,.73),(.065,.065,.59),edge)
for z in [.46,.98]:g.box((-.85,.69,z),(4.7,.075,.065),edge)
for x in [-2.75,1.05]:g.box((x,1.14,1.41),(.88,1.02,.09),edge)
for y in [.71,1.59]:g.box((-.85,y,1.43),(2.9,.06,.055),edge)
for x in [-2.29,.59]:
 for y in [.73,1.57]:g.box((x,y,1.22),(.045,.045,.39),brass)
g.box((-.85,1.15,1.025),(2.84,.8,.025),red)
g.finish()
g=Geo('RUDY_INT_Counter_Glass');g.box((-.85,.728,1.225),(2.82,.012,.365),glass);g.box((-.85,1.15,1.394),(2.83,.8,.012),glass)
for x in [-2.285,.585]:g.box((x,1.15,1.225),(.012,.79,.365),glass)
g.finish(0)
def watch(g,x,y,z,r=.07):
 g.box((x,y,z+.025),(.15,.15,.05),red);g.rod((x,y,z+.065),(x,y+.026,z+.065),r,brass,16)
 g.rod((x,y-.003,z+.065),(x,y-.006,z+.065),r*.84,paper,16)
 g.rod((x,y-.012,z+.065),(x+.035,y-.012,z+.09),.004,iron,6)
 g.rod((x,y-.012,z+.065),(x-.018,y-.012,z+.1),.004,iron,6)
def valuables(g,x,y,z):
 for i in range(4):watch(g,x+i*.26,y,z)
 for i in range(5):g.ring((x+i*.16,y+.26,z+.025),.045,.008,brass)
 g.box((x+1.02,y+.12,z+.015),(.32,.4,.03),red)
 for i in range(3):
  for j in range(3):g.rod((x+.91+i*.09,y+j*.09,z+.032),(x+.91+i*.09,y+j*.09,z+.04),.032,brass,12)
g=Geo('RUDY_INT_Counter_Valuables');valuables(g,-2.05,.88,1.05);g.finish(.001)
# Freestanding cabinet left of the circulation route.
g=Geo('RUDY_INT_Display_Cabinet')
g.box((-2.8,-1.3,.69),(2.1,.9,.65),wood);g.box((-2.8,-1.3,.42),(2.22,1,.1),dark)
for x in [-3.82,-2.8,-1.78]:g.box((x,-1.77,.73),(.06,.04,.55),edge)
for y in [-1.76,-.84]:g.box((-2.8,y,1.42),(2.2,.06,.06),edge)
for x in [-3.87,-1.73]:g.box((x,-1.3,1.42),(.06,.86,.06),edge)
g.box((-2.8,-1.3,1.035),(2,.8,.035),red)
for x in [-3.8,-1.8]:
 for y in [-1.71,-.89]:g.box((x,y,1.23),(.04,.04,.35),brass)
g.finish()
g=Geo('RUDY_INT_Display_Glass')
for y in [-1.71,-.89]:g.box((-2.8,y,1.23),(1.97,.012,.34),glass)
for x in [-3.8,-1.8]:g.box((x,-1.3,1.23),(.012,.8,.34),glass)
g.box((-2.8,-1.3,1.382),(1.98,.8,.012),glass);g.finish(0)
g=Geo('RUDY_INT_Display_Valuables');valuables(g,-3.58,-1.55,1.06);g.finish(.001)
# Shelves face south; rotate left wall units as complete editable groups.
def shelf(name,x,y,w,angle=0):
 g=Geo(name)
 g.box((0,.22,1.67),(w,.045,2.5),dark)
 for xx in [-w/2,w/2]:g.box((xx,0,1.67),(.075,.5,2.5),edge)
 for z in [.43,.94,1.47,2.0,2.53,2.93]:g.box((0,-.02,z),(w+.13,.56,.055),wood)
 g.box((0,0,2.97),(w+.18,.6,.08),edge)
 o=g.finish();o.location=(x,y,0);o.rotation_euler.z=angle
 return o
def stock(name,x,y,w,angle=0):
 g=Geo(name)
 for level,z in enumerate([.47,.98,1.51,2.04,2.57]):
  for j in range(3):
   xx=-w*.33+j*w*.32;kind=(level+j)%4
   if kind==0:
    for k in range(4):
     h=.23+.025*(k%3);g.box((xx+k*.065-.1,-.06,z+h/2),(.055,.25,h),[red,green,teal,wood][k]);g.box((xx+k*.065-.1,-.191,z+.045),(.04,.008,.015),brass)
   elif kind==1: # camera, lens, viewfinder, silver top
    g.box((xx,-.05,z+.12),(.32,.22,.21),iron);g.box((xx,-.05,z+.235),(.32,.22,.035),brass)
    g.rod((xx,-.16,z+.13),(xx,-.24,z+.13),.075,brass,12);g.rod((xx,-.24,z+.13),(xx,-.25,z+.13),.055,glass,12)
    g.box((xx+.1,-.17,z+.19),(.05,.025,.035),paper)
   elif kind==2: # contemporary vintage radio
    g.box((xx,0,z+.14),(.38,.25,.28),wood);g.box((xx-.065,-.132,z+.14),(.19,.015,.2),dark)
    for k in range(6):g.box((xx-.14+k*.03,-.144,z+.14),(.008,.008,.18),brass)
    g.box((xx+.11,-.14,z+.19),(.09,.01,.04),paper)
    for zz in [.07,.13]:g.rod((xx+.11,-.14,z+zz),(xx+.11,-.16,z+zz),.025,brass,8)
    g.rod((xx+.12,.06,z+.28),(xx+.18,.06,z+.44),.007,iron,6)
   else:
    g.box((xx,0,z+.12),(.35,.3,.24),[teal,wood,red][j]);g.box((xx,-.156,z+.12),(.1,.012,.05),paper)
    g.box((xx,0,z+.23),(.36,.31,.025),edge)
 o=g.finish(.003);o.location=(x,y,0);o.rotation_euler.z=angle
for name,x,y,w,angle in [('BackLeft',-3.65,3.4,1.7,0),('BackMiddle',-1.72,3.4,1.7,0),('LeftA',-4.4,1.8,1.8,math.pi/2),('LeftB',-4.4,-.45,1.8,math.pi/2)]:
 shelf('RUDY_INT_Shelves_'+name,x,y,w,angle);stock('RUDY_INT_Stock_'+name,x,y,w,angle)
# Safe, card drawers, storage boxes and a low working stool.
g=Geo('RUDY_INT_BackOffice')
g.box((.45,3.29,1.02),(1.04,.75,1.3),iron);g.box((.45,2.89,1.04),(.88,.065,1.12),teal)
g.ring((.48,2.84,1.14),.18,.025,brass,True)
for a in [0,math.tau/3,2*math.tau/3]:g.rod((.48,2.82,1.14),(.48+.16*math.cos(a),2.82,1.14+.16*math.sin(a)),.016,brass,8)
g.rod((.15,2.84,1.4),(.15,2.81,1.4),.055,brass,12)
for z in [.65,1.4]:g.box((.86,2.84,z),(.055,.09,.14),brass)
g.box((1.81,3.3,.97),(.95,.71,1.2),wood)
for x in [1.58,2.04]:
 for z in [.55,.82,1.09,1.36]:
  g.box((x,2.925,z),(.42,.045,.24),edge);g.box((x,2.894,z+.035),(.16,.015,.06),paper);g.rod((x-.07,2.86,z-.045),(x+.07,2.86,z-.045),.012,brass,8)
for x in [-2.5,-.8]:
 g.box((x,2.9,.54),(.6,.5,.35),wood);g.box((x,2.64,.57),(.15,.02,.07),paper)
g.rod((-.7,2.25,.78),(-.7,2.25,.88),.25,red,16)
for dx,dy in [(-.15,-.15),(.15,-.15),(-.15,.15),(.15,.15)]:g.rod((-.7+dx*1.25,2.25+dy*1.25,.37),(-.7+dx,2.25+dy,.8),.028,wood,8)
g.finish()
# Register, ledger with visible ruled pages, task lamp and pencil cup.
g=Geo('RUDY_INT_Desk_Details')
g.box((-2.74,1.19,1.52),(.58,.51,.14),iron);g.box((-2.74,1.28,1.72),(.5,.28,.3),teal)
g.box((-2.74,1.44,1.83),(.28,.02,.1),dark)
for i in range(5):
 for j in range(3):g.box((-2.93+i*.095,1.0+j*.08,1.61),(.06,.05,.025),paper)
g.box((1.03,1.12,1.477),(.62,.39,.045),red)
for xx in [.877,1.183]:
 g.box((xx,1.12,1.505),(.29,.36,.018),paper)
 for k in range(8):g.box((xx,1.0+k*.03,1.516),(.23,.002,.001),wood)
g.rod((.88,1.18,1.525),(1.17,1.25,1.525),.008,iron,8)
g.rod((.99,1.52,1.46),(.99,1.52,1.49),.16,brass,16);g.rod((.99,1.52,1.49),(.99,1.52,1.91),.023,brass)
g.rod((.72,1.5,1.91),(1.26,1.5,1.91),.12,green,16)
g.rod((.79,1.48,1.86),(1.19,1.48,1.86),.035,bulb,12)
g.rod((-2.28,1.5,1.46),(-2.28,1.5,1.64),.065,brass,12)
for j in range(5):g.rod((-2.32+j*.02,1.5,1.6),(-2.33+j*.026,1.49,1.79),.006,[red,wood,teal][j%3],6)
g.finish(.002)
# Signage and community notices.
g=Geo('RUDY_INT_Signs')
g.box((.65,3.64,2.45),(2.9,.08,.91),dark)
for z in [2.03,2.87]:g.box((.65,3.58,z),(2.9,.05,.035),brass)
for x in [-.78,2.08]:g.box((x,3.58,2.45),(.035,.05,.85),brass)
g.box((3.12,.1,2.02),(.065,1.12,1.15),wood)
for j in range(5):g.box((3.078,-.23+(j%2)*.43,1.7+(j//2)*.3),(.012,.33,.24),paper)
g.finish()
text('RUDY_INT_Sign_Text',"RUDY'S PAWN",(.65,3.575,2.45),.28,brass)
text('RUDY_INT_Trade_Text','BUY  /  SELL  /  TRADE',(.65,3.572,2.18),.105,paper)
# Rug: layered borders separated vertically, woven diamond motifs.
g=Geo('RUDY_INT_Rug');g.box((1.3,-1.38,.376),(1.6,3.25,.012),red)
for x in [.55,2.05]:g.box((x,-1.38,.384),(.065,3.12,.003),edge)
for y in [-2.94,.18]:g.box((1.3,y,.384),(1.5,.065,.003),edge)
for y in [-2.6,-1.85,-1.1,-.35]:
 g.box((1.3,y,.385),(.21,.21,.003),edge,math.pi/4);g.box((1.3,y,.388),(.11,.11,.002),red,math.pi/4)
g.finish(0)
# Pendant housings and emissive bulbs, no level light actors.
g=Geo('RUDY_INT_Pendants')
for x,y in [(-2.65,-1.25),(1.25,-1.5),(-.8,1.0)]:
 g.rod((x,y,3.24),(x,y,2.91),.012,brass,8)
 g.rod((x,y,2.75),(x,y,2.94),.28,brass,20,r2=.08)
 g.rod((x,y,2.738),(x,y,2.753),.245,paper,20)
 g.rod((x,y,2.68),(x,y,2.74),.065,bulb,12,r2=.09)
 g.ring((x,y,2.75),.278,.012,brass)
g.finish(.002)
# Stylized potted plants with individual low-poly leaves.
g=Geo('RUDY_INT_Plants')
for x,y,z,size in [(-4.15,-3.15,.37,1),(2.48,3.28,1.58,.48),(-3.6,3.39,3.015,.25)]:
 g.rod((x,y,z),(x,y,z+.32*size),.15*size,bpy.data.materials['RUDY_Terracotta_Pots'],12,r2=.22*size)
 g.rod((x,y,z+.32*size),(x,y,z+.33*size),.19*size,dark,12)
 for j in range(12):
  a=j*2.4;h=(.45+(j%4)*.12)*size;end=Vector((x+math.cos(a)*.27*size,y+math.sin(a)*.27*size,z+h))
  g.rod((x,y,z+.32*size),end,.008*size,green,6)
  side=Vector((-math.sin(a)*.1*size,math.cos(a)*.1*size,0));tip=end+Vector((math.cos(a)*.2*size,math.sin(a)*.2*size,.09*size));mid=(end+tip)/2
  g.add([tuple(end),tuple(mid+side),tuple(tip),tuple(mid-side),tuple(mid+Vector((0,0,.035*size)))],[(0,1,4),(1,2,4),(2,3,4),(3,0,4),(3,2,1,0)],bpy.data.materials['RUDY_Foliage_'+str(j%3)])
g.finish(.001)
bpy.context.view_layer.update()
# Store compact provenance and UE-compatible values, not generated screenshots.
source=Path(bpy.data.filepath).parent
manifest={}
for m in [glass,brass,red,plaster,paper,bulb]:
 p=next(n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED');manifest[m.name]={'color':list(m.diffuse_color),'roughness':p.inputs['Roughness'].default_value,'metallic':p.inputs['Metallic'].default_value,'transmission':p.inputs['Transmission Weight'].default_value,'emission_strength':p.inputs['Emission Strength'].default_value}
manifest['RUDY_INT_Clear_Glass'].update({'opacity':.12,'unreal_blend_mode':'Translucent','unreal_lighting_mode':'Surface ForwardShading','two_sided':True,'refraction':1.0})
(source/'interior_materials.json').write_text(json.dumps(manifest,indent=2))
root['interior_version']='2026-11-12';root['interior_floor_z']=.368;root['stair_clear_width']=1.38
result={'added_objects':len(interior.objects),'source_meshes_preserved':all(hashlib.sha256(bytes(str([tuple(v.co) for v in bpy.data.objects[n].data.vertices]),'utf8')).hexdigest()==h for n,h in originals.items()),'cutters':len(cutters.objects)}

# Separate hinged entrance door. Its FBX uses the closed, hinge-local frame.
parts=bpy.data.collections.new('RUDY_Movable_Parts');bpy.context.scene.collection.children.link(parts)
door_root=bpy.data.objects.new('RUDY_Door_Entrance_ROOT',None);parts.objects.link(door_root)
new_hinge=Vector((.665,-4.09,.365))
door_root.location=new_hinge;door_root.rotation_euler.z=math.radians(-102)
bpy.context.view_layer.update()
for name in ['RUDY_12_Shop_Door','RUDY_41_Door_Open']:
 o=bpy.data.objects[name]
 closed=transform.inverted() @ o.matrix_world
 o.matrix_world=closed
 if o.type=='MESH':
  inv=closed.inverted()
  for v in o.data.vertices:
   p=closed @ v.co
   if p.z<.365:p.z=.365;v.co=inv @ p
 world=Matrix.Translation(new_hinge) @ Matrix.Rotation(math.radians(-102),4,'Z') @ Matrix.Translation(-new_hinge) @ closed
 for c in list(o.users_collection):c.objects.unlink(o)
 parts.objects.link(o);o.parent=door_root;o.matrix_world=world
# The leaf moves independently; a fixed jamb and lintel stay with the building.
g=Geo('RUDY_INT_Entrance_Frame')
for x in [.612,2.148]:g.box((x,-3.94,1.50),(.09,.32,2.3),edge)
g.box((1.38,-3.94,2.69),(1.61,.32,.09),edge);g.finish()
opening=bpy.data.objects['INT_Cut_Entrance']
for v in opening.data.vertices:v.co.x=1.38+(v.co.x-1.38)*1.43/1.24
bpy.context.view_layer.update()
config={'model_id':'RudyPawnshop','source_blend':'SourceAssets/Blender/Buildings/RudyPawnshop/Source/RudyPawnshop.blend','unreal_asset':'/Game/Art/Models/Buildings/RudyPawnshop/SM_RudyPawnshop','unreal_materials':'/Game/Art/Models/Buildings/RudyPawnshop/Materials','unreal_parts':'/Game/Art/Models/Buildings/RudyPawnshop/Parts','parts':[{'root':door_root.name,'fbx':'SM_RudyPawnshop_Door_Entrance.fbx','unreal_asset':'/Game/Art/Models/Buildings/RudyPawnshop/Parts/SM_RudyPawnshop_Door_Entrance','pivot_m':list(new_hinge),'ue_relative_location_cm':[66.5,409,36.5],'closed_ue_yaw':0,'source_preview_open_degrees':-102}],'status':'Source and FBX prepared; import is user-managed'}
config.update({'material_manifest':'interior_materials.json','use_complex_collision':True,'remove_generated_simple_collision':True})
(source/'model_config.json').write_text(json.dumps(config,indent=2))
