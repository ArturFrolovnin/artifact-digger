"""Standalone metre-scale prototype; run in Blender. Rebuilds the current file."""
import bpy
import math
import json
from pathlib import Path
from mathutils import Vector, Matrix

BASE = Path('D:/UEProject/ArcheoDig/Content/TestLevel/Level_6/Blender/CarDealership')
bpy.ops.wm.read_homefile(use_empty=True, use_factory_startup=True)
bpy.context.preferences.filepaths.save_version = 0
scene = bpy.context.scene
scene.name = 'CarDealership_Blockout'
scene.unit_settings.system = 'METRIC'
scene.unit_settings.scale_length = 1
assembly = bpy.data.collections.new('BLD_CarDealership')
scene.collection.children.link(assembly)
root = bpy.data.objects.new('CarDealership_ROOT', None)
assembly.objects.link(root)
root.empty_display_size = 1.5
root['design_status'] = 'Size test / not locked; independent new geometry'
root['body_footprint_m'] = '18 x 24'
root['front_direction'] = '-Y; service doors +X'
groups = {}
for name in ['Walls', 'Roof', 'ShowroomGlass', 'Entrance', 'ServiceBay', 'GarageDoors', 'Trim', 'Signs', 'Props']:
    col = bpy.data.collections.new(name)
    assembly.children.link(col)
    group = bpy.data.objects.new(name, None)
    col.objects.link(group)
    group.parent = root
    groups[name] = (col, group)
presentation = bpy.data.collections.new('Presentation_NOT_EXPORT')
scene.collection.children.link(presentation)

def material(name, color, rough=.5, metal=0):
    m = bpy.data.materials.new(name)
    m.diffuse_color = (*color, 1)
    m.use_nodes = True
    p = next(n for n in m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
    p.inputs['Base Color'].default_value = (*color, 1)
    p.inputs['Roughness'].default_value = rough
    p.inputs['Metallic'].default_value = metal
    return m

ivory = material('CD | warm ivory panels', (.76,.72,.62))
dark = material('CD | graphite powdercoat', (.065,.085,.095), .32, .45)
red = material('CD | vermilion accent', (.65,.055,.025), .35, .25)
floor = material('CD | pale concrete', (.48,.5,.49), .78)
roofmat = material('CD | roof membrane', (.15,.18,.19), .8)
door = material('CD | sectional door metal', (.29,.34,.35), .42, .4)
rubber = material('CD | rubber', (.025,.03,.035), .85)
blue = material('CD | blue car placeholder', (.035,.21,.38), .27,.4)
glass = material('CD | showroom clear glass', (.58,.79,.85), .08)
p = next(n for n in glass.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
p.inputs['Transmission Weight'].default_value = 1
p.inputs['IOR'].default_value = 1.45
carwindow = material('CD | car glazing', (.045,.09,.12), .18,.4)
lamp = material('CD | warm lamp', (.9,.79,.52), .4)
p = next(n for n in lamp.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
p.inputs['Emission Color'].default_value = (.95,.8,.5,1)
p.inputs['Emission Strength'].default_value = 2

def link(obj, group):
    for c in list(obj.users_collection):
        c.objects.unlink(obj)
    col, parent = groups[group] if group else (presentation, None)
    col.objects.link(obj)
    obj.parent = parent
    return obj

def box(name, loc, size, mat, group, bevel=.025):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
    obj = bpy.context.view_layer.objects.active
    obj.name = name
    obj.data.transform(Matrix.Diagonal((*size, 1)))
    link(obj, group)
    obj.data.materials.append(mat)
    if bevel:
        mod = obj.modifiers.new('Soft manufactured edges', 'BEVEL')
        mod.width = bevel
        mod.segments = 2
    return obj

def text(name, body, loc, size, mat, side=False):
    curve = bpy.data.curves.new(name, 'FONT')
    curve.body = body
    curve.align_x = 'CENTER'
    curve.size = size
    curve.extrude = .012
    curve.bevel_depth = .004
    obj = bpy.data.objects.new(name, curve)
    groups['Signs'][0].objects.link(obj)
    obj.parent = groups['Signs'][1]
    obj.location = loc
    obj.rotation_euler = (math.pi/2, 0, math.pi/2 if side else 0)
    curve.materials.append(mat)
    return obj

# Body: a glazed 18 x 11 m showroom and a lower 18 x 13 m workshop.
box('Foundation / exact body footprint 18x24', (0,0,.12), (18,24,.24), floor, 'Walls')
box('Showroom display floor', (0,-6.5,.27), (17.5,10.5,.06), ivory, 'Walls')
box('Workshop rear wall', (0,11.84,2.68), (18,.32,4.88), ivory, 'ServiceBay')
box('Workshop west wall', (-8.84,5.5,2.68), (.32,13,4.88), ivory, 'ServiceBay')
box('Showroom backdrop / service partition', (0,-.85,2.65), (17.5,.25,4.7), ivory, 'Walls')
box('Workshop east header', (8.84,5.5,4.67), (.32,13,.9), ivory, 'ServiceBay')
for a,b in [(-1,.7),(4.9,6.3),(10.5,12)]:
    box('Service bay structural pier', (8.84,(a+b)/2,2.23), (.32,b-a,3.98), ivory,'ServiceBay')

# Broad glazed front, central double doors, and wrapped corner windows.
for x in [-8.8,-5.35,-1.9,1.9,5.35,8.8]:
    box('Front mullion', (x,-11.84,2.63), (.13,.18,4.72), dark, 'ShowroomGlass', .01)
for a,b in [(-8.8,-5.35),(-5.35,-1.9),(1.9,5.35),(5.35,8.8)]:
    box('Full height showroom pane', ((a+b)/2,-11.84,2.7), (b-a-.13,.035,4.36), glass,'ShowroomGlass',0)
    box('Display sill', ((a+b)/2,-11.84,.4), (b-a,.28,.28), ivory,'Trim')
for z in [.53,4.91]:
    box('Continuous front glazing rail', (0,-11.84,z), (17.75,.18,.11), dark,'ShowroomGlass',.008)
for x in [-8.84,8.84]:
    for y in [-11.8,-8.2,-4.6,-1.1]:
        box('Side mullion', (x,y,2.63), (.18,.13,4.72), dark,'ShowroomGlass',.01)
    for a,b in [(-11.8,-8.2),(-8.2,-4.6),(-4.6,-1.1)]:
        box('Side showroom pane', (x,(a+b)/2,2.7), (.035,b-a-.13,4.36), glass,'ShowroomGlass',0)
    for z in [.4,4.91]:
        box('Side glazing rail', (x,-6.45,z), (.23,10.8,.16), dark,'ShowroomGlass',.01)
for x in [-8.82,8.82]:
    box('Showroom corner pier', (x,-11.82,2.64), (.36,.36,4.8), ivory,'Walls')
box('Front panel fascia', (0,-11.82,5.51), (18,.36,1.18), ivory,'Walls')
for x in [-8.82,8.82]:
    box('Side panel fascia', (x,-6.5,5.51), (.36,11,1.18), ivory,'Walls')
for x in [-6,-3,3,6]:
    box('Front panel reveal', (x,-12.005,5.53), (.018,.008,1.05), dark,'Trim',0)
box('Showroom flat roof', (0,-6.5,5.94), (18,11,.24), roofmat,'Roof')
box('Showroom front coping', (0,-11.93,6.13), (18.25,.34,.2), dark,'Roof')
for x in [-9.02,9.02]:
    box('Showroom side coping', (x,-6.48,6.13), (.25,11.25,.2), dark,'Roof')
box('Showroom rear coping', (0,-.98,6.13), (18.25,.25,.2), dark,'Roof')
box('Workshop roof', (0,5.5,5.12), (18,13,.22), roofmat,'Roof')
for x in [-8.9,8.9]:
    box('Workshop parapet', (x,5.5,5.33), (.2,13,.35), ivory,'Roof')
    box('Workshop coping', (x,5.5,5.55), (.32,13.25,.14), dark,'Roof')
box('Rear parapet', (0,11.9,5.33), (18,.2,.35), ivory,'Roof')
box('Rear coping', (0,11.9,5.55), (18.2,.32,.14), dark,'Roof')

# Readable centred sign tower, shallow entrance canopy, human-scale double doors.
box('Sign feature panel', (0,-11.78,6.09), (7.6,.55,2.1), ivory,'Signs')
box('Sign crown', (0,-11.78,7.22), (7.85,.72,.16), dark,'Trim')
box('Entry canopy', (0,-12.25,3.58), (4.9,1.65,.24), dark,'Entrance')
box('Canopy red leading edge', (0,-13.085,3.6), (4.9,.04,.09), red,'Trim',.008)
for x in [-1.8,0,1.8]:
    box('Entry door jamb', (x,-11.96,1.72), (.105,.15,2.86), dark,'Entrance',.01)
for x in [-.9,.9]:
    box('Entry glass door', (x,-11.96,1.75), (1.66,.045,2.68), glass,'Entrance',0)
    box('Door kick plate', (x,-11.99,.47), (1.68,.08,.25), dark,'Entrance')
for x in [-.18,.18]:
    box('Door pull', (x,-12.09,1.65), (.035,.055,.65), door,'Entrance',.015)
box('Entry transom', (0,-11.84,4.1), (3.67,.035,1.51), glass,'Entrance',0)
box('Entry horizontal frame', (0,-11.96,3.15), (3.7,.16,.12), dark,'Entrance')
box('Entry threshold', (0,-12,.13), (3.8,.6,.26), floor,'Entrance')
text('CITY lettering', 'CITY', (-1.97,-12.075,5.53), .82,dark)
text('MOTORS lettering', 'MOTORS', (1.19,-12.075,5.53), .82,red)
text('Showroom subtitle', 'SHOWROOM  /  SALES & SERVICE', (0,-12.078,5.17), .19,dark)
# A small editable curve evokes the reference's car-roof emblem.
cu=bpy.data.curves.new('Car silhouette emblem','CURVE'); cu.dimensions='3D'; cu.bevel_depth=.035; cu.bevel_resolution=2
sp=cu.splines.new('BEZIER'); sp.bezier_points.add(6)
for bp,co in zip(sp.bezier_points,[(-2,-12.085,6.51),(-1.3,-12.085,6.66),(-.6,-12.085,6.95),(.2,-12.085,7),(.9,-12.085,6.68),(1.5,-12.085,6.56),(2,-12.085,6.5)]):
    bp.co=co; bp.handle_left_type='AUTO'; bp.handle_right_type='AUTO'
ob=bpy.data.objects.new('Red car roof emblem',cu); groups['Signs'][0].objects.link(ob); ob.parent=groups['Signs'][1]; cu.materials.append(red)

# Two 4.2 m wide, 3.9 m high side garage doors. No solid wall behind them.
for n,y in enumerate([2.8,8.4],1):
    box(f'Garage {n} dark recess', (8.79,y,2.22), (.12,4.22,3.96), dark,'GarageDoors')
    for k in range(8):
        box(f'Garage {n} sectional leaf {k+1}', (8.89,y,.49+k*.47), (.12,4.02,.445), door,'GarageDoors',.012)
    for yy in [y-1.25,y,y+1.25]:
        box(f'Garage {n} window surround', (8.965,yy,2.37), (.065,.88,.42),dark,'GarageDoors')
        box(f'Garage {n} vision panel', (9.005,yy,2.37), (.02,.74,.29),carwindow,'GarageDoors',.01)
    for yy in [y-2.16,y+2.16]:
        box(f'Garage {n} frame', (9.015,yy,2.27), (.19,.14,4.05),dark,'GarageDoors')
    box(f'Garage {n} lintel', (9.015,y,4.27), (.2,4.45,.16),dark,'GarageDoors')
    text(f'Bay {n} number', f'0{n}', (9.02,y,4.56),.35,red,True)
    box(f'Garage {n} task lamp', (9.08,y,4.94),(.25,.65,.13),dark,'Props')
text('Service lettering', 'SERVICE', (9.04,5.5,5.05),.32,dark,True)

# Small enclosed technical room within the rear workshop footprint.
box('Technical room partition', (-3.8,9.6,1.65), (.16,4.3,2.82), ivory,'ServiceBay')
box('Technical room front', (-6.35,7.45,1.65), (5.1,.16,2.82), ivory,'ServiceBay')
box('Rear staff door frame', (-6.2,12.035,1.44), (1.35,.12,2.4),dark,'ServiceBay')
box('Rear staff door', (-6.2,12.11,1.44), (1.16,.06,2.22),door,'ServiceBay')
box('Rear staff canopy', (-6.2,12.35,2.85), (2.0,1.1,.12),dark,'ServiceBay')
box('Single rooftop HVAC curb', (-4,7.8,5.43), (2.65,2.0,.4),dark,'Roof')
box('Single rooftop HVAC', (-4,7.8,5.99), (2.4,1.75,.82),door,'Roof')
for k in range(6):
    box('HVAC louvre', (-4,6.91,5.69+k*.11), (2.15,.04,.035),dark,'Roof',.006)

# Deliberately simple display props and two vehicle scale placeholders.
box('Reception desk', (0,-2.1,.88), (3.4,.8,1.16),ivory,'Props')
box('Reception top', (0,-2.1,1.5), (3.55,.88,.09),dark,'Props')
text('Interior brand wall', 'CITY MOTORS', (0,-1.0,3.3),.55,dark)
for x in [-5.0,5.0]:
    box('Display accent backdrop', (x,-1.03,2.4), (1.1,.08,3.7),red,'Props')
for i,(x,y,paint) in enumerate([(-4.8,-7.9,red),(4.8,-7.9,blue)],1):
    box(f'Car {i} display pad', (x,y,.34), (3.3,5.7,.08),floor,'Props')
    box(f'Car {i} placeholder body', (x,y,1.02), (1.84,4.25,.77),paint,'Props',.18)
    box(f'Car {i} placeholder cabin', (x,y+.2,1.65), (1.56,2.12,.68),carwindow,'Props',.24)
    box(f'Car {i} roof', (x,y+.27,2.0), (1.46,1.65,.08),paint,'Props',.04)
    for dx in [-.9,.9]:
        for dy in [-1.35,1.35]:
            bpy.ops.mesh.primitive_cylinder_add(vertices=16, radius=.36, depth=.2, location=(x+dx,y+dy,.74), rotation=(0,math.pi/2,0))
            ob=bpy.context.view_layer.objects.active; ob.name=f'Car {i} wheel'; link(ob,'Props'); ob.data.materials.append(rubber)
            ob.data.transform(ob.rotation_euler.to_matrix().to_4x4())
            ob.rotation_euler=(0,0,0)
    for dx in [-.58,.58]:
        box(f'Car {i} headlamp', (x+dx,y-2.14,1.08), (.42,.045,.17),lamp,'Props',.03)
for x in [-5.5,0,5.5]:
    for y in [-8.5,-3.5]:
        box('Showroom ceiling panel', (x,y,5.79), (1.8,.7,.025),lamp,'Props',.015)

# Simple neutral presentation setup, isolated from the architecture.
box('Preview ground - not architecture', (0,0,-.15),(200,200,.2),material('CD | preview ground',(.21,.26,.28)),None,0)
world=bpy.data.worlds.new('CD neutral world'); scene.world=world; world.use_nodes=True
next(n for n in world.node_tree.nodes if n.type == 'BACKGROUND').inputs[0].default_value=(.65,.76,.88,1)
next(n for n in world.node_tree.nodes if n.type == 'BACKGROUND').inputs[1].default_value=.4
def light(name,loc,energy,size,target):
    d=bpy.data.lights.new(name,'AREA'); d.energy=energy; d.shape='DISK'; d.size=size
    o=bpy.data.objects.new(name,d); presentation.objects.link(o); o.location=loc
    o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler()
light('Preview key',(5,-16,25),4500,14,(0,0,0))
light('Showroom soft fill',(0,-6,5.5),650,8,(0,-6,0))
sun=bpy.data.lights.new('Preview sun','SUN'); sun.energy=2; sun.angle=.15
ob=bpy.data.objects.new('Preview sun',sun); presentation.objects.link(ob); ob.rotation_euler=(.5,-.4,-.5)
cam=bpy.data.cameras.new('Preview camera'); ob=bpy.data.objects.new('Preview camera',cam); presentation.objects.link(ob)
ob.location=(34,-43,27); ob.rotation_euler=(Vector((0,0,2.4))-ob.location).to_track_quat('-Z','Y').to_euler()
cam.type='ORTHO'; cam.ortho_scale=37; scene.camera=ob
scene.render.engine='CYCLES'; scene.cycles.samples=32; scene.cycles.use_denoising=True
scene.render.resolution_x=1400; scene.render.resolution_y=1100; scene.render.resolution_percentage=100
scene.view_settings.view_transform='AgX'
for area in [a for screen in bpy.data.screens for a in screen.areas]:
    if area.type=='VIEW_3D':
        area.spaces.active.region_3d.view_distance=39
        area.spaces.active.region_3d.view_location=(0,0,2.5)
        area.spaces.active.region_3d.view_rotation=ob.rotation_euler.to_quaternion()
        area.spaces.active.shading.type='MATERIAL'
        area.spaces.active.overlay.show_extras=False
bpy.ops.object.select_all(action='DESELECT')
root.select_set(True); bpy.context.view_layer.objects.active=root
bpy.context.view_layer.update()
pts=[o.matrix_world@Vector(v) for o in assembly.all_objects if o.type=='MESH' for v in o.bound_box]
report={'body_footprint_m':[18,24], 'bounds_m':[[min(p[i] for p in pts),max(p[i] for p in pts)] for i in range(3)], 'root_location':list(root.location),'root_scale':list(root.scale),'assembly_object_count':len(assembly.all_objects),'non_unit_scale':[o.name for o in assembly.all_objects if any(abs(s-1)>1e-6 for s in o.scale)],'unparented':[o.name for o in assembly.all_objects if o!=root and o not in root.children_recursive],'presentation_in_assembly':[o.name for o in assembly.all_objects if o.type in {'CAMERA','LIGHT'}],'garage_door_count':2,'dimensions_locked':False}
assert abs(report['bounds_m'][2][0])<1e-5
assert not report['non_unit_scale'] and not report['unparented'] and not report['presentation_in_assembly']
(BASE/'Source').mkdir(parents=True,exist_ok=True)
(BASE/'Previews').mkdir(exist_ok=True)
(BASE/'Source'/'validation.txt').write_text(json.dumps(report,indent=2),encoding='utf-8')
scene.render.filepath=str(BASE/'Previews'/'CarDealership_Perspective.png')
bpy.ops.wm.save_as_mainfile(filepath=str(BASE/'Source'/'CarDealership_Blockout.blend'))
print(json.dumps(report))
