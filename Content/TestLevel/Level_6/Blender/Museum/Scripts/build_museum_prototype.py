import bpy, math, os
from mathutils import Vector
from math import sin,cos,pi

scene=bpy.data.scenes.new('Museum_Prototype')
bpy.context.window.scene=scene
scene.unit_settings.system='METRIC'
scene.unit_settings.scale_length=1
assembly=bpy.data.collections.new('BLD_Museum'); scene.collection.children.link(assembly)
root=bpy.data.objects.new('Museum_ROOT',None); assembly.objects.link(root)
root['status']='Prototype вЂ” dimensions not locked; no UE export'
groups={}
for name in ['Walls','Roof','Windows','Entrance','Columns_Trim','Props']:
    c=bpy.data.collections.new(name); assembly.children.link(c); groups[name]=c
def mat(name,c,metal=0):
    m=bpy.data.materials.new('Museum_'+name); m.diffuse_color=(*c,1); m.use_nodes=True
    p=next(n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED'); p.inputs['Base Color'].default_value=(*c,1); p.inputs['Roughness'].default_value=.64; p.inputs['Metallic'].default_value=metal
    return m
stone=mat('Warm_Limestone',(.68,.53,.34)); trim=mat('Ivory_Cutstone',(.88,.74,.51)); inset=mat('Recess_Shadow',(.09,.105,.11)); glass=mat('Smoky_Teal_Glass',(.105,.22,.25),.3); roofmat=mat('Charcoal_Slate',(.085,.12,.16)); bronze=mat('Aged_Bronze',(.32,.20,.085),.45); wood=mat('Walnut_Entry',(.19,.075,.026)); blue=mat('Museum_Deep_Blue',(.025,.105,.19)); gold=mat('Banner_Ochre',(.88,.59,.20)); base=mat('Base_Sandstone',(.48,.40,.29))
def finish(o,name,m,g):
    o.name='MUS_'+name
    for c in list(o.users_collection): c.objects.unlink(o)
    groups[g].objects.link(o); o.parent=root
    if m:o.data.materials.append(m)
    return o
def box(name,loc,dims,m,g='Columns_Trim',bevel=.035):
    bpy.ops.mesh.primitive_cube_add(size=1,location=loc); o=bpy.context.object; o.scale=dims
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    finish(o,name,m,g)
    if bevel:
        b=o.modifiers.new('Soft stone edges','BEVEL'); b.width=bevel;b.segments=2
    return o
def mesh(name,vs,fs,m,g):
    me=bpy.data.meshes.new(name);me.from_pydata(vs,[],fs);me.update();o=bpy.data.objects.new(name,me);groups[g].objects.link(o);o.parent=root;o.data.materials.append(m);return o
def line(name,pts,r,m,g='Columns_Trim'):
    cu=bpy.data.curves.new(name,'CURVE');cu.dimensions='3D';cu.bevel_depth=r;cu.bevel_resolution=2
    s=cu.splines.new('POLY');s.points.add(len(pts)-1)
    for p,co in zip(s.points,pts):p.co=(*co,1)
    o=bpy.data.objects.new('MUS_'+name,cu);groups[g].objects.link(o);o.parent=root;cu.materials.append(m);return o
def cyl(name,loc,r,depth,m,g='Columns_Trim',r2=None):
    bpy.ops.mesh.primitive_cone_add(vertices=32,radius1=r,radius2=r if r2 is None else r2,depth=depth,location=loc)
    o=finish(bpy.context.object,name,m,g)
    for p in o.data.polygons:p.use_smooth=len(p.vertices)==4
    return o
def text(name,body,loc,size,m):
    cu=bpy.data.curves.new(name,'FONT');cu.body=body;cu.align_x='CENTER';cu.size=size;cu.extrude=.008
    o=bpy.data.objects.new('MUS_'+name,cu);groups['Props'].objects.link(o);o.parent=root;o.location=loc;o.rotation_euler=(pi/2,0,0);cu.materials.append(m);return o
def hip(name,x,y,w,d,z,h):
    vs=[(x-w/2,y-d/2,z),(x+w/2,y-d/2,z),(x+w/2,y+d/2,z),(x-w/2,y+d/2,z),(x,y-d/2+w*.36,z+h),(x,y+d/2-w*.36,z+h)]
    mesh(name,vs,[(0,1,4),(1,2,5,4),(2,3,5),(3,0,4,5),(3,2,1,0)],roofmat,'Roof')
    for a,b in [(0,4),(1,4),(2,5),(3,5),(4,5)]:line(name+'_Seam',[vs[a],vs[b]],.065,bronze,'Roof')

# Main envelope: front -Y; 30 m facade, 21 m body, stair apron to -13.5.
box('Foundation',(0,0,.35),(30,21,.7),base,'Walls')
box('Main_Two_Storey_Envelope',(0,0,4.2),(29.6,20.6,7.0),stone,'Walls')
box('Central_Pavilion',(0,-9.5,4.6),(10.3,3.1,7.8),stone,'Walls')
for z,h,out in [(.75,.24,.2),(4.05,.24,.25),(7.55,.22,.3),(7.85,.3,.65)]:
    box('Perimeter_Stringcourse',(0,0,z),(30+out,21+out,h),trim)
for x in [-14.55,14.55]:
    for y in [-10.15,10.15]:
        box('Corner_Pilaster',(x,y,4.15),(.7,.7,6.7),trim)
        for z in [1.1,1.8,2.5,3.2,4.6,5.3,6,6.7]:box('Quoin',(x,y,z),(.86,.86,.26),trim)
hip('Main_Hipped_Roof',0,0,31,22,8.0,2.45)
# Shallow horizontal stone joints retain broad, quiet masonry.
for z in [1.5,2.3,3.1,4.8,5.6,6.4,7.15]:
    box('Front_Masonry_Joint',(0,-10.314,z),(29.1,.025,.024),base,bevel=0)
    for x in [-14.814,14.814]:box('Side_Masonry_Joint',(x,0,z),(.025,20.1,.024),base,bevel=0)

def window(name,x,y,z,w=1.65,h=2.7,angle=0,arched=True):
    # Local facade coordinates, outward normal -Y; rotate onto side/rear elevations.
    made=[]; before=set(bpy.data.objects)
    r=w/2; spring=h-r
    if arched:
        outline=[(-r,0,0),(r,0,0)]+[(r*cos(t*pi/24),0,spring+r*sin(t*pi/24)) for t in range(25)]
    else:outline=[(-r,0,0),(r,0,0),(r,0,h),(-r,0,h)]
    mesh(name+'_Dark_Reveal',[(a,-.07,c) for a,b,c in outline],[tuple(range(len(outline)))],inset,'Windows')
    mesh(name+'_Glass',[(a*.89,-.095,.10+c*.94) for a,b,c in outline],[tuple(range(len(outline)))],glass,'Windows')
    line(name+'_Stone_Arch',[(a,-.14,c) for a,b,c in outline+[outline[0]]],.115,trim,'Windows')
    box(name+'_Sill',(0,-.17,0),(w+.48,.40,.18),trim,'Windows')
    box(name+'_Mullion',(0,-.19,h/2),(.075,.09,h-.10),bronze,'Windows',.01)
    for zz in [.85,1.65]:
        if zz<h-r*.15:box(name+'_Transom',(0,-.19,zz),(w-.13,.09,.065),bronze,'Windows',.01)
    if arched:box(name+'_Keystone',(0,-.16,h+.045),(.28,.26,.36),trim,'Windows')
    for o in set(bpy.data.objects)-before:
        o.location=Vector((x,y,z))+Vector((cos(angle)*o.location.x-sin(angle)*o.location.y,sin(angle)*o.location.x+cos(angle)*o.location.y,o.location.z))
        o.rotation_euler.z+=angle
for x in [-12,-8.3,8.3,12]:
    window('Front_Lower',x,-10.35,1.12,h=2.45,arched=False)
    window('Front_Upper',x,-10.35,4.48,h=2.72)
for side in [-1,1]:
    for y in [-7.7,-3.85,0,3.85,7.7]:
        window('Gallery_Lower',side*14.84,y,1.12,h=2.45,angle=side*pi/2,arched=False)
        window('Gallery_Upper',side*14.84,y,4.48,h=2.72,angle=side*pi/2)
for x in [-11,-6,0,6,11]:
    window('Rear_Lower',x,10.35,1.12,h=2.45,angle=pi,arched=False)
    window('Rear_Upper',x,10.35,4.48,h=2.72,angle=pi)

# Broad stairs and a two-column monumental portico.
for i in range(7):
    depth=3.0-i*.36
    box('Entry_Step_%02d'%i,(0,-10.5-depth/2,(i+1)*.15/2),(8.4,depth,(i+1)*.15),trim,'Entrance',.025)
box('Entry_Landing',(0,-10.85,1.0),(9.4,1.8,.3),trim,'Entrance')
box('Portal_Shadow',(0,-11.075,2.6),(3.7,.08,3.1),inset,'Entrance')
for x in [-.79,.79]:
    box('Oak_Door',(x,-11.16,2.54),(1.49,.16,2.82),wood,'Entrance')
    box('Door_Glass',(x,-11.26,2.9),(1.10,.05,1.5),glass,'Entrance')
    for xx in [x-.57,x+.57]:box('Door_Stile',(xx,-11.30,2.55),(.09,.08,2.65),bronze,'Entrance')
    box('Door_Lower_Panel',(x,-11.26,1.6),(1.12,.07,.65),bronze,'Entrance')
    cyl('Door_Handle',(x*.20,-11.37,2.2),.045,.42,gold,'Entrance')
window('Central_Arched_Transom',0,-11.075,4.27,w=3.45,h=3.1)
for x in [-3.85,3.85]:
    box('Column_Plinth',(x,-11.65,1.3),(1.15,1.15,.5),trim,'Entrance')
    cyl('Column_Base',(x,-11.65,1.65),.54,.22,trim)
    cyl('Tapered_Column',(x,-11.65,4.6),.43,5.7,trim,r2=.35)
    cyl('Column_Capital',(x,-11.65,7.48),.53,.22,trim)
    box('Capital_Abacus',(x,-11.65,7.69),(1.2,1.1,.23),trim)
box('Portico_Entablature',(0,-11.45,8.10),(10.6,1.9,.70),trim)
box('Portico_Cornice',(0,-11.45,8.55),(11.0,2.15,.22),trim)
text('Museum_Name','TOWN MUSEUM',(0,-12.415,7.94),.55,bronze)
vs=[(-5.5,-12.55,8.68),(5.5,-12.55,8.68),(0,-12.55,11.30),(-5.5,-10.55,8.68),(5.5,-10.55,8.68),(0,-10.55,11.30)]
mesh('Central_Pediment',vs,[(0,1,2),(5,4,3),(0,3,4,1),(1,4,5,2),(2,5,3,0)],stone,'Entrance')
for a,b in [(0,1),(0,2),(1,2)]:line('Pediment_Moulding',[vs[a],vs[b]],.16,trim)
line('Pediment_Inner_Border',[(-4.6,-12.59,8.9),(0,-12.59,11.02),(4.6,-12.59,8.9)],.065,trim)
# Small roof lantern, civic rather than campus silhouette.
box('Lantern_Curb',(0,-2,10.1),(4.5,4.5,.45),trim,'Roof')
box('Lantern_Glazing',(0,-2,10.7),(3.9,3.9,1.05),glass,'Roof')
for x in [-1.95,0,1.95]:
    for y in [-3.95,-.05]:box('Lantern_Frame',(x,y,10.7),(.09,.09,1.08),bronze,'Roof')
for x in [-1.95,1.95]:box('Lantern_Side_Frame',(x,-2,10.7),(.09,.09,1.08),bronze,'Roof')
hip('Lantern_Cap',0,-2,4.5,4.5,11.26,.68)
# Vertical exhibition banners and restrained amphora emblems.
def amphora(name,x,y,z,s):
    profile=[(.12,0),(.23,.10),(.39,.43),(.42,.7),(.27,.92),(.16,1.0),(.16,1.18),(.25,1.20)]
    vs=[(x+r*s*cos(t*2*pi/32),y+r*s*sin(t*2*pi/32),z+h*s) for r,h in profile for t in range(32)]
    fs=[]
    for j in range(len(profile)-1):
        for t in range(32):a=j*32+t;b=j*32+(t+1)%32;fs.append((a,b,b+32,a+32))
    mesh(name,vs,fs,gold,'Props')
    for side in [-1,1]:line(name+'_Handle',[(x+side*s*(.22+.26*sin(t*pi/16)),y,z+s*(1.02-.50*t/16)) for t in range(17)],.045*s,gold,'Props')
for x in [-5.55,5.55]:
    box('Exhibition_Banner',(x,-10.68,5.15),(1.5,.09,3.5),blue,'Props')
    for z in [3.39,6.91]:box('Banner_Hem',(x,-10.75,z),(1.64,.12,.07),gold,'Props')
    amphora('Banner_Amphora',x,-10.91,4.6,.9)
    text('Banner_Label','HISTORY',(x,-10.80,3.75),.19,gold)
amphora('Pediment_Amphora',0,-12.66,9.05,.95)
for side in [-1,1]:
    x=side*4.55
    box('Stair_Cheek',(x,-11.7,.65),(.55,3.4,1.3),stone,'Entrance')
    box('Stair_Cheek_Cap',(x,-11.7,1.33),(.68,3.5,.14),trim,'Entrance')

scene.world=bpy.data.worlds.new('Museum_Preview_World');scene.world.color=(.23,.23,.23)
bpy.ops.object.select_all(action='DESELECT')
bpy.context.view_layer.update()
for screen in bpy.data.screens:
    for area in screen.areas:
        if area.type=='VIEW_3D':
            sp=area.spaces.active;sp.shading.type='SOLID';sp.shading.color_type='MATERIAL';sp.shading.light='STUDIO';sp.shading.studiolight_rotate_z=.4;sp.shading.show_shadows=True;sp.shading.show_cavity=True;sp.shading.cavity_type='BOTH';sp.overlay.show_overlays=False
            sp.region_3d.view_rotation=Vector((.85,-1.55,.82)).to_track_quat('Z','Y');sp.region_3d.view_distance=48;sp.region_3d.view_location=(0,0,4.7);sp.region_3d.view_perspective='ORTHO'
scene['prototype_dimensions']='30 m facade x 24 m including entrance apron; two floors; height 11.94 m'
path='D:/UEProject/ArcheoDig/Content/TestLevel/Level_6/Blender/Source/Museum_Blockout.blend'
# Serialize only this newly created scene and dependencies; Rudy remains untouched.
bpy.data.libraries.write(path,{scene},fake_user=True,compress=True)
result={'saved':path,'objects':len(scene.objects),'bytes':os.path.getsize(path)}

