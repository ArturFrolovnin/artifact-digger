import bpy
from mathutils import Vector
for a in bpy.context.screen.areas:
    if a.type=='VIEW_3D':
        a.spaces.active.region_3d.view_rotation=Vector((1.3,-2,1.15)).to_track_quat('Z','Y')
        a.tag_redraw()
result={'view':'front','collection':'BLD_Dormitory','root':'Dormitory_ROOT'}
