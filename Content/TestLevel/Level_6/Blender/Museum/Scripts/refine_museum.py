import bpy, math, ast, os
from mathutils import Vector
from math import sin,cos,pi
scene=bpy.context.scene
assert scene.name=='Museum_Prototype' and bpy.data.objects.get('Museum_ROOT')
assert not scene.get('refinement_pass_01')
path=bpy.data.filepath
backup=os.path.join(os.path.dirname(path),'Museum_Blockout_BeforeRefinement.blend')
assert not os.path.exists(backup)
bpy.ops.wm.save_as_mainfile(filepath=backup,copy=True)
root=bpy.data.objects['Museum_ROOT']
groups={k:bpy.data.collections[k] for k in ['Walls','Roof','Windows','Entrance','Columns_Trim','Props']}
# Reuse construction helpers only, never run the original building generator.
source=os.path.join(os.path.dirname(path),'build_museum_prototype.py')
tree=ast.parse(open(source,encoding='utf-8').read())
exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef)],type_ignores=[]),source,'exec'))
stone=bpy.data.materials['Museum_Warm_Limestone.001'];trim=bpy.data.materials['Museum_Ivory_Cutstone'];bronze=bpy.data.materials['Museum_Aged_Bronze'];gold=bpy.data.materials['Museum_Banner_Ochre'];blue=bpy.data.materials['Museum_Museum_Deep_Blue'];glass=bpy.data.materials['Museum_Smoky_Teal_Glass'];base=bpy.data.materials['Museum_Base_Sandstone']
protected={o.name:(tuple(o.matrix_world),len(o.data.vertices) if o.type=='MESH' else None) for o in scene.objects if o.name in ['MUS_Main_Two_Storey_Envelope','MUS_Foundation','MUS_Central_Pavilion','Central_Pediment','Main_Hipped_Roof']}
def recolor(m,c):
    m.diffuse_color=(*c,1)
    p=next(n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED');p.inputs['Base Color'].default_value=(*c,1)
recolor(stone,(.83,.65,.43));recolor(trim,(.98,.84,.61));recolor(base,(.61,.48,.32));recolor(bronze,(.43,.27,.10));recolor(blue,(.022,.13,.25));recolor(glass,(.16,.27,.28))
warm=mat('Warm_Window_Reflection',(.38,.29,.16),.18)
for o in scene.objects:
    if o.name.startswith(('MUS_Front_Lower_Glass','MUS_Door_Glass')):o.data.materials[0]=warm
# Replace only the small roof lantern; main roof and curb remain unchanged.
remove=[o for o in scene.objects if 'Lantern' in o.name and o.name!='MUS_Lantern_Curb']
for o in remove:bpy.data.objects.remove(o,do_unlink=True)
domeglass=mat('Lantern_Blue_Glass',(.28,.47,.51),.35)
def ring(name,r,z):
    return line(name,[(r*cos(t*2*pi/64),-2+r*sin(t*2*pi/64),z) for t in range(65)],.055,bronze,'Roof')
cyl('Lantern_Octagonal_Drum',(0,-2,10.54),1.92,.40,trim,'Roof')
profile=[(1.87,10.72),(1.84,11.00),(1.66,11.40),(1.30,11.77),(.78,12.04),(.22,12.15)]
N=32
vs=[(r*cos(i*2*pi/N),-2+r*sin(i*2*pi/N),z) for r,z in profile for i in range(N)]
fs=[(j*N+i,j*N+(i+1)%N,(j+1)*N+(i+1)%N,(j+1)*N+i) for j in range(len(profile)-1) for i in range(N)]
o=mesh('MUS_Lantern_Glass_Dome',vs,fs,domeglass,'Roof')
for p in o.data.polygons:p.use_smooth=True
for i in range(12):
    a=i*2*pi/12
    line('Dome_Bronze_Rib',[(r*cos(a),-2+r*sin(a),z) for r,z in profile],.045,bronze,'Roof')
for r,z in [profile[0],profile[2],profile[4]]:ring('Dome_Horizontal_Ring',r,z)
cyl('Dome_Crown',(0,-2,12.16),.25,.14,bronze,'Roof')
cyl('Dome_Finial',(0,-2,12.34),.115,.28,gold,'Roof',r2=.025)
# Restrained laurel wreath around the existing pediment amphora.
for side in [-1,1]:
    pts=[(side*(.33+.66*sin(t*pi/2/16)),-12.74,9.12+t*.076) for t in range(17)]
    line('Pediment_Laurel_Stem',pts,.026,gold,'Props')
    for j in range(2,15,2):
        x,y,z=pts[j]
        for outward in [-1,1]:
            leaf=mesh('MUS_Laurel_Leaf',[(x,y,z),(x+side*outward*.16,y-.035,z+.10),(x+side*outward*.27,y,z+.29),(x+side*outward*.04,y+.005,z+.19)],[(0,1,2,3)],gold,'Props')
# Small dentil course; existing pediment and entablature geometry preserved.
for i in range(23):box('Portico_Dentil',(-4.95+i*.45,-12.40,8.48),(.18,.26,.20),trim)
for x in [-4.86,4.86]:
    box('Risalit_Edge_Pilaster',(x,-11.09,4.4),(.26,.16,6.1),trim)
for x in [-1.94,1.94]:box('Portal_Stone_Jamb',(x,-11.22,2.68),(.19,.28,3.1),trim,'Entrance')
box('Portal_Stone_Lintel',(0,-11.22,4.22),(4.07,.31,.20),trim,'Entrance')
# Exhibition banners gain larger lettering, fine borders and a simple key pattern.
for o in scene.objects:
    if o.name.startswith('MUS_Banner_Label'):
        o.data.body='ANCIENT\nSTORIES';o.data.size=.22;o.data.space_line=1.2;o.location.z=3.90
for x in [-5.55,5.55]:
    for dx in [-.69,.69]:box('Banner_Gold_Edge',(x+dx,-10.745,5.15),(.035,.035,3.39),gold,'Props',.005)
    text('Banner_Exhibit_Header','COLLECTION',(x,-10.78,6.52),.165,gold)
    for dx in [-.47,-.16,.16,.47]:
        line('Banner_Key_Pattern',[(x+dx-.1,-10.78,4.35),(x+dx-.1,-10.78,4.49),(x+dx+.1,-10.78,4.49),(x+dx+.1,-10.78,4.40)],.015,gold,'Props')
# Quiet relief panels between floors on four existing front window axes.
for x in [-12,-8.3,8.3,12]:
    box('Gallery_Relief_Panel',(x,-10.44,3.91),(1.7,.12,.34),stone)
    box('Gallery_Relief_Inlay',(x,-10.52,3.91),(1.35,.035,.13),trim)
    for dx in [-.73,.73]:box('Window_Sill_Corbel',(x+dx,-10.52,4.29),(.16,.30,.25),trim)
# Bronze museum plaque and one freestanding archaeological accent.
box('Welcome_Plaque_Frame',(-2.75,-11.18,2.7),(.92,.14,.78),bronze,'Props')
box('Welcome_Plaque_Face',(-2.75,-11.265,2.7),(.80,.035,.66),blue,'Props')
text('Welcome_Plaque_Text','TOWN\nMUSEUM\nHISTORY',(-2.75,-11.29,2.87),.125,gold)
box('Artifact_Pedestal',(6.0,-11.8,.52),(1.15,1.1,1.04),stone,'Props')
box('Artifact_Pedestal_Cap',(6,-11.8,1.10),(1.33,1.25,.16),trim,'Props')
box('Artifact_Pedestal_Foot',(6,-11.8,.11),(1.30,1.23,.22),trim,'Props')
amphora('MUS_Outdoor_Amphora',6,-11.8,1.18,.93)
text('Artifact_Pedestal_Label','ARCHAEOLOGY',(6,-12.365,.61),.105,bronze)
# Modest warm entry lanterns, geometric props without scene lights.
amber=mat('Entry_Lantern_Amber',(.95,.55,.15))
for x in [-2.7,2.7]:
    line('Lantern_Wall_Bracket',[(x,-11.15,4.02),(x,-11.62,4.02),(x,-11.62,3.88)],.035,bronze,'Entrance')
    box('Entry_Lantern_Glass',(x,-11.62,3.64),(.26,.24,.46),amber,'Entrance')
    for z in [3.38,3.9]:box('Entry_Lantern_Cap',(x,-11.62,z),(.37,.34,.08),bronze,'Entrance')
    for dx in [-.145,.145]:box('Entry_Lantern_Frame',(x+dx,-11.755,3.64),(.03,.03,.47),bronze,'Entrance',.005)
bpy.ops.object.select_all(action='DESELECT')
bpy.context.view_layer.update()
assert all((tuple(bpy.data.objects[n].matrix_world),len(bpy.data.objects[n].data.vertices) if bpy.data.objects[n].type=='MESH' else None)==v for n,v in protected.items())
scene['refinement_pass_01']='Existing architecture retained; glass cupola, entrance accents, warmer palette'
for screen in bpy.data.screens:
    for a in screen.areas:
        if a.type=='VIEW_3D':
            sp=a.spaces.active;sp.region_3d.view_rotation=Vector((.50,-1.65,.50)).to_track_quat('Z','Y');sp.region_3d.view_distance=43;sp.region_3d.view_location=(0,-1,5.3);sp.region_3d.view_perspective='ORTHO'
bpy.ops.wm.save_as_mainfile(filepath=path)
result={'saved':path,'backup':backup,'objects':len(scene.objects),'protected_masses_unchanged':list(protected)}


