import bpy
result={o.name:{'up':sum(p.normal.z>.1 for p in o.data.polygons),'down':sum(p.normal.z<-.1 for p in o.data.polygons)} for o in bpy.data.collections['BLD_Dormitory'].objects if o.name.startswith(('DORM_25','DORM_26','DORM_32'))}
