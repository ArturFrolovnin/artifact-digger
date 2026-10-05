import unreal, json, traceback
from pathlib import Path
disk=Path('D:/UEProject/ArcheoDig/Content/TestLevel/Level_6/Blender/CarDealership')
base='/Game/TestLevel/Level_6/Blender/CarDealership'
try:
    assert not unreal.EditorAssetLibrary.does_asset_exist(base+'/SM_CarDealership_Blockout')
    options=unreal.FbxImportUI()
    options.automated_import_should_detect_type=False
    options.import_mesh=True; options.import_as_skeletal=False
    options.mesh_type_to_import=unreal.FBXImportType.FBXIT_STATIC_MESH
    options.original_import_type=unreal.FBXImportType.FBXIT_STATIC_MESH
    options.import_materials=False; options.import_textures=False; options.import_animations=False
    imp=options.static_mesh_import_data
    imp.combine_meshes=True; imp.import_uniform_scale=1.0
    imp.normal_import_method=unreal.FBXNormalImportMethod.FBXNIM_IMPORT_NORMALS
    task=unreal.AssetImportTask(); task.filename=str(disk/'Source/SM_CarDealership_Blockout.fbx')
    task.destination_path=base; task.destination_name='SM_CarDealership_Blockout'; task.automated=True
    task.replace_existing=False; task.save=False; task.options=options; task.factory=unreal.FbxFactory()
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    mesh=unreal.load_asset(base+'/SM_CarDealership_Blockout'); assert mesh
    manifest=json.loads((disk/'Source/material_manifest.txt').read_text())
    assets=unreal.AssetToolsHelpers.get_asset_tools(); lib=unreal.MaterialEditingLibrary
    names={'warm ivory panels':'Wall','graphite powdercoat':'Metal','vermilion accent':'Sign','pale concrete':'Service_Concrete','roof membrane':'Roof','sectional door metal':'Door','rubber':'Rubber','blue car placeholder':'Display_Blue','showroom clear glass':'Glass','car glazing':'Glass_Dark','warm lamp':'Lamp'}
    mapped={}
    for source,p in manifest.items():
        name='CAR_'+names[source.removeprefix('CD | ')]
        material=assets.create_asset(name,base+'/Materials',unreal.Material,unreal.MaterialFactoryNew())
        material.set_editor_property('two_sided',True)
        if name == 'CAR_Glass':
            material.set_editor_property('blend_mode',unreal.BlendMode.BLEND_TRANSLUCENT)
            material.set_editor_property('translucency_lighting_mode',unreal.TranslucencyLightingMode.TLM_SURFACE)
            opacity=lib.create_material_expression(material,unreal.MaterialExpressionConstant,-300,350)
            opacity.set_editor_property('r',.16)
            lib.connect_material_property(opacity,'',unreal.MaterialProperty.MP_OPACITY)
        if name == 'CAR_Lamp':
            emission=lib.create_material_expression(material,unreal.MaterialExpressionConstant3Vector,-300,450)
            emission.set_editor_property('constant',unreal.LinearColor(1.9,1.6,1.,1.))
            lib.connect_material_property(emission,'',unreal.MaterialProperty.MP_EMISSIVE_COLOR)
        color=lib.create_material_expression(material,unreal.MaterialExpressionConstant3Vector,-300,0)
        color.set_editor_property('constant',unreal.LinearColor(*p['color']))
        lib.connect_material_property(color,'',unreal.MaterialProperty.MP_BASE_COLOR)
        for prop,value,y in [(unreal.MaterialProperty.MP_ROUGHNESS,p['roughness'],150),(unreal.MaterialProperty.MP_METALLIC,p['metallic'],250)]:
            n=lib.create_material_expression(material,unreal.MaterialExpressionConstant,-300,y)
            n.set_editor_property('r',value); lib.connect_material_property(n,'',prop)
        lib.recompile_material(material); unreal.EditorAssetLibrary.save_loaded_asset(material)
        mapped[source]=material
    slots=[]
    for i,slot in enumerate(mesh.static_materials):
        key=str(slot.material_slot_name); assert key in mapped,key
        mesh.set_material(i,mapped[key]); slots.append([key,mapped[key].get_path_name()])
    unreal.EditorAssetLibrary.save_loaded_asset(mesh)
    b=mesh.get_bounding_box()
    def v(p):return [p.x,p.y,p.z]
    report={'asset':mesh.get_path_name(),'bounds_min':v(b.min),'bounds_max':v(b.max),'dimensions_cm':v(b.max-b.min),'triangles':mesh.get_num_triangles(0),'materials':slots,'import_scale':imp.import_uniform_scale}
    expected=json.loads((disk/'Source/export_validation.txt').read_text())['dimensions_m']
    assert all(abs(report['dimensions_cm'][i]-expected[i]*100)<.1 for i in range(3)),report
    assert abs(b.min.z)<.01
    (disk/'Source/ue_import_report.txt').write_text(json.dumps(report,indent=2))
except Exception:
    (disk/'Source/ue_import_error.txt').write_text(traceback.format_exc()); raise

