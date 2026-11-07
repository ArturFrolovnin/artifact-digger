import bpy
from mathutils import Vector
for a in bpy.context.screen.areas:
    if a.type=='VIEW_3D':
        a.spaces.active.region_3d.view_rotation=Vector((-1.25,1.8,1.2)).to_track_quat('Z','Y')
        a.tag_redraw()
result={'view':'rear_left'}
