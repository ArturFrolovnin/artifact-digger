"""Run inside Blender through execute_blender_code. Metres, no save or export.

Source: Docs/GameDesign/Level6_Blockout_Dimensions_v2.md.
Geometry is grouped by architectural assembly with shared material slots.
All mesh origins are at the building ground-centre for a later combined export.
"""
import bpy
import math
import json
from mathutils import Vector

W, D = 26.0, 18.0
FLOORS, BASE, STOREY = 4, 0.45, 2.40
ROOF = BASE + FLOORS * STOREY
PREFIX = 'DORM_'
assert bpy.context.mode == 'OBJECT', 'Please leave Edit mode before building'
assert bpy.data.collections.get('DORMITORY_Blockout') is None, 'Building already exists; refusing to duplicate'
scene = bpy.context.scene
assert abs(scene.unit_settings.scale_length - 1.0) < 1e-6, 'Expected one Blender unit per metre'
protected = {n: (bpy.data.objects[n].as_pointer(), tuple(v for row in bpy.data.objects[n].matrix_world for v in row), bpy.data.objects[n].data.as_pointer()) for n in ('Camera', 'Light') if n in bpy.data.objects}
coll = bpy.data.collections.new('DORMITORY_Blockout')
scene.collection.children.link(coll)
root = bpy.data.objects.new('DORMITORY_ROOT__ground_pivot', None)
coll.objects.link(root)
root.empty_display_type = 'PLAIN_AXES'
root.empty_display_size = 1.5
root['purpose'] = 'Editable city blockout, exterior only. Front = -Y, Z up. No export performed.'
root['body_dimensions_m'] = [W, D, 10.5]
root['storeys'] = FLOORS
root['source'] = 'Docs/GameDesign/Level6_Blockout_Dimensions_v2.md; supplied reference'
root['export_note'] = 'Select child meshes, join a duplicate or use Combine Meshes on import. Shared origin at ground centre. Apply metre-to-centimetre conversion once.'

materials = []
def material(name, color, metallic=0.0, roughness=0.7):
    m = bpy.data.materials.new(PREFIX + name)
    m.diffuse_color = (*color, 1)
    m.use_nodes = True
    p = next(n for n in m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
    p.inputs['Base Color'].default_value = (*color, 1)
    p.inputs['Metallic'].default_value = metallic
    p.inputs['Roughness'].default_value = roughness
    materials.append(m)
    return len(materials) - 1

PLASTER = material('Warm_Limestone', (0.63, 0.49, 0.33))
TERRA = material('Terracotta', (0.46, 0.20, 0.105))
TRIM = material('Pale_Stone', (0.78, 0.68, 0.50))
BASEMAT = material('Basalt_Plinth', (0.22, 0.25, 0.25))
FRAME = material('Painted_Frame', (0.64, 0.66, 0.60), .18, .4)
GLASS = material('Blue_Glass', (0.065, 0.17, 0.23), .35, .25)
GLASS2 = material('Blue_Glass_Light', (0.13, 0.26, 0.30), .3, .3)
DARK = material('Recess_Shadow', (0.035, 0.046, 0.05))
METAL = material('Graphite_Metal', (0.115, 0.15, 0.16), .55, .42)
ROOFMAT = material('Roof_Membrane', (0.19, 0.205, 0.20))
EQUIP = material('Equipment_Enamel', (0.53, 0.57, 0.55), .25, .6)
DOOR = material('Entry_Teal', (0.065, 0.16, 0.155), .15, .55)
LAMP = material('Warm_Lamp', (0.95, 0.66, 0.25), .0, .4)

groups = {}
def meshgroup(name):
    return groups.setdefault(name, [[], [], []])

def box(group, center, size, mat, mapper=None):
    vertices, faces, indices = meshgroup(group)
    x,y,z = center
    a,b,c = (v*.5 for v in size)
    vv = [(x-a,y-b,z-c),(x+a,y-b,z-c),(x+a,y+b,z-c),(x-a,y+b,z-c),
          (x-a,y-b,z+c),(x+a,y-b,z+c),(x+a,y+b,z+c),(x-a,y+b,z+c)]
    start = len(vertices)
    vertices.extend([mapper(*v) for v in vv] if mapper else vv)
    faces.extend(tuple(start+i for i in f) for f in [(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)])
    indices.extend([mat]*6)

def rod(group, start, end, radius, mat, sides=8):
    vertices, faces, indices = meshgroup(group)
    start, end = Vector(start), Vector(end)
    axis = (end-start).normalized()
    u = axis.cross(Vector((0,0,1)) if abs(axis.z)<.95 else Vector((1,0,0))).normalized()
    v = axis.cross(u)
    off = len(vertices)
    for p in (start,end):
        for i in range(sides):
            q = p + radius*(math.cos(i*math.tau/sides)*u + math.sin(i*math.tau/sides)*v)
            vertices.append(tuple(q))
    faces.append(tuple(off+i for i in reversed(range(sides))))
    faces.append(tuple(off+sides+i for i in range(sides)))
    for i in range(sides):
        j=(i+1)%sides
        faces.append((off+i,off+j,off+sides+j,off+sides+i))
    indices.extend([mat]*(sides+2))

facades = [
    ('Front', W, lambda u,v,z:(u,-D/2-v,z), [-10.5,-7.1,-3.7,3.7,7.1,10.5]),
    ('Right', D, lambda u,v,z:(W/2+v,u,z), [-6.7,-3.35,0,3.35,6.7]),
    ('Rear', W, lambda u,v,z:(-u,D/2+v,z), [-10.5,-7,-3.5,0,3.5,7,10.5]),
    ('Left', D, lambda u,v,z:(-W/2-v,-u,z), [-6.7,-3.35,0,3.35,6.7]),
]
window_count = 0
def window(group, u, z, mapper, width=1.64, height=1.57, variant=0):
    global window_count
    window_count += 1
    box(group,(u,-.105,z),(width,.035,height),DARK,mapper)
    box(group,(u,-.078,z),(width-.15,.025,height-.14), GLASS2 if variant%4==0 else GLASS,mapper)
    for offset in (-width/2+.047,width/2-.047):
        box(group,(u+offset,.005,z),(.095,.17,height),FRAME,mapper)
    for offset in (-height/2+.047,height/2-.047):
        box(group,(u,.005,z+offset),(width,.17,.095),FRAME,mapper)
    box(group,(u+.19,.022,z),(.065,.15,height-.13),FRAME,mapper)
    box(group,(u,.022,z+.40),(width-.14,.15,.055),FRAME,mapper)
    # Projecting sill, simple pale lintel and side reveals.
    box(group,(u,.13,z-height/2-.08),(width+.28,.43,.13),TRIM,mapper)
    box(group,(u,.025,z+height/2+.10),(width+.27,.19,.14),TRIM,mapper)
    for dx in (-width/2-.065,width/2+.065):
        box(group,(u+dx,-.012,z),(.13,.22,height+.10),TRIM,mapper)

# Body cap and plinth; exterior panels contain actual shallow window recesses.
box('01_Plinth',(0,0,BASE/2),(W,D,BASE),BASEMAT)
box('01_Plinth',(0,0,BASE+.035),(W+.12,D+.12,.07),TRIM)
for name, length, mapper, bays in facades:
    for f in range(FLOORS):
        group = '02_'+name+'_Floor_'+str(f+1)
        z0=BASE+f*STOREY
        zwin=z0+1.29
        holes=[(u,1.78,zwin,1.71) for u in bays]
        if name=='Front':
            holes.append((0,2.30,z0+1.34,1.94 if f else 2.1))
        holes.sort()
        cursor=-length/2
        for i,(u,ww,zw,hh) in enumerate(holes):
            left,right=u-ww/2,u+ww/2
            wallmat=TERRA if ((f==0 and abs(u)>2) or (name!='Front' and f==2 and i%3==1)) else PLASTER
            if left>cursor:
                box(group,((cursor+left)/2,-.16,z0+STOREY/2),(left-cursor,.32,STOREY),wallmat,mapper)
            bottom,top=zw-hh/2,zw+hh/2
            if bottom>z0:
                box(group,(u,-.16,(z0+bottom)/2),(ww,.32,bottom-z0),wallmat,mapper)
            if top<z0+STOREY:
                box(group,(u,-.16,(top+z0+STOREY)/2),(ww,.32,z0+STOREY-top),wallmat,mapper)
            cursor=right
        if cursor<length/2:
            box(group,((cursor+length/2)/2,-.16,z0+STOREY/2),(length/2-cursor,.32,STOREY),PLASTER,mapper)
        for i,u in enumerate(bays):
            window('03_'+name+'_Windows_'+str(f+1),u,zwin,mapper,variant=f+i)
        if f:
            box('04_Floor_Bands_'+name,(0,.014,z0),(length,.045,.045),BASEMAT,mapper)
    # Panel joints restrained enough to read from city scale.
    for u in [(-length/2)+i*length/(len(bays)+1) for i in range(1,len(bays)+1)]:
        if name=='Front' and abs(u)<2: continue
        box('04_Panel_Joints_'+name,(u,.014,ROOF/2+.2),(.021,.018,ROOF-.45),BASEMAT,mapper)

front=facades[0][2]
# Central staircase bay, with terracotta flanks and continuous pale verticals.
for u in (-1.55,1.55):
    box('05_Stair_Bay',(u,.075,(ROOF+BASE)/2),(.65,.18,ROOF-BASE),TERRA,front)
for u in (-1.20,1.20):
    box('05_Stair_Bay',(u,.13,(ROOF+BASE)/2),(.15,.25,ROOF-BASE),TRIM,front)
for f in range(1,FLOORS):
    z=BASE+f*STOREY+1.34
    window('05_Stair_Glazing',0,z,front,2.12,1.94,f)
    box('05_Stair_Bay',(0,.05,BASE+f*STOREY+.17),(2.28,.22,.30),TRIM,front)

# Heavy flat cornice; an inset membrane and capped parapet.
box('06_Roof_Slab',(0,0,ROOF-.035),(W+.48,D+.48,.27),TRIM)
box('06_Roof_Membrane',(0,0,ROOF+.115),(W-.38,D-.38,.04),ROOFMAT)
for y in (-D/2+.10,D/2-.10):
    box('07_Parapet',(0,y,10.285),(W,.24,.37),PLASTER)
    box('07_Parapet',(0,y,10.465),(W+.12,.36,.07),TRIM)
for x in (-W/2+.10,W/2-.10):
    box('07_Parapet',(x,0,10.285),(.24,D,.37),PLASTER)
    box('07_Parapet',(x,0,10.465),(.36,D+.12,.07),TRIM)
# Metal roof perimeter safety rails set inward of the parapet.
for y in (-D/2+.48,D/2-.48):
    for z in (10.58,10.95):
        rod('08_Roof_Railings',(-W/2+.48,y,z),(W/2-.48,y,z),.026,METAL)
    for i in range(12):
        x=-W/2+.48+i*(W-.96)/11
        rod('08_Roof_Railings',(x,y,10.15),(x,y,10.98),.028,METAL)
for x in (-W/2+.48,W/2-.48):
    for z in (10.58,10.95):
        rod('08_Roof_Railings',(x,-D/2+.48,z),(x,D/2-.48,z),.026,METAL)
    for i in range(8):
        y=-D/2+.48+i*(D-.96)/7
        rod('08_Roof_Railings',(x,y,10.15),(x,y,10.98),.028,METAL)

# Modest rooftop stair/service head; no inside space or opening door.
box('09_Roof_Service_Head',(0,1.6,11.07),(5.2,4.2,1.86),PLASTER)
box('09_Roof_Service_Head',(0,1.6,12.04),(5.45,4.45,.16),TRIM)
box('09_Roof_Service_Head',(0,1.6,12.135),(5.1,4.1,.035),ROOFMAT)
box('09_Roof_Service_Head',(0,-.513,11.02),(1.0,.07,1.72),METAL)
for z in (10.42,10.51,10.60,11.45,11.54,11.63):
    box('09_Roof_Service_Head',(0,-.562,z),(.78,.045,.035),EQUIP)
for x,y,h in [(-7.8,3.7,1.25),(7.5,4.0,1.45),(7.6,-3.4,.95)]:
    box('10_Roof_Vents',(x,y,10.40),(.9,.9,.52),PLASTER)
    rod('10_Roof_Vents',(x,y,10.52),(x,y,10.52+h),.13,EQUIP,12)
    box('10_Roof_Vents',(x,y,10.55+h),(.45,.45,.08),METAL)
for x in (-5.8,5.8):
    box('10_Roof_Vents',(x,1.3,10.59),(1.7,1.1,.9),EQUIP)
    box('10_Roof_Vents',(x,1.3,11.065),(1.83,1.23,.10),METAL)
    for yy in (.88,1.02,1.16,1.30,1.44,1.58,1.72):
        box('10_Roof_Vents',(x,yy,11.125),(1.49,.055,.025),DARK)
# Access ladder on the service head.
for x in (1.60,2.12):
    rod('11_Roof_Ladder',(x,-.79,10.15),(x,-.79,12.72),.032,METAL)
    rod('11_Roof_Ladder',(x,-.79,12.72),(x,-.38,12.72),.032,METAL)
for i in range(10):
    z=10.30+i*.24
    rod('11_Roof_Ladder',(1.60,-.79,z),(2.12,-.79,z),.025,METAL)
rod('11_Antenna',(-1.1,2.4,12.15),(-1.1,2.4,13.45),.035,METAL)
rod('11_Antenna',(-1.75,2.4,13.1),(-.45,2.4,13.1),.024,METAL)
for x in (-1.6,-.6):
    box('11_Antenna',(x,2.4,13.12),(.11,.15,.48),EQUIP)

# Central entrance: three shallow risers, a landing and a restrained stone canopy.
for i in range(3):
    height=(i+1)*.15
    box('12_Entry_Steps',(0,-D/2-2.45+i*.32,height/2),(5.8, .64,height),TRIM)
box('12_Entry_Landing',(0,-D/2-.88,.225),(5.8,1.76,.45),TRIM)
box('13_Entry_Canopy',(0,-D/2-1.02,3.02),(6.35,2.40,.25),TRIM)
box('13_Entry_Canopy',(0,-D/2-1.02,3.17),(6.18,2.25,.07),ROOFMAT)
for x in (-2.65,2.65):
    box('13_Entry_Canopy',(x,-D/2-1.79,1.71),(.33,.33,2.52),TRIM)
    box('13_Entry_Canopy',(x,-D/2-1.79,.57),(.47,.47,.24),BASEMAT)
box('14_Entry_Doors',(0,-D/2+.05,1.49),(2.3,.20,2.10),DARK)
for x in (-.52,.52):
    box('14_Entry_Doors',(x,-D/2-.07,1.49),(1.01,.10,2.05),DOOR)
    box('14_Entry_Doors',(x,-D/2-.13,1.92),(.76,.025,.89),GLASS)
    box('14_Entry_Doors',(x,-D/2-.13,.92),(.75,.035,.60),METAL)
    hx=x+(.33 if x<0 else -.33)
    rod('14_Entry_Doors',(hx,-D/2-.22,1.25),(hx,-D/2-.22,1.56),.023,TRIM)
box('14_Entry_Doors',(0,-D/2-.15,2.73),(2.80,.14,.34),DOOR)
for x in (-1.89,1.89):
    box('15_Entry_Lights',(x,-D/2-.15,2.35),(.18,.27,.29),METAL)
    box('15_Entry_Lights',(x,-D/2-.30,2.35),(.12,.05,.20),LAMP)
    box('15_Entry_Lights',(x,-D/2-.11,1.51),(.34,.06,.44),TRIM)
for x in (-2.67,2.67):
    for y,z in [(-D/2-2.65,.15),(-D/2-1.60,.45),(-D/2-.5,.45)]:
        rod('16_Entry_Railings',(x,y,z),(x,y,z+.91),.028,METAL)
    rod('16_Entry_Railings',(x,-D/2-2.65,1.06),(x,-D/2-1.60,1.36),.034,METAL)
    rod('16_Entry_Railings',(x,-D/2-1.60,1.36),(x,-D/2-.5,1.36),.034,METAL)

# Downpipes and sparse AC units. Silhouette detail without production-level density.
for name,length,mapper,bays in facades:
    for u in (-length/2+.43,length/2-.43):
        rod('17_Downpipes',mapper(u,.21,.22),mapper(u,.21,ROOF-.17),.060,METAL)
        for z in (1.0,3.4,5.8,8.2):
            box('17_Downpipes',(u,.18,z),(.20,.18,.08),EQUIP,mapper)
    for idx,f in [(0,1),(len(bays)-1,2)]:
        u=bays[idx]+.88
        z=BASE+f*STOREY+.42
        box('18_AC_'+name,(u,.37,z),(.80,.48,.48),EQUIP,mapper)
        rod('18_AC_'+name,mapper(u-.13,.61,z),mapper(u-.13,.635,z),.172,DARK,16)
        for dx in (-.36,.30):
            box('18_AC_'+name,(u+dx,.36,z-.31),(.05,.55,.10),METAL,mapper)
        for j in range(4):
            box('18_AC_'+name,(u+.20,.625,z-.13+j*.085),(.19,.027,.024),METAL,mapper)

created=[]
for name,(vertices,faces,indices) in groups.items():
    mesh=bpy.data.meshes.new(PREFIX+name)
    mesh.from_pydata(vertices,[],faces)
    mesh.update()
    for mat in materials: mesh.materials.append(mat)
    for polygon,index in zip(mesh.polygons,indices): polygon.material_index=index
    obj=bpy.data.objects.new(PREFIX+name,mesh)
    coll.objects.link(obj)
    obj.parent=root
    obj['assembly']=name
    created.append(obj)

# Original test object is retained, outside the export collection.
test=bpy.data.objects.get('MCP_TestCube')
if test:
    archive=bpy.data.collections.get('MCP_Test_Archive') or bpy.data.collections.new('MCP_Test_Archive')
    if archive.name not in scene.collection.children: scene.collection.children.link(archive)
    for c in list(test.users_collection): c.objects.unlink(test)
    archive.objects.link(test)
    archive.hide_viewport=True
    archive.hide_render=True

bpy.context.view_layer.update()
for obj in bpy.context.selected_objects: obj.select_set(False)
root.select_set(True)
bpy.context.view_layer.objects.active=root
for area in bpy.context.screen.areas:
    if area.type=='VIEW_3D':
        space=area.spaces.active
        space.shading.type='SOLID'
        space.shading.light='STUDIO'
        space.shading.studiolight_rotate_z=.35
        space.shading.color_type='MATERIAL'
        space.shading.show_shadows=True
        space.shading.show_cavity=True
        space.shading.cavity_type='BOTH'
        space.shading.curvature_ridge_factor=1.25
        space.shading.curvature_valley_factor=1.05
        space.shading.background_type='WORLD'
        space.overlay.show_overlays=False
        region=space.region_3d
        direction=Vector((1.3,-1.8,1.12))
        region.view_rotation=direction.to_track_quat('Z','Y')
        region.view_distance=48
        region.view_location=(0,-.5,5.6)
        region.view_perspective='ORTHO'
        area.tag_redraw()
points=[obj.matrix_world@Vector(corner) for obj in created for corner in obj.bound_box]
low=[min(p[i] for p in points) for i in range(3)]
high=[max(p[i] for p in points) for i in range(3)]
after={n: (bpy.data.objects[n].as_pointer(),tuple(v for row in bpy.data.objects[n].matrix_world for v in row),bpy.data.objects[n].data.as_pointer()) for n in protected}
result={'status':'built','body_m':[W,D,10.5], 'total_bounds_min_m':low,'total_bounds_max_m':high,'total_dimensions_m':[high[i]-low[i] for i in range(3)],'storeys':FLOORS,'window_modules':window_count,'mesh_objects':len(created),'triangles':sum(len(p.vertices)-2 for o in created for p in o.data.polygons),'camera_light_unchanged':protected==after,'saved':False,'exported':False}
root['validation']=json.dumps(result)
