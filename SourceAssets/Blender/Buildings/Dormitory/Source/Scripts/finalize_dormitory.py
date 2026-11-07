import bpy, bmesh, json, math
from mathutils import Vector
from pathlib import Path
coll=bpy.data.collections['DORMITORY_Blockout']
root=bpy.data.objects['DORMITORY_ROOT__ground_pivot']
# Normalize outward winding, including reflected facade coordinate mappings.
for obj in coll.objects:
    if obj.type!='MESH': continue
    bm=bmesh.new()
    bm.from_mesh(obj.data)
    bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
    bm.to_mesh(obj.data)
    bm.free()
    obj.data.update()
# Small campus plaque, converted to mesh with the same ground-level origin.
if not bpy.data.objects.get('DORM_19_Entrance_Sign'):
    curve=bpy.data.curves.new('DORM_Campus_Plaque','FONT')
    curve.body='CAMPUS  /  01'
    curve.align_x='CENTER'
    curve.align_y='CENTER'
    curve.size=.17
    curve.extrude=.002
    curve.resolution_u=2
    obj=bpy.data.objects.new('DORM_19_Entrance_Sign',curve)
    coll.objects.link(obj)
    obj.location=(0,-9.233,2.73)
    obj.rotation_euler=(math.pi/2,0,0)
    curve.materials.append(bpy.data.materials['DORM_Pale_Stone'])
    for o in bpy.context.selected_objects: o.select_set(False)
    obj.select_set(True)
    bpy.context.view_layer.objects.active=obj
    bpy.ops.object.convert(target='MESH')
    obj=bpy.context.object
    obj.data.transform(obj.matrix_world)
    obj.matrix_world.identity()
    obj.parent=root
    obj['assembly']='Entrance lettering'
for obj in bpy.context.selected_objects: obj.select_set(False)
root.select_set(True)
bpy.context.view_layer.objects.active=root
bpy.context.view_layer.update()
meshes=[o for o in coll.objects if o.type=='MESH']
def bounds(objects):
    deps=bpy.context.evaluated_depsgraph_get()
    points=[o.matrix_world@Vector(c) for obj in objects for o in [obj.evaluated_get(deps)] for c in o.bound_box]
    lo=[min(p[i] for p in points) for i in range(3)]
    hi=[max(p[i] for p in points) for i in range(3)]
    return {'min_m':lo,'max_m':hi,'dimensions_m':[hi[i]-lo[i] for i in range(3)]}
body=bounds([o for o in meshes if o.name.startswith('DORM_02_')]+[o for o in meshes if o.name=='DORM_01_Plinth'])
wall=bounds([o for o in meshes if o.name.startswith('DORM_02_')])
parapet=bounds([bpy.data.objects['DORM_07_Parapet']])
report={'unit_system':bpy.context.scene.unit_settings.system,'metres_per_blender_unit':bpy.context.scene.unit_settings.scale_length,'body_wall_footprint_measured_m':wall['dimensions_m'][:2], 'parapet_top_measured_m':parapet['max_m'][2], 'total_evaluated_bounds':bounds(meshes), 'storeys':4,'floor_to_floor_m':2.4,'mesh_objects':len(meshes),'triangles':sum(len(p.vertices)-2 for o in meshes for p in o.data.polygons),'all_mesh_origins_at_ground_centre':all(o.location.length<1e-6 for o in meshes),'all_scales_unit':all(all(abs(v-1)<1e-6 for v in o.scale) for o in meshes),'zero_area_faces':sum(p.area<1e-10 for o in meshes for p in o.data.polygons),'nonfinite_vertices':sum(not all(math.isfinite(v) for v in vert.co) for o in meshes for vert in o.data.vertices),'file_saved':False,'ue_exported':False}
root['validation']=json.dumps(report)
Path('D:/UEProject/ArcheoDig/Saved/BlenderDormitory/validation.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
for area in bpy.context.screen.areas:
    if area.type=='VIEW_3D':
        s=area.spaces.active
        s.show_gizmo=False
        s.shading.background_type='VIEWPORT'
        s.shading.background_color=(.19,.21,.24)
        s.shading.light='STUDIO'
        s.shading.show_shadows=True
        s.shading.show_cavity=True
        s.shading.cavity_type='BOTH'
        s.shading.curvature_ridge_factor=1.05
        s.shading.curvature_valley_factor=.85
        s.region_3d.view_rotation=Vector((1.2,-2,1.0)).to_track_quat('Z','Y')
        s.region_3d.view_distance=42
        s.region_3d.view_location=(0,-.4,5.7)
        s.region_3d.view_perspective='ORTHO'
        area.tag_redraw()
result=report
