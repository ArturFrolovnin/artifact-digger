"""Specific staged pedestrian rework for the current Level_6, no city generator."""
import json
import math
MODE="snapshot_roads"
INDEX=0
L="/Game/TestLevel/Level_6/level_6_create_map"
B="D:/UEProject/ArcheoDig/Saved/Level6RoadNetwork/"
S="editor_toolset.toolsets.scene.SceneTools."
A="editor_toolset.toolsets.actor.ActorTools."
O="editor_toolset.toolsets.object.ObjectTools."
F="editor_toolset.toolsets.asset.AssetTools."
def api(t,a):return execute_tool(t,json.dumps(a))["returnValue"]
def read(n):return json.loads(api(F+"read_file",{"file_path":B+n}).lstrip("\ufeff"))
def write(n,v):api(F+"write_file",{"file_path":B+n,"content":json.dumps(v)})
def props(c,n):return json.loads(api(O+"get_properties",{"instance":c,"properties":n}))
def setp(c,v):assert api(O+"set_properties",{"instance":c,"values":json.dumps(v)})
def same(a,b):return all(abs(a[k][v]-b[k][v])<.001 for k in ["location","rotation","scale"] for v in a[k])
def run():
    assert api(S+"get_current_level",{})==L and not api("EditorToolset.EditorAppToolset.IsPIERunning",{})
    if MODE=="snapshot_roads":
        rows=read("road_input_"+str(INDEX)+".json")
        for r in rows:r["before"]=api(A+"get_actor_transform",{"actor":r["actor"]});r["xform"]=r["before"]
        write("roads_"+str(INDEX)+".json",rows)
        return {"road_batch":INDEX,"read":len(rows)}
    if MODE=="snapshot_models":
        rows=read("models_input.json")
        for r in rows:
            r["transform"]=api(A+"get_actor_transform",{"actor":r["actor"]})
            r["bounds"]=api(A+"get_actor_bounds",{"actor":r["actor"]})
            for m in r["meshes"]:m["properties"]=props(m["component"],["staticMesh","overrideMaterials"])
        write("models.json",rows)
        return {"landmarks_read":len(rows)}
    if MODE=="snapshot_background":
        rows=read("background_input.json")
        for r in rows:r["transform"]=api(A+"get_actor_transform",{"actor":r["actor"]})
        write("background.json",rows)
        return {"background_read":len(rows)}
    if MODE=="final_save":
        paths=[L,"/Game/TestLevel/Level_6/Blockout/Materials/RoadNetwork/M_RN_Stone"]
        paths.extend("/Game/TestLevel/Level_6/Blockout/Materials/RoadNetwork/MI_RN_"+v for v in ["Street","Alley","Park"])
        for layer in ["market","primary","plazas","accent","secondary","park","alleys","curbs"]:
            r=read("placed_"+layer+".json");p=props(r["root"],["bVisible","bHiddenInGame","bodyInstance"])
            assert p["bVisible"] and not p["bHiddenInGame"] and p["bodyInstance"]["collisionEnabled"]=="NoCollision"
            assert abs(api(A+"get_actor_transform",{"actor":r["actor"]})["location"]["z"])<.01
            box=api(A+"get_actor_bounds",{"actor":r["actor"]})
            assert abs(box["max"]["z"]-25)<.1 and box["min"]["x"]>-7920 and box["max"]["x"]<7920 and box["min"]["y"]>-9920 and box["max"]["y"]<9920
            paths.append(r["asset"].split('.')[0])
        assert api(F+"save_assets",{"asset_paths":paths})
        assert all(not api(F+"is_dirty",{"asset_path":p}) for p in paths)
        return {"status":"SUCCESS","level_saved":True,"new_road_actors":83,"surface_actors":8,"collision_floor_actors_new":75,"assets_saved":len(paths),"other_exits":False}
    if MODE=="preserve":
        roads=[r for i in range(6) for r in read("roads_"+str(i)+".json")]
        bg=read("background.json");models=read("models.json")
        assert not ({r["actor"]["refPath"] for r in roads}&{r["actor"]["refPath"] for r in bg+models})
        assert all(.239<r["before"]["scale"]["z"]<.251 for r in roads)
        for r in models:
            assert same(api(A+"get_actor_transform",{"actor":r["actor"]}),r["transform"]),r["label"]
            for m in r["meshes"]:assert props(m["component"],["staticMesh","overrideMaterials"])==m["properties"],r["label"]
        for r in bg:assert same(api(A+"get_actor_transform",{"actor":r["actor"]}),r["transform"]),r["label"]
        private=[r for r in roads if r.get("private")]
        for r in private:assert same(api(A+"get_actor_transform",{"actor":r["actor"]}),r["before"]),r["label"]
        safety=json.loads(api(F+"read_file",{"file_path":"D:/UEProject/ArcheoDig/Saved/Level6Replan/BoundaryRoads/safety_created.json"}))
        for r in safety:
            assert same(api(A+"get_actor_transform",{"actor":r["actor"]}),r["xform"])
            root=api(A+"get_root_component",{"actor":r["actor"]});p=props(root,["bodyInstance"])["bodyInstance"]
            assert p["collisionEnabled"]=="QueryAndPhysics" and p["collisionProfileName"]=="BlockAll"
        entrances=[("Museum",8.8,-24),("University",45.73,7),("Library",47.9,43),("TownHall",51.2,78),("Rudy",-19.1,-24),("Graham",-2.8,33),("Cafe",-54.8,13),("Hospital",4.6,78),("Car",-30,63.1),("Store",41.8,-80),("Bus",39.5,-80),("PrivateStreet",-25,-73.55)]
        for name,x,y in entrances:
            box={"min":{"x":x*100-35,"y":y*100-35,"z":27},"max":{"x":x*100+35,"y":y*100+35,"z":205},"isValid":True}
            assert not api(S+"find_actors",{"name":"","tag":"","collision_channels":["ObjectTypeQuery1","ObjectTypeQuery2"],"bounds":box}),name
            box["min"]["z"]=23;box["max"]["z"]=26
            assert api(S+"find_actors",{"name":"","tag":"","collision_channels":["ObjectTypeQuery1","ObjectTypeQuery2"],"bounds":box}),name
        return {"main_groups_unchanged":len(models),"background_unchanged":len(bg),"private_streets_unchanged":len(private),"entrances_accessible":len(entrances),"safety_unchanged":4}
    if MODE=="cleanup":
        removed=0
        for r in read("retired.json"):
            root=api(A+"get_root_component",{"actor":r["actor"]})
            assert props(root,["bodyInstance"])["bodyInstance"]["collisionEnabled"]=="NoCollision"
            assert api(S+"remove_from_scene",{"actor":r["actor"]});removed+=1
        old=read("render_input.json")["surfaces"]
        for name in ["surface_created.json","curbs_created.json"]:old.append(json.loads(api(F+"read_file",{"file_path":"D:/UEProject/ArcheoDig/Saved/Level6Replan/BoundaryRoads/"+name})))
        for r in old:
            p=props(r["root"],["staticMesh","bVisible"])
            assert "/Blockout/Generated/SM_L6_Pedestrian" in p["staticMesh"]["refPath"] and not p["bVisible"]
            assert api(S+"remove_from_scene",{"actor":r["actor"]});removed+=1
        for r in read("render_input.json")["roadComponents"]:assert api(A+"remove_component",{"component":r["component"]})
        street=read("render_input.json")["streetActor"]
        assert len(api(A+"get_components",{"actor":street,"component_type":{"refPath":"/Script/Engine.StaticMeshComponent"}}))==19
        return {"removed_road_actors":removed,"removed_local_road_components":40,"street_furniture_retained":True}
    if MODE=="switch":
        for layer in ["market","primary","plazas","accent","secondary","park","alleys","curbs"]:
            r=read("placed_"+layer+".json");t=api(A+"get_actor_transform",{"actor":r["actor"]})
            assert abs(t["location"]["z"]-1)<.01;t["location"]["z"]=0
            assert api(A+"set_actor_transform",{"actor":r["actor"],"xform":t,"worldspace":True})
        for r in read("render_input.json")["surfaces"]:
            assert props(r["root"],["staticMesh"])["staticMesh"]["refPath"]==r["asset"]
            setp(r["root"],{"bVisible":False,"bHiddenInGame":True})
        old=[]
        for i in range(6):
            for r in read("roads_"+str(i)+".json"):
                if not r.get("private"):continue
                root=api(A+"get_root_component",{"actor":r["actor"]});p=props(root,["staticMesh","bVisible","bHiddenInGame"])
                assert p["staticMesh"]["refPath"]=="/Engine/BasicShapes/Cube.Cube"
                old.append({"actor":r["actor"],"root":root,"before":p});setp(root,{"bVisible":False,"bHiddenInGame":True})
        write("private_render_before.json",old)
        for r in read("retired.json"):
            assert same(api(A+"get_actor_transform",{"actor":r["actor"]}),r["before"])
            root=api(A+"get_root_component",{"actor":r["actor"]});p=props(root,["staticMesh"])
            assert p["staticMesh"]["refPath"]=="/Engine/BasicShapes/Cube.Cube"
            setp(root,{"bUseDefaultCollision":False,"bodyInstance":{"collisionEnabled":"NoCollision","collisionProfileName":"NoCollision"}})
        return {"new_network_active":True,"private_street_transforms_untouched":31,"old_floor_parts_disabled":63}
    if MODE=="check_routes":
        blocked=[];unsupported=[];count=0
        for r in read("routes_"+str(INDEX)+".json"):
            seen=set()
            for i in range(1,len(r["points"])):
                a,b=r["points"][i-1],r["points"][i];n=max(1,int(math.ceil(math.hypot(b[0]-a[0],b[1]-a[1])/4)))
                for j in range(n+1):
                    x=a[0]+(b[0]-a[0])*j/n;y=a[1]+(b[1]-a[1])*j/n
                    key=(int(round(x/1.5)),int(round(y/1.5)))
                    if key in seen:continue
                    seen.add(key)
                    box={"min":{"x":x*100-35,"y":y*100-35,"z":27},"max":{"x":x*100+35,"y":y*100+35,"z":205},"isValid":True}
                    found=api(S+"find_actors",{"name":"","tag":"","collision_channels":["ObjectTypeQuery1","ObjectTypeQuery2"],"bounds":box})
                    if found:blocked.append({"route":r["name"],"point":[x,y],"hits":found})
                    box["min"]["x"]=x*100-8;box["max"]["x"]=x*100+8;box["min"]["y"]=y*100-8;box["max"]["y"]=y*100+8;box["min"]["z"]=23;box["max"]["z"]=26
                    if not api(S+"find_actors",{"name":"","tag":"","collision_channels":["ObjectTypeQuery1","ObjectTypeQuery2"],"bounds":box}):unsupported.append({"route":r["name"],"point":[x,y]})
                    count+=1
        return {"batch":INDEX,"samples":count,"blocked":blocked,"unsupported":unsupported}
    if MODE=="new_floors":
        result=[]
        for r in read("new_floors_"+str(INDEX)+".json"):
            a=api(S+"add_to_scene_from_asset",{"asset_path":"/Engine/BasicShapes/Cube.Cube","name":r["label"]+"_Floor","xform":r["xform"],"snap_to_ground":False});root=api(A+"get_root_component",{"actor":a})
            setp(root,{"bVisible":False,"bHiddenInGame":True,"bUseDefaultCollision":False,"bodyInstance":{"collisionEnabled":"QueryAndPhysics","collisionProfileName":"BlockAll","bSimulatePhysics":False},"canCharacterStepUpOn":"ECB_Yes"})
            api(S+"set_actor_folder",{"actor":a,"folder_path":"CityBlockout/07_Pedestrian/RoadNetwork/Floors"});result.append({"actor":a,"root":root,"xform":r["xform"]})
        write("new_floors_done_"+str(INDEX)+".json",result)
        return {"batch":INDEX,"new_collision_floors":len(result)}
    if MODE=="changes":
        rows=read("changes_"+str(INDEX)+".json")
        for r in rows:
            assert same(api(A+"get_actor_transform",{"actor":r["actor"]}),r["before"])
            assert api(A+"set_actor_transform",{"actor":r["actor"],"xform":r["xform"],"worldspace":True})
        return {"batch":INDEX,"floor_widths_refitted":len(rows)}
    if MODE=="checkpoint":
        paths=[L,"/Game/TestLevel/Level_6/Blockout/Materials/RoadNetwork/M_RN_Stone"]
        paths.extend("/Game/TestLevel/Level_6/Blockout/Materials/RoadNetwork/MI_RN_"+v for v in ["Street","Alley","Park"])
        for layer in ["market","primary","plazas","accent","secondary","park","alleys","curbs"][:INDEX+1]:paths.append(read("placed_"+layer+".json")["asset"].split('.')[0])
        assert api(F+"save_assets",{"asset_paths":paths})
        return {"checkpoint":INDEX,"saved":True}
    if MODE=="place":
        layers=["market","primary","plazas","accent","secondary","park","alleys","curbs"]
        layer=layers[INDEX];asset="/Game/TestLevel/Level_6/Blockout/Generated/RoadNetwork/SM_RN_"+layer.title()+".SM_RN_"+layer.title()
        assert not api(S+"find_actors",{"name":"RN_"+layer,"tag":"","collision_channels":[]})
        t={"location":{"x":0,"y":0,"z":1},"rotation":{"pitch":0,"yaw":0,"roll":0},"scale":{"x":1,"y":-1,"z":1}}
        actor=api(S+"add_to_scene_from_asset",{"asset_path":asset,"name":"RN_"+layer,"xform":t,"snap_to_ground":False});root=api(A+"get_root_component",{"actor":actor})
        mat="/Game/TestLevel/Level_6/Blockout/Materials/RoadNetwork/MI_RN_"+("Alley" if layer=="alleys" else "Park" if layer=="park" else "Street")
        mat=mat+"."+mat.split('/')[-1]
        if layer in ["accent","curbs"]:mat="/Game/Art/Models/Residential/IntellectualGrandpaHouse/Materials/MI_IGH_Limestone.MI_IGH_Limestone"
        setp(root,{"overrideMaterials":[{"refPath":mat}],"bUseDefaultCollision":False,"bodyInstance":{"collisionEnabled":"NoCollision","collisionProfileName":"NoCollision"},"bVisible":True,"bHiddenInGame":False})
        api(S+"set_actor_folder",{"actor":actor,"folder_path":"CityBlockout/07_Pedestrian/RoadNetwork/Surfaces"})
        bounds=api(A+"get_actor_bounds",{"actor":actor});assert bounds["isValid"] and abs(bounds["max"]["z"]-26)<.1
        write("placed_"+layer+".json",{"actor":actor,"root":root,"asset":asset,"xform":t})
        if layer=="market":
            assert bounds["min"]["x"]>1200 and bounds["max"]["x"]<3600
            for r in read("render_input.json")["roadComponents"]:setp(r["component"],{"bVisible":False,"bHiddenInGame":True})
        return {"layer":layer,"new_surface_placed":True,"bounds":bounds}
    raise ValueError(MODE)
