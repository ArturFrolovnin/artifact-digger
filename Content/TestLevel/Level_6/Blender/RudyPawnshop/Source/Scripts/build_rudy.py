"""Rudy's house/pawnshop: editable exterior preview, metres, no UE export."""
import bpy, bmesh, math, random, json
from pathlib import Path
from mathutils import Vector
assert bpy.context.mode=='OBJECT'
assert not bpy.data.collections.get('BLD_RudyPawnshop'), 'Existing Rudy model: inspect rather than duplicate'
scene=bpy.data.scenes.new('Rudy_Pawnshop_Preview')
bpy.context.window.scene=scene
scene.unit_settings.system='METRIC'; scene.unit_settings.scale_length=1.0
coll=bpy.data.collections.new('BLD_RudyPawnshop'); scene.collection.children.link(coll)
root=bpy.data.objects.new('RudyPawnshop_ROOT',None); coll.objects.link(root)
root.empty_display_type='PLAIN_AXES'; root.empty_display_size=.7
root['purpose']='Exterior city blockout; two storeys and attic; preview before UE approval'
root['target_actor']='BO_Pawnshop'
root['body_footprint_m']=[10,8]
root['source']='Buildings/StyleGuide.md; Buildings/Dimensions.md; Characters/RudyDexon.md; supplied references'
materials=[]
def mat(name,c,rough=.75,metal=0):
    m=bpy.data.materials.new('RUDY_'+name); m.diffuse_color=(*c,1); m.use_nodes=True
    p=next(n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED')
    p.inputs['Base Color'].default_value=(*c,1); p.inputs['Roughness'].default_value=rough; p.inputs['Metallic'].default_value=metal
    materials.append(m); return len(materials)-1
PLASTER=mat('Aged_Ochre_Plaster',(.58,.51,.35))
LIGHT=mat('Limestone',(.76,.65,.46))
MORTAR=mat('Mortar',(.31,.27,.19))
BRICKS=[mat('Brick_'+str(i),c) for i,c in enumerate([(.53,.23,.10),(.62,.29,.14),(.46,.185,.08),(.58,.26,.12)])]
WOOD=mat('Oak',(.25,.13,.060)); WOODL=mat('Oak_Edge',(.40,.24,.115)); WOODD=mat('Dark_Timber',(.115,.075,.042))
SLATES=[mat('Slate_'+str(i),c) for i,c in enumerate([(.085,.115,.16),(.115,.15,.20),(.145,.18,.22)])]
METAL=mat('Blackened_Iron',(.07,.085,.08),.55,.4)
GOLD=mat('Painted_Gold',(.83,.52,.17),.55,.15)
GLASS=mat('Upper_Window_Blue',(.14,.25,.30),.38,.12)
AMBER=mat('Shop_Glass_Amber',(.27,.16,.065),.48)
CREAM=mat('Canvas_Cream',(.81,.63,.38)); RED=mat('Canvas_Russet',(.54,.20,.12)); GREEN=mat('Canvas_Olive',(.22,.30,.13))
LEAVES=[mat('Foliage_'+str(i),c) for i,c in enumerate([(.18,.29,.07),(.29,.39,.10),(.39,.43,.09)])]
POT=mat('Terracotta_Pots',(.40,.18,.075)); BLUE=mat('Painted_Teal',(.10,.23,.24)); GLOW=mat('Warm_Lantern',(.98,.64,.22))
RUG=mat('Terrace_Rug',(.42,.12,.065)); PATCH=mat('Plaster_Patch',(.66,.59,.44))
groups={}
def group(n):return groups.setdefault(n,[[],[],[]])
def box(n,c,s,m,mp=None):
    vv,ff,mm=group(n); off=len(vv); x,y,z=c; a,b,d=[t/2 for t in s]
    pts=[(x-a,y-b,z-d),(x+a,y-b,z-d),(x+a,y+b,z-d),(x-a,y+b,z-d),(x-a,y-b,z+d),(x+a,y-b,z+d),(x+a,y+b,z+d),(x-a,y+b,z+d)]
    vv.extend([mp(*p) for p in pts] if mp else pts)
    ff.extend(tuple(off+i for i in f) for f in [(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)]); mm.extend([m]*6)
def face(n,pts,m):
    vv,ff,mm=group(n); off=len(vv); vv.extend(pts); ff.append(tuple(range(off,off+len(pts)))); mm.append(m)
def rod(n,a,b,r,m,sides=8,r2=None):
    vv,ff,mm=group(n); off=len(vv); a,b=Vector(a),Vector(b); axis=(b-a).normalized()
    u=axis.cross(Vector((0,0,1)) if abs(axis.z)<.95 else Vector((1,0,0))).normalized(); v=axis.cross(u)
    for p,rr in [(a,r),(b,r if r2 is None else r2)]:
        vv.extend(tuple(p+rr*(math.cos(i*math.tau/sides)*u+math.sin(i*math.tau/sides)*v)) for i in range(sides))
    ff.extend([tuple(off+i for i in reversed(range(sides))),tuple(off+sides+i for i in range(sides))]); mm.extend([m]*2)
    for i in range(sides):
        j=(i+1)%sides; ff.append((off+i,off+j,off+sides+j,off+sides+i)); mm.append(m)
def ring(n,c,r,thickness,m,plane='XZ',steps=24):
    x,y,z=c
    def pt(rr,t):return (x+rr*math.cos(t),y,z+rr*math.sin(t)) if plane=='XZ' else (x,y+rr*math.cos(t),z+rr*math.sin(t))
    for i in range(steps):
        a=i*math.tau/steps; b=(i+1)*math.tau/steps
        face(n,[pt(r-thickness,a),pt(r-thickness,b),pt(r,b),pt(r,a)],m)
rng=random.Random(105)
front=lambda u,v,z:(u,-4-v,z)
right=lambda u,v,z:(5+v,u,z)
back=lambda u,v,z:(-u,4+v,z)
left=lambda u,v,z:(-5-v,-u,z)
# Main ground floor and narrower two-storey house create an actual terrace silhouette.
box('01_Ground_Mass',(0,0,1.71),(10,8,3.42),MORTAR)
box('01_Upper_House',(1.4,0,4.90),(7.2,8,2.98),PLASTER)
box('02_Stone_Base',(0,0,.17),(10.12,8.12,.34),LIGHT)
box('02_Stone_Courses',(0,0,3.42),(10.2,8.2,.18),LIGHT)
box('02_Stone_Courses',(1.4,0,6.35),(7.45,8.25,.19),WOODD)
# Brick courses on lower walls and stepped areas of exposed brick on the upper plaster.
for name,length,mp in [('Front',10,front),('Right',8,right),('Rear',10,back),('Left',8,left)]:
    for row in range(14):
        z=.35+row*.215
        for col in range(-14,14):
            a=max(-length/2,col*.39+(row%2)*.195+.012); b=min(length/2,(col+1)*.39+(row%2)*.195-.012)
            if b>a:face('03_Lower_Brick_'+name,[mp(a,.016,z),mp(b,.016,z),mp(b,.016,z+.19),mp(a,.016,z+.19)],rng.choice(BRICKS))
# Deliberate plaster wear patches: large readable areas, not noise across the whole wall.
for name,mp,a,b in [('Front',front,-2.2,5),('Right',right,-4,4),('Rear',back,-5,2.2)]:
    for row in range(13):
        z=3.52+row*.215
        for col in range(-15,15):
            x=col*.39+(row%2)*.195
            if x<a or x+.37>b:continue
            exposed=(row<2 or (x<a+.65 and row<10) or (x>b-.60 and row>3) or (row<5 and (col+3*row)%13<4))
            if exposed:face('04_Exposed_Brick_'+name,[mp(x,.021,z),mp(x+.365,.021,z),mp(x+.365,.021,z+.188),mp(x,.021,z+.188)],rng.choice(BRICKS))
# Corner brick piers make the patchy plaster construction read from a distance.
for x in (-2.2,5):
    for y in (-4,4):
        for j in range(13):
            box('05_Corner_Brick',(x,y,3.57+j*.214),(.24,.25,.19),BRICKS[j%4])
# A few geometric plaster repairs, attached to exterior only.
for u,z,w,h in [(-1.65,5.65,.25,.37),(2.6,5.85,.32,.25),(4.45,4.15,.35,.32),(.1,3.78,.20,.25)]:
    box('06_Plaster_Repairs',(u,.028,z),(w,.012,h),PATCH,front)

def window(n,u,z,mp,w=1.3,h=1.58,shutters=False):
    box(n,(u,.044,z),(w+.22,.09,h+.24),WOODD,mp)
    box(n,(u,.10,z),(w,.06,h),GLASS,mp)
    for x in (-w/2,w/2):box(n,(u+x,.15,z),(.085,.16,h+.12),LIGHT,mp)
    for zz in (-h/2,h/2):box(n,(u,.15,z+zz),(w+.14,.16,.09),LIGHT,mp)
    box(n,(u,.17,z),(.065,.10,h),WOODL,mp)
    box(n,(u,.17,z+.15),(w,.10,.065),WOODL,mp)
    box(n,(u,.21,z-h/2-.12),(w+.4,.43,.15),LIGHT,mp)
    box(n,(u,.13,z+h/2+.13),(w+.36,.19,.16),LIGHT,mp)
    # Opaque curtain strips indicate residence without modelling an interior.
    for dx in (-w*.34,w*.34):box(n,(u+dx,.135,z),(.18,.016,h-.14),CREAM,mp)
    if shutters:
        for side in (-1,1):
            sx=u+side*(w/2+.29)
            box(n,(sx,.12,z),(.39,.13,h),WOODD,mp)
            for i in range(9):box(n,(sx,.205,z-h/2+.10+i*(h-.15)/9),(.34,.07,.09),WOODL,mp)

window('07_Upper_Front',-.52,4.92,front,1.35,1.56,True)
window('07_Upper_Front',3.05,4.92,front,1.35,1.56,True)
for u in (-2.1,1.65):window('08_Right_Windows',u,4.94,right,1.10,1.52,True)
for u in (-3.6,.3):window('08_Rear_Windows',u,4.94,back,1.2,1.52)
upperleft=lambda u,v,z:(-2.2-v,-u,z)
window('08_Terrace_Window',-1.8,4.95,upperleft,1.0,1.5)
box('09_Terrace_Door',(.4,.08,4.55),(1.0,.12,2.15),WOODD,upperleft)
box('09_Terrace_Door',(.4,.16,4.94),(.70,.05,1.05),GLASS,upperleft)
# Lower storefront. Shallow opaque display panels, no rooms/interior.
for u,w in [(-3.37,2.18),(-.78,2.18),(3.33,2.15)]:
    box('10_Shopfront',(u,.065,1.55),(w+.22,.16,2.24),WOODD,front)
    box('10_Shopfront',(u,.17,1.52),(w,.04,2.04),AMBER,front)
    for dx in (-w/2,0,w/2):box('10_Shopfront',(u+dx,.31,1.54),(.105,.20,2.14),WOODL,front)
    for z in (.50,2.59):box('10_Shopfront',(u,.31,z),(w+.18,.22,.12),WOODL,front)
    # Small shelf objects arranged as a relief within the storefront panel.
    for z in (.91,1.63):
        box('11_Display_Relief',(u,.24,z),(w-.15,.12,.065),WOODL,front)
        for j in range(4):
            px=u-w*.38+j*w*.25
            if j%2:
                rod('11_Display_Relief',front(px,.255,z+.045),front(px,.255,z+.30),.11,GOLD,8,r2=.075)
                rod('11_Display_Relief',front(px,.255,z+.30),front(px,.255,z+.37),.052,GOLD,8)
            else:
                for k in range(3):box('11_Display_Relief',(px+k*.06,.255,z+.15+k*.015),(.048,.08,.27+k*.03),[GREEN,RED,BLUE][k],front)
# Shop door on the right of centre.
box('12_Shop_Door',(1.38,.09,1.38),(1.43,.18,2.55),WOODD,front)
box('12_Shop_Door',(1.38,.22,1.37),(1.19,.12,2.34),WOODL,front)
box('12_Shop_Door',(1.38,.30,1.78),(.93,.035,1.24),GLASS,front)
for u in (1.02,1.38,1.74):box('12_Shop_Door',(u,.325,1.78),(.044,.05,1.24),WOODD,front)
for z in (.59,.89):box('12_Shop_Door',(1.38,.30,z),(.91,.05,.20),WOODD,front)
rod('12_Shop_Door',front(1.83,.39,1.05),front(1.83,.39,1.32),.025,GOLD)
box('12_Shop_Steps',(1.38,-4.53,.08),(1.88,.78,.16),LIGHT)
box('12_Shop_Steps',(1.38,-4.24,.17),(1.68,.42,.18),LIGHT)
# Wide readable sign and three-ball pawn emblem.
box('13_Signboard',(0,-4.24,3.02),(9.66,.33,.86),WOODD)
for z in (2.59,3.45):box('13_Sign_Frame',(0,-4.44,z),(9.78,.09,.08),GOLD)
for x in (-4.84,4.84):box('13_Sign_Frame',(x,-4.44,3.02),(.08,.09,.92),GOLD)
for x,z in [(-4.05,3.19),(-4.33,2.87),(-3.77,2.87)]:
    ring('14_Pawn_Emblem',(x,-4.48,z),.145,.047,GOLD)
rod('14_Pawn_Emblem',(-4.05,-4.48,3.04),(-4.33,-4.48,2.98),.019,GOLD)
rod('14_Pawn_Emblem',(-4.05,-4.48,3.04),(-3.77,-4.48,2.98),.019,GOLD)
# Striped storefront awning, projecting from the face with a scalloped valance.
for i in range(24):
    a=-4.65+i*9.30/24; b=a+9.30/24
    m=RED if i%2==0 else CREAM
    face('15_Striped_Awning',[(a,-4.43,2.58),(b,-4.43,2.58),(b,-5.33,2.24),(a,-5.33,2.24)],m)
    face('15_Striped_Awning',[(a,-5.33,2.24),(b,-5.33,2.24),(b,-5.33,2.06),(b-.07,-5.33,2.01),(a+.07,-5.33,2.01),(a,-5.33,2.06)],m)
for x in (-4.61,-1.6,1.6,4.61):rod('15_Awning_Supports',(x,-4.2,2.23),(x,-5.28,2.22),.021,METAL)
# Upper left terrace, plank decking and stout railings.
for i in range(14):box('16_Terrace_Deck',(-4.97+i*.202,-1.95,3.56),(.187,4.3,.12),WOODL if i%4==0 else WOOD)
for x in (-5.03,-3.65,-2.27):
    box('17_Terrace_Rails',(x,-4.10,4.12),(.16,.16,1.12),WOODL)
    box('17_Terrace_Rails',(x,-4.10,4.70),(.23,.23,.10),LIGHT)
for y in (-2.65,-1.25,.1):box('17_Terrace_Rails',(-5.03,y,4.12),(.15,.15,1.10),WOODL)
for z in (3.77,4.58):
    box('17_Terrace_Rails',(-3.65,-4.10,z),(2.91,.12,.13),WOODL)
    box('17_Terrace_Rails',(-5.03,-2.0,z),(.12,4.35,.13),WOODL)
for i in range(11):box('17_Terrace_Rails',(-4.9+i*.24,-4.10,4.13),(.065,.085,.79),WOOD)
for i in range(16):box('17_Terrace_Rails',(-5.03,-3.9+i*.25,4.13),(.085,.065,.79),WOOD)
# Rug draped over railing.
box('18_Terrace_Rug',(-3.67,-4.19,4.23),(1.0,.025,.68),RUG)
for x in (-4.12,-3.22):box('18_Terrace_Rug',(x,-4.21,4.23),(.04,.018,.65),GOLD)
for z in (3.93,4.53):box('18_Terrace_Rug',(-3.67,-4.21,z),(.94,.018,.04),GOLD)
# Simple olive canvas canopy, with a visible slope and light string.
for x in (-5.04,-2.25):rod('19_Terrace_Canopy',(x,-3.95,3.56),(x,-3.95,5.60),.04,WOODD)
face('19_Terrace_Canopy',[(-5.22,-4.23,5.60),(-2.18,-4.23,5.60),(-2.18,-.50,5.97),(-5.22,-.50,5.97)],GREEN)
box('19_Terrace_Canopy',(-3.70,-4.23,5.52),(3.05,.04,.18),GREEN)
for i in range(8):
    x=-5.05+i*.39; z=5.47-.12*math.sin(i*math.pi/7)
    rod('20_Terrace_String',(x,-4.25,z),(x+.39,-4.25,5.47-.12*math.sin((i+1)*math.pi/7)),.012,METAL)
    rod('20_Terrace_String',(x,-4.25,z),(x,-4.25,z-.11),.012,METAL)
    rod('20_Terrace_String',(x,-4.25,z-.15),(x,-4.25,z-.21),.043,GLOW,8)
# Main pitched roof, ridge along X. Dormer interrupts the front slope.
rx0,rx1=-2.62,5.42; eave=6.46; ridge=8.48; dep=4.43
for side in (-1,1):
    face('21_Main_Roof',[(rx0,side*dep,eave),(rx1,side*dep,eave),(rx1,0,ridge),(rx0,0,ridge)],SLATES[0])
    for row in range(13):
        ya=row*dep/13+.012; yb=(row+1)*dep/13-.012
        for col in range(16):
            xa=max(rx0,rx0+col*.55-(row%2)*.275+.012); xb=min(rx1,rx0+(col+1)*.55-(row%2)*.275-.012)
            if xb<=xa:continue
            za=ridge-(ridge-eave)*ya/dep+.018; zb=ridge-(ridge-eave)*yb/dep+.018
            face('22_Slate_Tiles',[(xa,side*ya,za),(xb,side*ya,za),(xb,side*yb,zb),(xa,side*yb,zb)],rng.choice(SLATES))
for x in (-2.2,5):face('23_Gable_Plaster',[(x,-4,6.30),(x,4,6.30),(x,0,8.27)],PLASTER)
for x in (rx0,rx1):
    for s in (-1,1):rod('24_Roof_Trim',(x,s*dep,eave),(x,0,ridge+.02),.083,WOODL,4)
for y in (-dep,dep):box('24_Roof_Trim',(1.4,y,6.43),(8.15,.17,.17),WOODL)
rod('24_Roof_Trim',(rx0,0,ridge+.045),(rx1,0,ridge+.045),.085,SLATES[1],6)
# Front dormer: clear small house-shaped silhouette, not a third full storey.
box('25_Dormer_Mass',(1.15,-2.01,7.30),(1.82,1.96,1.32),PLASTER)
dormer=lambda u,v,z:(u,-3.02-v,z)
window('26_Dormer_Window',1.15,7.30,dormer,1.04,1.12,False)
face('25_Dormer_Mass',[(.24,-3.025,7.91),(2.06,-3.025,7.91),(1.15,-3.025,8.49)],PLASTER)
for side in (-1,1):
    face('27_Dormer_Roof',[(1.15,-3.25,8.57),(1.15,-.90,8.57),(1.15+side*1.10,-.90,7.96),(1.15+side*1.10,-3.25,7.96)],SLATES[1])
    rod('27_Dormer_Roof',(1.15,-3.27,8.56),(1.15+side*1.11,-3.27,7.95),.065,WOODL,4)
# Chimney with simple brick coursing and a rain cap.
box('28_Chimney',(3.25,.55,8.73),(.69,.76,1.49),MORTAR)
for j in range(7):
    z=8.10+j*.19
    box('28_Chimney',(3.25,.55,z),(.71,.78,.165),BRICKS[j%4])
    box('28_Chimney',(3.25+(.17 if j%2 else -.17),.151,z),(.018,.02,.16),MORTAR)
box('28_Chimney',(3.25,.55,9.48),(.85,.92,.14),LIGHT)
for x in (2.94,3.56):rod('28_Chimney',(x,.55,9.53),(x,.55,9.79),.025,METAL)
box('28_Chimney',(3.25,.55,9.80),(.95,1.02,.10),METAL)
# A modest TV aerial, one domestic detail rather than rooftop machinery.
rod('29_Aerial',(4.37,.6,7.95),(4.37,.6,9.4),.021,METAL)
rod('29_Aerial',(3.8,.6,9.2),(4.94,.6,9.2),.018,METAL)
for x in (3.85,4.12,4.39,4.66,4.91):rod('29_Aerial',(x,.36,9.2),(x,.84,9.2),.012,METAL)
# Right-side storage lean-to; keep overall width within the old 16m parcel.
for y in (-2.3,2.0):
    box('30_LeanTo_Frame',(7.1,y,1.19),(.18,.18,2.38),WOOD)
    rod('30_LeanTo_Frame',(7.1,y,1.78),(6.45,y,2.59),.065,WOODL,4)
box('30_LeanTo_Frame',(7.1,-.15,2.4),(.19,4.73,.19),WOOD)
for i in range(17):
    ya=-2.6+i*.29; yb=ya+.275
    face('31_LeanTo_Planks',[(4.92,ya,3.24),(7.4,ya,2.42),(7.4,yb,2.42),(4.92,yb,3.24)],WOODL if i%4==0 else WOOD)
for y in (-2.63,2.31):rod('31_LeanTo_Planks',(4.88,y,3.25),(7.42,y,2.41),.075,WOODD,4)
# Domestic downpipe, one AC on the side. Secondary to the building silhouette.
rod('32_Drainpipe',(5.16,-3.74,.30),(5.16,-3.74,6.38),.048,METAL)
for z in (1.1,3.2,5.3):box('32_Drainpipe',(5.16,-3.74,z),(.16,.16,.055),WOODD)
box('33_Domestic_AC',(-.1,.35,4.19),(.85,.45,.56),LIGHT,right)
rod('33_Domestic_AC',right(-.20,.58,4.19),right(-.20,.60,4.19),.19,METAL,16)
for i in range(5):box('33_Domestic_AC',(.17,.605,4.04+i*.075),(.22,.025,.027),WOODD,right)
# Low-poly pots and plants. Keep each cluster grouped for easy removal.
def plant(n,x,y,z,rad=.20):
    rod(n,(x,y,z),(x,y,z+.35),rad*.72,POT,10,r2=rad)
    rod(n,(x,y,z+.31),(x,y,z+.38),rad*1.09,POT,10)
    for j in range(5):
        a=j*math.tau/5
        xx=x+rad*.6*math.cos(a); yy=y+rad*.6*math.sin(a)
        rod(n,(x,y,z+.35),(xx,yy,z+.68),.014,LEAVES[0],5)
        rod(n,(xx,yy,z+.53),(xx,yy,z+.82+rng.uniform(-.06,.07)),rad*.64,LEAVES[j%3],7,r2=.035)
for x,y,z in [(-4.65,-3.65,3.62),(-2.7,-3.62,3.62),(-4.65,-.4,3.62),(-4.58,-4.78,0),(4.67,-4.63,0),(6.8,1.85,0)]:plant('34_Potted_Plants',x,y,z)
for u in (-.52,3.05):
    box('35_Window_Boxes',(u,.36,3.99),(1.55,.43,.25),WOOD,front)
    for j in range(7):
        p=front(u-.64+j*.21,.39,4.12)
        rod('35_Window_Boxes',p,(p[0],p[1],p[2]+.22),.13,LEAVES[j%3],6,r2=.055)
# Bench and small storage clutter, deliberately no full street furniture scene.
for x in (-3.83,-2.30):box('36_Bench',(x,-5.31,.27),(.10,.42,.54),METAL)
for j in range(3):box('36_Bench',(-3.06,-5.48+j*.15,.55),(1.95,.13,.075),WOODL)
for j in range(2):box('36_Bench',(-3.06,-5.08,.82+j*.16),(1.95,.07,.13),WOOD)
for x in (-3.83,-2.30):box('36_Bench',(x,-5.08,.70),(.07,.08,.80),METAL)
def crate(n,c,s):
    x,y,z=c; a,b,h=s
    box(n,c,s,WOODD)
    for i in range(5):
        box(n,(x-a/2+(i+.5)*a/5,y-b/2-.012,z),(a/5-.022,.045,h-.06),WOODL)
        box(n,(x-a/2+(i+.5)*a/5,y,z+h/2+.013),(a/5-.022,b,.035),WOOD)
    for zz in (z-h*.33,z+h*.33):box(n,(x,y-b/2-.042,zz),(a+.04,.045,.064),WOOD)
crate('37_Crates',(5.77,-.60,.49),(.91,.81,.98)); crate('37_Crates',(5.88,.43,.38),(.75,.80,.76)); crate('37_Crates',(5.77,-.60,1.32),(.71,.66,.67))
crate('37_Crates',(3.82,-4.96,.25),(.78,.52,.50))
# Goose-neck lamps above the sign.
for x in (-3.15,0,3.15):
    rod('38_Sign_Lamps',(x,-4.12,3.62),(x,-4.63,3.87),.026,METAL)
    rod('38_Sign_Lamps',(x,-4.63,3.87),(x,-4.74,3.63),.026,METAL)
    rod('38_Sign_Lamps',(x,-4.74,3.52),(x,-4.74,3.65),.17,METAL,12,r2=.055)
    rod('38_Sign_Lamps',(x,-4.74,3.505),(x,-4.74,3.525),.12,GLOW,12)
# Freestanding small A-board, limited to the building's frontage.
box('39_Aboard',(-4.88,-5.02,.66),(.56,.12,.95),WOODL)
box('39_Aboard',(-4.88,-5.09,.68),(.46,.035,.77),WOODD)
for x in (-5.16,-4.60):rod('39_Aboard',(x,-5.24,0),(x,-4.90,1.17),.035,WOOD,4)
# Build editable architectural assemblies. Open surfaces retain their intended winding.
created=[]
for name,(vv,ff,mm) in groups.items():
    mesh=bpy.data.meshes.new('RUDY_'+name); mesh.from_pydata(vv,[],ff); mesh.update()
    used=sorted(set(mm)); remap={i:j for j,i in enumerate(used)}
    for i in used:mesh.materials.append(materials[i])
    for p,i in zip(mesh.polygons,mm):p.material_index=remap[i]
    bm=bmesh.new(); bm.from_mesh(mesh); bm.normal_update()
    loose={f: f.normal.copy() for f in bm.faces if all(e.is_boundary for e in f.edges)}
    bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces)); bm.normal_update()
    for f,n in loose.items():
        if f.normal.dot(n)<0:f.normal_flip()
    # Roof faces should always face upwards.
    if name.startswith(('21_','22_','27_','31_','15_Striped','19_Terrace')):
        for f in bm.faces:
            if abs(f.normal.z)>.1 and f.normal.z<0 and all(e.is_boundary for e in f.edges):f.normal_flip()
    bm.to_mesh(mesh); bm.free(); mesh.update()
    obj=bpy.data.objects.new('RUDY_'+name,mesh); coll.objects.link(obj); obj.parent=root; obj['assembly']=name; created.append(obj)
# Legible lettering retained as editable text, separate from geometry.
def text(n,body,loc,size,material,maxwidth=None):
    c=bpy.data.curves.new('RUDY_'+n,'FONT'); c.body=body; c.align_x='CENTER'; c.align_y='CENTER'; c.size=size; c.extrude=.003; c.resolution_u=3
    o=bpy.data.objects.new('RUDY_'+n,c); coll.objects.link(o); o.parent=root; o.location=loc; o.rotation_euler=(math.pi/2,0,0); c.materials.append(materials[material]); bpy.context.view_layer.update()
    if maxwidth and o.dimensions.x>maxwidth:c.size*=maxwidth/o.dimensions.x
    return o
text('40_Main_Lettering',"RUDY'S PAWN",(.28,-4.48,3.02),.59,GOLD,6.82)
text('40_Sign_Trade','BUY\nSELL\nTRADE',(4.13,-4.48,3.04),.17,GOLD,.78)
text('41_Door_Open','OPEN',(1.38,-4.37,1.87),.16,GOLD,.68)
text('41_Aboard_Text','BUY\nSELL\nTRADE',(-4.88,-5.12,.68),.13,CREAM,.43)
# Preview setup; existing scene is left intact in its own scene tab.
for o in bpy.context.selected_objects:o.select_set(False)
root.select_set(True); bpy.context.view_layer.objects.active=root
for area in bpy.context.screen.areas:
    if area.type=='VIEW_3D':
        s=area.spaces.active; s.shading.type='SOLID'; s.shading.light='STUDIO'; s.shading.color_type='MATERIAL'; s.shading.show_shadows=True; s.shading.show_cavity=True; s.shading.cavity_type='BOTH'; s.shading.curvature_ridge_factor=1.1; s.shading.curvature_valley_factor=.85
        s.shading.background_type='VIEWPORT'; s.shading.background_color=(.19,.21,.235); s.overlay.show_overlays=False; s.show_gizmo=False
        s.region_3d.view_rotation=Vector((1.3,-2,1.05)).to_track_quat('Z','Y'); s.region_3d.view_location=(.6,-.3,4.3); s.region_3d.view_distance=21; s.region_3d.view_perspective='ORTHO'; area.tag_redraw()
bpy.context.view_layer.update()
pts=[o.matrix_world@Vector(c) for o in coll.objects if o.type in {'MESH','FONT'} for c in o.bound_box]
lo=[min(p[i] for p in pts) for i in range(3)]; hi=[max(p[i] for p in pts) for i in range(3)]
report={'body_footprint_m':[10,8],'main_eave_m':6.46,'ridge_m':8.48,'min_m':lo,'max_m':hi,'total_dimensions_m':[hi[i]-lo[i] for i in range(3)],'storeys':2,'attic':True,'mesh_assemblies':len(created),'editable_texts':4,'triangles':sum(len(p.vertices)-2 for o in created for p in o.data.polygons),'zero_area_faces':sum(p.area<1e-10 for o in created for p in o.data.polygons),'root_m':list(root.location),'target_actor':'BO_Pawnshop','ue_exported':False}
root['validation']=json.dumps(report)
Path('D:/UEProject/ArcheoDig/Saved/BlenderRudy/validation.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
result=report
