import json

BASE='/Game/TestLevel/Level_6/Blender/ConspiracyHouse/'
DISK='D:/UEProject/ArcheoDig/Content/TestLevel/Level_6/Blender/ConspiracyHouse/Source/'
def read(name):
 return json.loads(execute_tool('editor_toolset.toolsets.asset.AssetTools.read_file',json.dumps({'file_path':DISK+name}))['returnValue'])
def write(name,data):
 execute_tool('editor_toolset.toolsets.asset.AssetTools.write_file',json.dumps({'file_path':DISK+name,'content':json.dumps(data,indent=2)}))
def sm(method,mesh,**kwargs):
 return execute_tool('editor_toolset.toolsets.static_mesh.StaticMeshTools.'+method,json.dumps(dict({'mesh':mesh},**kwargs)))['returnValue']
def props(instance,keys):
 return json.loads(execute_tool('editor_toolset.toolsets.object.ObjectTools.get_properties',json.dumps({'instance':instance,'properties':keys}))['returnValue'])
def param(instance,name,kind):
 return execute_tool('editor_toolset.toolsets.material_instance.MaterialInstanceTools.get_'+kind+'_parameter',json.dumps({'instance':instance,'name':name}))['returnValue']
def assets():
 return execute_tool('editor_toolset.toolsets.asset.AssetTools.find_assets',json.dumps({'folder_path':BASE,'name':''}))['returnValue']
def save(paths):
 return execute_tool('editor_toolset.toolsets.asset.AssetTools.save_assets',json.dumps({'asset_paths':paths}))['returnValue']
def dirty(path):
 return execute_tool('editor_toolset.toolsets.asset.AssetTools.is_dirty',json.dumps({'asset_path':path}))['returnValue']
def run():
 source=read('export_validation.txt')
 manifest=read('material_manifest.txt')
 rows={}
 for key,expected in source['groups'].items():
  name='SM_ConspiracyHouse_'+key
  mesh={'refPath':BASE+name+'.'+name}
  b=sm('get_bounds',mesh)
  lo=expected['min_m']; hi=expected['max_m']
  elo=[lo[0]*100,-hi[1]*100,lo[2]*100]
  ehi=[hi[0]*100,-lo[1]*100,hi[2]*100]
  error=max([abs(b['min'][a]-elo[i]) for i,a in enumerate('xyz')]+[abs(b['max'][a]-ehi[i]) for i,a in enumerate('xyz')])
  assert error<0.001,(key,error)
  tri=sm('get_triangle_count',mesh)
  assert tri==expected['triangles'],(key,tri,expected['triangles'])
  slots=sm('get_material_slots',mesh)
  for slot in slots:
   assigned=sm('get_material',mesh,slot_name=slot)['refPath']
   assert assigned==BASE+'Materials/CH_'+slot+'.CH_'+slot,assigned
  refs=props(mesh,['assetImportData','bodySetup'])
  imp=props(refs['assetImportData'],['importUniformScale','normalImportMethod','bCombineMeshes'])
  assert imp['importUniformScale']==1 and imp['normalImportMethod']=='FBXNIM_ImportNormals' and imp['bCombineMeshes']
  collision=props(refs['bodySetup'],['collisionTraceFlag'])
  assert collision['collisionTraceFlag']=='CTF_UseComplexAsSimple'
  assert sm('get_lod_count',mesh)==1
  assert not sm('is_nanite_enabled',mesh)
  rows[key]={'asset':mesh['refPath'],'bounds_cm':b,'max_bound_error_cm':error,'dimensions_m':expected['dimensions_m'],'triangles':tri,'materials':slots,'import':imp,'collision':collision}
 for name,p in manifest.items():
  i={'refPath':BASE+'Materials/CH_'+name+'.CH_'+name}
  color=param(i,'BaseColor','vector')
  assert all(abs(color[a]-p['color'][j])<1e-6 for j,a in enumerate(['r','g','b','a']))
  for n,k in [('Roughness','roughness'),('Metallic','metallic'),('Opacity','alpha')]:
   assert abs(param(i,n,'scalar')-p[k])<1e-6
  emission=param(i,'Emissive','vector')
  assert all(abs(emission[a]-p['emission'][j]*p['emission_strength'])<1e-6 for j,a in enumerate(['r','g','b']))
 paths=[p for p in assets() if p.startswith(BASE)]
 assert len(paths)==39,len(paths)
 assert save(paths)
 assert not any(dirty(p) for p in paths)
 report={'meshes':rows,'material_instances_verified':len(manifest),'assets_saved':len(paths),'scope':'import verification; see placement_report.txt for level status','screenshots_created':False}
 write('ue_import_report.txt',report)
 return {'meshes':len(rows),'triangles':sum(r['triangles'] for r in rows.values()),'material_instances':len(manifest),'assets_saved':len(paths),'max_bound_error_cm':max(r['max_bound_error_cm'] for r in rows.values())}
