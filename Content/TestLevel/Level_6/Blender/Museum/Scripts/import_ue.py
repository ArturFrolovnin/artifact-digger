import unreal,json,traceback
from pathlib import Path
disk=Path('D:/UEProject/ArcheoDig/Content/TestLevel/Level_6/Blender/Museum')
base='/Game/TestLevel/Level_6/Blender/Museum'
try:
    options=unreal.FbxImportUI()
    options.automated_import_should_detect_type=False
    options.import_mesh=True;options.import_as_skeletal=False
    options.mesh_type_to_import=unreal.FBXImportType.FBXIT_STATIC_MESH
    options.original_import_type=unreal.FBXImportType.FBXIT_STATIC_MESH
    options.import_materials=False;options.import_textures=False;options.import_animations=False
    imp=options.static_mesh_import_data
    imp.combine_meshes=True;imp.import_uniform_scale=1.0
    imp.normal_import_method=unreal.FBXNormalImportMethod.FBXNIM_IMPORT_NORMALS
    task=unreal.AssetImportTask();task.filename=str(disk/'Source/SM_Museum_Blockout.fbx')
    task.destination_path=base;task.destination_name='SM_Museum_Blockout';task.automated=True;task.replace_existing=False;task.save=False;task.options=options;task.factory=unreal.FbxFactory()
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    mesh=unreal.load_asset(base+'/SM_Museum_Blockout');assert mesh
    manifest=json.loads((disk/'Materials/material_manifest.txt').read_text())
    assets=unreal.AssetToolsHelpers.get_asset_tools();lib=unreal.MaterialEditingLibrary
    mapped={}
    names={'Warm_Limestone.001':'Stone','Ivory_Cutstone':'Stone_Trim','Base_Sandstone':'Stone_Base','Charcoal_Slate':'Roof','Smoky_Teal_Glass':'Glass','Lantern_Blue_Glass':'Glass_Cupola','Walnut_Entry':'Wood','Aged_Bronze':'Metal','Banner_Ochre':'Metal_Gold','Museum_Deep_Blue':'Banner','Recess_Shadow':'Recess','Warm_Window_Reflection':'Glass_Warm','Entry_Lantern_Amber':'Lantern_Amber'}
    for source,p in manifest.items():
        name='MUS_'+names[source.removeprefix('Museum_')]
        material=assets.create_asset(name,base+'/Materials',unreal.Material,unreal.MaterialFactoryNew())
        material.set_editor_property('two_sided',True)
        color=lib.create_material_expression(material,unreal.MaterialExpressionConstant3Vector,-300,0)
        color.set_editor_property('constant',unreal.LinearColor(*p['color']))
        lib.connect_material_property(color,'',unreal.MaterialProperty.MP_BASE_COLOR)
        for prop,value,y in [(unreal.MaterialProperty.MP_ROUGHNESS,p['roughness'],150),(unreal.MaterialProperty.MP_METALLIC,p['metallic'],250)]:
            n=lib.create_material_expression(material,unreal.MaterialExpressionConstant,-300,y);n.set_editor_property('r',value);lib.connect_material_property(n,'',prop)
        lib.recompile_material(material);unreal.EditorAssetLibrary.save_loaded_asset(material)
        mapped[source.replace('.','_')]=material;mapped[source]=material
    slots=[]
    for i,slot in enumerate(mesh.static_materials):
        key=str(slot.material_slot_name);assert key in mapped,key
        mesh.set_material(i,mapped[key]);slots.append([key,mapped[key].get_path_name()])
    unreal.EditorAssetLibrary.save_loaded_asset(mesh)
    b=mesh.get_bounding_box()
    report={'asset':mesh.get_path_name(),'bounds_min':[b.min.x,b.min.y,b.min.z],'bounds_max':[b.max.x,b.max.y,b.max.z],'triangles':mesh.get_num_triangles(0),'materials':slots,'import_scale':imp.import_uniform_scale}
    (disk/'Source/ue_import_report.txt').write_text(json.dumps(report,indent=2))
except Exception:
    (disk/'Source/ue_import_error.txt').write_text(traceback.format_exc());raise


