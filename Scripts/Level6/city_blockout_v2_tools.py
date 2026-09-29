import json
def spawn(item):
 return execute_tool("editor_toolset.toolsets.scene.SceneTools.add_to_scene_from_asset",json.dumps({"asset_path":"/Engine/BasicShapes/Cube.Cube","name":"BO_"+item["name"],"xform":{"location":{"x":(80-item["v"])*100,"y":(item["u"]-100)*100,"z":(item["z"]+item["h"]/2)*100},"rotation":{"pitch":0,"yaw":item["yaw"],"roll":0},"scale":{"x":item["d"],"y":item["w"],"z":item["h"]}}}))["returnValue"]
def components(a):
 return execute_tool("editor_toolset.toolsets.actor.ActorTools.get_components",json.dumps({"actor":a,"component_type":{"refPath":"/Script/Engine.StaticMeshComponent"}}))["returnValue"]
def material(c,n):
 return execute_tool("editor_toolset.toolsets.object.ObjectTools.set_properties",json.dumps({"instance":c,"values":json.dumps({"overrideMaterials":[{"refPath":"/Game/TestLevel/Level_6/Blockout/Materials/M_BO_"+n+".M_BO_"+n}]})}))["returnValue"]
def folder(a,n):
 execute_tool("editor_toolset.toolsets.scene.SceneTools.set_actor_folder",json.dumps({"actor":a,"folder_path":"CityBlockout/"+n}))
def build(items):
 result=[]
 for item in items:
  a=spawn(item)
  assert material(components(a)[0],item["mat"])
  folder(a,item["folder"])
  result.append({"actor":a,"name":item["name"]})
 return {"created":result}

# Tool-orchestration helpers. Pass items from city_blockout_v2.json to build().
# Run only through ProgrammaticToolset.execute_tool_script with a run() entrypoint.

