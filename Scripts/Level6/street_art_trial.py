"""One bounded facade and paving trial on four existing Level_6 buildings."""
import json
import math
MODE="facade"
INDEX=0
L="/Game/TestLevel/Level_6/level_6_create_map"
B="D:/UEProject/ArcheoDig/Saved/Level6StreetArt/"
S="editor_toolset.toolsets.scene.SceneTools."
A="editor_toolset.toolsets.actor.ActorTools."
O="editor_toolset.toolsets.object.ObjectTools."
F="editor_toolset.toolsets.asset.AssetTools."
C={"refPath":"/Script/Engine.StaticMeshComponent"}
def api(n,a):return execute_tool(n,json.dumps(a))["returnValue"]
def read(n):return json.loads(api(F+"read_file",{"file_path":B+n}).lstrip("\ufeff"))
def write(n,v):api(F+"write_file",{"file_path":B+n,"content":json.dumps(v)})
def props(c,n):return json.loads(api(O+"get_properties",{"instance":c,"properties":n}))
def setp(c,p):assert api(O+"set_properties",{"instance":c,"values":json.dumps(p)})
def same(a,b):return all(abs(a[k][v]-b[k][v])<.001 for k in ["location","rotation","scale"] for v in a[k])
def part_properties(p,t,world=False):
    if world:
        loc={k:(p["p"][i]*100-t["location"][k])/t["scale"][k] for i,k in enumerate(["x","y","z"])}
    else:
        loc={"x":p["p"][0]*100/t["scale"]["x"],"y":p["p"][1]*100/t["scale"]["y"],"z":(p["p"][2]*100-t["location"]["z"])/t["scale"]["z"]}
    return {"staticMesh":{"refPath":p["mesh"]},"relativeLocation":loc,"relativeRotation":p["rot"],"relativeScale3D":dict(zip(["x","y","z"],p["d"])),"bAbsoluteScale":True,"mobility":"Static","overrideMaterials":[{"refPath":p["m"]}],"bVisible":True,"bHiddenInGame":False,"bUseDefaultCollision":False,"bodyInstance":{"collisionEnabled":"QueryAndPhysics" if p.get("collision") else "NoCollision","collisionProfileName":"BlockAll" if p.get("collision") else "NoCollision","bSimulatePhysics":False},"bCanEverAffectNavigation":bool(p.get("collision")),"castShadow":not ("Joint" in p["name"] or "Paving" in p["name"]),"bVisibleInRayTracing":False}
def run():
    assert api(S+"get_current_level",{})==L and not api("EditorToolset.EditorAppToolset.IsPIERunning",{})
    if MODE=="facade":
        if INDEX:assert read("facade_done_0.json")["verified"]
        r=read("facade_"+str(INDEX)+".json");t=r["transform"]
        assert same(api(A+"get_actor_transform",{"actor":r["actor"]}),t)
        old=api(A+"get_components",{"actor":r["actor"],"component_type":C})
        assert len(old)==len(r["components"])
        made=[]
        try:
            setp(r["root"],{"overrideMaterials":[{"refPath":r["color"]}]})
            for p in r["parts"]:
                c=api(A+"add_component",{"owner":r["root"],"component_type":C,"name":p["name"]});made.append(c)
                setp(c,part_properties(p,t))
            assert len(api(A+"get_components",{"actor":r["actor"],"component_type":C}))==len(old)+len(made)
            assert same(api(A+"get_actor_transform",{"actor":r["actor"]}),t)
            for p in r["components"]:
                if p["component"]!=r["root"]:assert props(p["component"],list(p["properties"]))==p["properties"]
            for i in [0,6,len(made)-1]:
                expected=part_properties(r["parts"][i],t);actual=props(made[i],["staticMesh","overrideMaterials","relativeLocation","relativeRotation","relativeScale3D","bVisible","bodyInstance"])
                assert actual["staticMesh"]==expected["staticMesh"] and actual["overrideMaterials"]==expected["overrideMaterials"] and actual["bVisible"]
                for k in ["relativeLocation","relativeScale3D"]:assert all(abs(actual[k][v]-expected[k][v])<.001 for v in actual[k])
                assert actual["bodyInstance"]["collisionEnabled"]=="NoCollision"
            bounds=api(A+"get_actor_bounds",{"actor":r["actor"]})
            assert abs(bounds["max"]["z"]-r["bounds"]["max"]["z"])<.1
            result={"verified":True,"actor":r["actor"],"label":r["label"],"components":made,"parts":len(made),"bounds":bounds}
            write("facade_done_"+str(INDEX)+".json",result)
            return {"facade":r["label"],"parts":len(made),"roof_and_body_transform_unchanged":True,"verified":True}
        except Exception:
            for c in reversed(made):api(A+"remove_component",{"component":c})
            setp(r["root"],{"overrideMaterials":r["components"][0]["properties"]["overrideMaterials"]})
            raise
    if MODE=="street":
        assert all(read("facade_done_"+str(i)+".json")["verified"] for i in range(4))
        r=read("street.json");assert not api(S+"find_actors",{"name":r["name"],"tag":"","collision_channels":[]})
        p=r["parts"][0];t={"location":{"x":r["origin"][0],"y":r["origin"][1],"z":0},"rotation":{"pitch":0,"yaw":0,"roll":0},"scale":{"x":1,"y":1,"z":1}}
        a=api(S+"add_to_scene_from_asset",{"asset_path":"/Engine/BasicShapes/Cube.Cube","name":r["name"],"xform":t,"snap_to_ground":False});root=api(A+"get_root_component",{"actor":a})
        setp(root,{"bVisible":False,"bHiddenInGame":True,"bUseDefaultCollision":False,"bodyInstance":{"collisionEnabled":"NoCollision","collisionProfileName":"NoCollision"}})
        made=[]
        try:
            for p in r["parts"]:
                c=api(A+"add_component",{"owner":root,"component_type":C,"name":p["name"]});made.append(c);setp(c,part_properties(p,t,True))
            api(S+"set_actor_folder",{"actor":a,"folder_path":"CityBlockout/11_StreetArt/GrahamLane"})
            write("street_done.json",{"actor":a,"root":root,"components":made,"parts":len(made)})
            return {"new_actors":1,"street_parts":len(made)}
        except Exception:
            api(S+"remove_from_scene",{"actor":a});raise
    if MODE=="validate":
        assert read("clearance.json")["clear_for_capsule"] and not read("clearance.json")["body_center_conflicts"]
        for i in range(4):
            r=read("facade_"+str(i)+".json");done=read("facade_done_"+str(i)+".json")
            assert done["verified"] and same(api(A+"get_actor_transform",{"actor":r["actor"]}),r["transform"])
            assert props(r["root"],["overrideMaterials"])["overrideMaterials"]==[{"refPath":r["color"]}]
            for c in r["components"][1:]:assert props(c["component"],list(c["properties"]))==c["properties"]
        st=read("street_done.json");plan=read("street.json")
        assert len(api(A+"get_components",{"actor":st["actor"],"component_type":C}))==1+len(plan["parts"])
        for i,p in enumerate(plan["parts"]):
            if not p.get("collision") and i not in [10,30,len(plan["parts"])-1]:continue
            actual=props(st["components"][i],["bVisible","bHiddenInGame","bodyInstance","relativeLocation","relativeScale3D"])
            assert actual["bVisible"] and not actual["bHiddenInGame"]
            assert actual["bodyInstance"]["collisionEnabled"]==("QueryAndPhysics" if p.get("collision") else "NoCollision")
        points=[];route=[[14.3,21.3],[14.5,26.5],[23.5,28],[35,28]]
        for i in range(1,len(route)):
            a,b=route[i-1],route[i];steps=int(math.ceil(math.hypot(b[0]-a[0],b[1]-a[1])/2))
            points.extend([a[0]+(b[0]-a[0])*j/steps,a[1]+(b[1]-a[1])*j/steps] for j in range(steps+1))
        for x,y in points:
            box={"min":{"x":x*100-35,"y":y*100-35,"z":34},"max":{"x":x*100+35,"y":y*100+35,"z":208},"isValid":True}
            assert not api(S+"find_actors",{"name":"","tag":"","collision_channels":["ObjectTypeQuery1","ObjectTypeQuery2"],"bounds":box}),[x,y]
            box["min"]["z"]=24;box["max"]["z"]=27
            assert api(S+"find_actors",{"name":"","tag":"","collision_channels":["ObjectTypeQuery1","ObjectTypeQuery2"],"bounds":box}),[x,y]
        landmarks=json.loads(api(F+"read_file",{"file_path":"D:/UEProject/ArcheoDig/Saved/Level6Replan/ReferenceR2/models_before.json"}))
        checked=[]
        for r in landmarks:
            if r["group"] not in ["Museum","GrahamShop"]:continue
            assert same(api(A+"get_actor_transform",{"actor":r["actor"]}),r["transform"])
            for m in r["meshes"]:assert props(m["component"],["staticMesh","overrideMaterials"])==m["properties"]
            checked.append(r["group"])
        result={"route_samples":len(points),"clear":True,"floor_supported":True,"facades":4,"roofs_unchanged":True,"nearby_landmarks_unchanged":checked,"new_actors":1,"new_components":sum(read("facade_done_"+str(i)+".json")["parts"] for i in range(4))+len(plan["parts"])}
        write("validated.json",result)
        return result
    if MODE=="save":
        check=read("validated.json");assert check["clear"] and check["floor_supported"]
        assert read("pie.json")["passed"]
        assets=["/Game/TestLevel/Level_6/Blockout/Materials/StreetArt/MI_SA_LightOlive",L]
        assert api(F+"save_assets",{"asset_paths":assets})
        assert all(not api(F+"is_dirty",{"asset_path":p}) for p in assets)
        result={"status":"SUCCESS","saved":True,"buildings":4,"new_actors":1,"detail_components":check["new_components"],"new_material_instances":1,"route_length_m":read("clearance.json")["route_length_m"],"PIE_tested":True,"errors":[]}
        write("result.json",result)
        return result
    raise ValueError(MODE)
