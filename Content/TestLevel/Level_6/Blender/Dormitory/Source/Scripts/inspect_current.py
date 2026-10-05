import bpy
result={'collections':[c.name for c in bpy.data.collections], 'objects':[(o.name,o.type) for o in bpy.context.scene.objects if o.name.startswith(('DORM','Dormitory'))]}
