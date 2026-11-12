"""Export existing Rudy source and independent hinged door on temporary copies."""
import bpy,json
from pathlib import Path
from mathutils import Matrix

out=Path(bpy.data.filepath).parent
assert out.name=='Source' and out.parent.name=='RudyPawnshop'
assert bpy.context.mode=='OBJECT'
collection=bpy.data.collections['BLD_RudyPawnshop']
main=[o for o in collection.all_objects if o.type in {'MESH','FONT'}]
jobs=[('SM_RudyPawnshop',main,Matrix.Identity(4))]
door=bpy.data.objects.get('RUDY_Door_Entrance_ROOT')
if door:
    door_objects=[o for o in door.children_recursive if o.type in {'MESH','FONT'}]
    assert not set(main).intersection(door_objects),'Door must not be duplicated in main mesh'
    jobs.append(('SM_RudyPawnshop_Door_Entrance',door_objects,door.matrix_world.inverted()))
selected=list(bpy.context.selected_objects);active=bpy.context.view_layer.objects.active
reports={}
try:
    for name,objects,frame in jobs:
        temporary=[]
        try:
            for o in bpy.context.selected_objects:o.select_set(False)
            for original in objects:
                copy=original.copy();copy.data=original.data.copy()
                collection.objects.link(copy);copy.parent=None
                copy.matrix_world=frame @ original.matrix_world
                temporary.append(copy);copy.select_set(True)
            bpy.context.view_layer.objects.active=temporary[0]
            bpy.ops.object.convert(target='MESH')
            points=[];materials=set();triangles=0
            for o in temporary:
                o.data.transform(o.matrix_world);o.matrix_world=Matrix.Identity(4);o.data.update()
                uv=o.data.uv_layers.active or o.data.uv_layers.new(name='UVMap')
                for face in o.data.polygons:
                    dominant=max(range(3),key=lambda i:abs(face.normal[i]))
                    axes=[i for i in range(3) if i!=dominant]
                    for index in face.loop_indices:
                        co=o.data.vertices[o.data.loops[index].vertex_index].co
                        uv.data[index].uv=(co[axes[0]],co[axes[1]])
                o.data.calc_loop_triangles();triangles+=len(o.data.loop_triangles)
                points.extend(tuple(v.co) for v in o.data.vertices)
                materials.update(m.name for m in o.data.materials if m)
            bpy.ops.export_scene.fbx(filepath=str(out/(name+'.fbx')),use_selection=True,
                object_types={'MESH'},global_scale=1.0,apply_unit_scale=True,
                apply_scale_options='FBX_SCALE_NONE',axis_forward='-Y',axis_up='Z',
                use_space_transform=True,bake_space_transform=False,use_mesh_modifiers=True,
                mesh_smooth_type='FACE',use_triangles=True,bake_anim=False,path_mode='AUTO')
            reports[name]={'objects':len(objects),'triangles':triangles,'materials':sorted(materials),
                'min_m':[min(p[i] for p in points) for i in range(3)],
                'max_m':[max(p[i] for p in points) for i in range(3)]}
        finally:
            for o in temporary:
                data=o.data;bpy.data.objects.remove(o,do_unlink=True)
                if data.users==0:bpy.data.meshes.remove(data)
finally:
    for o in selected:o.select_set(True)
    bpy.context.view_layer.objects.active=active
log=out.parents[4]/'Saved/BlenderToUE'
assert log.is_dir()
(log/'rudypawnshop_export.json').write_text(json.dumps({'assets':reports},indent=2))
result={'exports':reports}
