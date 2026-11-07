"""Explicit Level_6 quarter relocation and pavement integration."""
import json
import math
MODE="snapshot_parts"
INDEX=0
L="/Game/TestLevel/Level_6/level_6_create_map"
B="D:/UEProject/ArcheoDig/Saved/Level6OrganicCity/"
S="editor_toolset.toolsets.scene.SceneTools."
A="editor_toolset.toolsets.actor.ActorTools."
O="editor_toolset.toolsets.object.ObjectTools."
F="editor_toolset.toolsets.asset.AssetTools."
CUBE="/Engine/BasicShapes/Cube.Cube"
ROOF="/Game/Art/Models/Residential/PlayerHouse/SM_PlayerHouse_Roof.SM_PlayerHouse_Roof"
def api(t,a):return execute_tool(t,json.dumps(a))["returnValue"]
def read(n):return json.loads(api(F+"read_file",{"file_path":B+n}).lstrip("\ufeff"))
def write(n,v):api(F+"write_file",{"file_path":B+n,"content":json.dumps(v)})
def props(c,n):return json.loads(api(O+"get_properties",{"instance":c,"properties":n}))
def setp(c,v):assert api(O+"set_properties",{"instance":c,"values":json.dumps(v)})
def asset(layer):
    n="SM_OC_"+layer.title();return "/Game/TestLevel/Level_6/Blockout/Generated/OrganicCity/"+n+"."+n
def trace(x,y):return api(S+"trace_world",{"start":{"x":x,"y":y,"z":200},"end":{"x":x,"y":y,"z":-100}})
def same(a,b):return all(abs(a[k][v]-b[k][v])<.001 for k in ["location","scale"] for v in a[k]) and all(abs((a["rotation"][v]-b["rotation"][v]+180)%360-180)<.001 for v in a["rotation"])
def run():
    assert api(S+"get_current_level",{})==L and not api("EditorToolset.EditorAppToolset.IsPIERunning",{})
    if MODE=="snapshot_parts":
        rows=read("moves_"+str(INDEX)+".json");resized=0
        for r in rows:
            assert same(api(A+"get_actor_transform",{"actor":r["actor"]}),r["transform"])
            assert api(A+"get_label",{"actor":r["actor"]})==r["label"]
            root=api(A+"get_root_component",{"actor":r["actor"]});r["root"]=root
            assert props(root,["staticMesh"])["staticMesh"]["refPath"]==CUBE
            r["components"]=[]
            if abs(r["xform"]["scale"]["x"]-r["transform"]["scale"]["x"])<.001 and abs(r["xform"]["scale"]["y"]-r["transform"]["scale"]["y"])<.001:continue
            cs=api(A+"get_components",{"actor":r["actor"],"component_type":{"refPath":"/Script/Engine.StaticMeshComponent"}})
            assert len(cs)<=4,r["label"]
            for c in cs:
                if c==root:continue
                p=props(c,["staticMesh","relativeLocation","relativeRotation","relativeScale3D","bAbsoluteScale","overrideMaterials"])
                assert p["bAbsoluteScale"] and p["staticMesh"]["refPath"] in [CUBE,ROOF] and all(abs(v)<.01 for v in p["relativeRotation"].values()),r["label"]
                r["components"].append({"component":c,"properties":p})
            resized+=1
        write("prepared_"+str(INDEX)+".json",rows)
        return {"batch":INDEX,"actors":len(rows),"resize_ready":resized}
    if MODE=="move":
        rows=read("prepared_"+str(INDEX)+".json");done=[]
        roof=json.loads(api(F+"read_file",{"file_path":"D:/UEProject/ArcheoDig/Saved/Level6Replan/ReferenceR2/roof_bounds.json"}))
        try:
            for r in rows:
                old,new=r["transform"],r["xform"]
                assert same(api(A+"get_actor_transform",{"actor":r["actor"]}),old),r["label"]
                done.append(r)
                assert api(A+"set_actor_transform",{"actor":r["actor"],"xform":new,"worldspace":True})
                for c in r["components"]:
                    p=c["properties"];mb=roof if p["staticMesh"]["refPath"]==ROOF else {"min":{"x":-50,"y":-50},"max":{"x":50,"y":50}}
                    sc=dict(p["relativeScale3D"]);loc=dict(p["relativeLocation"])
                    for k in ["x","y"]:
                        span=mb["max"][k]-mb["min"][k];center=(mb["max"][k]+mb["min"][k])/2
                        sc[k]+=(new["scale"][k]-old["scale"][k])*100/span
                        oc=p["relativeLocation"][k]*old["scale"][k]+center*p["relativeScale3D"][k]
                        loc[k]=(oc*new["scale"][k]/old["scale"][k]-center*sc[k])/new["scale"][k]
                    setp(c["component"],{"relativeScale3D":sc,"relativeLocation":loc})
                assert same(api(A+"get_actor_transform",{"actor":r["actor"]}),new)
            write("moved_"+str(INDEX)+".json",{"count":len(done)})
        except Exception:
            for r in reversed(done):
                api(A+"set_actor_transform",{"actor":r["actor"],"xform":r["transform"],"worldspace":True})
                for c in r["components"]:setp(c["component"],c["properties"])
            raise
        return {"batch":INDEX,"background_relocated":len(done)}
    if MODE=="checkpoint":
        assert api(F+"save_assets",{"asset_paths":[L]+([asset(v).split(".")[0] for v in ["market","primary","plazas","secondary","alleys","curbs","park","accent","support"]] if INDEX==3 else [])})
        return {"saved":True,"stage":INDEX}
    if MODE=="import":
        layer=["market","primary","plazas","secondary","alleys","curbs","park","accent","support"][INDEX]
        src="pedestrian_curbs.obj" if layer=="curbs" else "OC_support.obj" if layer=="support" else "RN_"+layer+".obj"
        path=asset(layer);n=path.split(".")[-1]
        refs=api("editor_toolset.toolsets.static_mesh.StaticMeshTools.import_file",{"folder_path":path.rsplit("/",1)[0],"asset_name":n,"source_file":B+src,"import_materials":False,"import_textures":False,"combine_meshes":True})
        assert len(refs)==1 and refs[0]["refPath"]==path,refs
        b=api("editor_toolset.toolsets.static_mesh.StaticMeshTools.get_bounds",{"mesh":refs[0]})
        assert abs(b["max"]["z"]-25)<.01 and b["min"]["x"]> -7920 and b["max"]["x"]<7920
        write("imported_"+str(INDEX)+".json",{"layer":layer,"asset":path,"bounds":b})
        return {"imported":layer,"existing_materials_reused":True}
    if MODE=="pavement":
        assert not api(S+"find_actors",{"name":"OC_PublicSupport","tag":"","collision_channels":[]})
        body=props({"refPath":asset("support")},["bodySetup"])["bodySetup"]
        setp(body,{"collisionTraceFlag":"CTF_UseComplexAsSimple","bDoubleSidedGeometry":True})
        t={"location":{"x":0,"y":0,"z":0},"rotation":{"pitch":0,"yaw":0,"roll":0},"scale":{"x":1,"y":-1,"z":1}}
        a=api(S+"add_to_scene_from_asset",{"asset_path":asset("support"),"name":"OC_PublicSupport","xform":t,"snap_to_ground":False});root=api(A+"get_root_component",{"actor":a})
        setp(root,{"bVisible":False,"bHiddenInGame":True,"bUseDefaultCollision":False,"bodyInstance":{"collisionEnabled":"QueryAndPhysics","collisionProfileName":"BlockAll","bSimulatePhysics":False},"canCharacterStepUpOn":"ECB_Yes","castShadow":False,"bVisibleInRayTracing":False})
        api(S+"set_actor_folder",{"actor":a,"folder_path":"CityBlockout/07_Pedestrian/OrganicCity"})
        write("support_actor.json",{"actor":a,"root":root})
        changed=[]
        try:
            for r in read("surfaces.json"):
                assert same(api(A+"get_actor_transform",{"actor":r["actor"]}),r["transform"])
                assert props(r["root"],["staticMesh"])["staticMesh"]==r["properties"]["staticMesh"]
                changed.append(r)
                setp(r["root"],{"staticMesh":{"refPath":asset(r["layer"])},"bUseDefaultCollision":False,"bodyInstance":{"collisionEnabled":"NoCollision","collisionProfileName":"NoCollision"}})
                assert props(r["root"],["overrideMaterials"])["overrideMaterials"]==r["properties"]["overrideMaterials"]
            assert abs(trace(-2500,-7355)-176)<.02
            assert abs(trace(-4300,2550)-175)<.02
        except Exception:
            for r in reversed(changed):setp(r["root"],r["properties"])
            api(S+"remove_from_scene",{"actor":a})
            raise
        return {"surface_actors_rebuilt":len(changed),"new_exact_collision":1,"surface_height_cm":25}
    if MODE=="retire_floors":
        rows=read("retire_floors_"+str(INDEX)+".json");done=[]
        for r in rows:
            assert not r.get("private") and not r["label"].startswith("RC_")
            assert same(api(A+"get_actor_transform",{"actor":r["actor"]}),r["xform"]),r["label"]
            assert abs(r["xform"]["scale"]["z"]-.25)<.001
            assert api(S+"remove_from_scene",{"actor":r["actor"]})
            done.append(r["actor"])
        write("retired_"+str(INDEX)+".json",done)
        return {"batch":INDEX,"obsolete_public_floor_actors_removed":len(done)}
    if MODE=="court_walls":
        old=[]
        for f in ["D:/UEProject/ArcheoDig/Saved/Level6Replan/ReferenceR2/court_fences_created.json","D:/UEProject/ArcheoDig/Saved/Level6Replan/BoundaryRoads/court_fences_created.json"]:old+=json.loads(api(F+"read_file",{"file_path":f}))
        for r in old:
            assert api(A+"get_label",{"actor":r["actor"]})==r["item"]["name"]
            assert api(S+"remove_from_scene",{"actor":r["actor"]})
        made=[]
        for p in read("walls_plan.json"):
            a=api(S+"add_to_scene_from_asset",{"asset_path":CUBE,"name":p["name"],"xform":p["xform"],"snap_to_ground":False});c=api(A+"get_root_component",{"actor":a})
            setp(c,{"overrideMaterials":[{"refPath":"/Game/Art/Models/Residential/IntellectualGrandpaHouse/Materials/MI_IGH_Limestone.MI_IGH_Limestone"}],"bUseDefaultCollision":False,"bodyInstance":{"collisionEnabled":"QueryAndPhysics","collisionProfileName":"BlockAll","bSimulatePhysics":False},"bVisibleInRayTracing":False})
            api(S+"set_actor_folder",{"actor":a,"folder_path":"CityBlockout/09_Background/OrganicCourts"});made.append({"actor":a,"root":c,"plan":p})
        write("walls_created.json",made)
        return {"old_court_closures_removed":len(old),"new_court_wall_sections":len(made)}
    if MODE=="cleanup_support":
        old=json.loads(api(F+"read_file",{"file_path":"D:/UEProject/ArcheoDig/Saved/Level6FacadePaving/support_actor.json"}))
        assert props(old["root"],["staticMesh"])["staticMesh"]["refPath"]==old["asset"]
        assert api(S+"remove_from_scene",{"actor":old["actor"]})
        for r in read("reserve_pads.json"):
            assert same(api(A+"get_actor_transform",{"actor":r["actor"]}),r["transform"])
            assert props(r["root"],["staticMesh","overrideMaterials"])==r["properties"]
            assert api(S+"remove_from_scene",{"actor":r["actor"]})
        return {"obsolete_infill_support_removed":1,"public_green_reserve_pads_removed":4}
    if MODE=="trees":
        done=[]
        for r in read("trees_plan.json"):
            assert same(api(A+"get_actor_transform",{"actor":r["actor"]}),r["transform"])
            c=api(A+"get_root_component",{"actor":r["actor"]});p=props(c,["bodyInstance","bUseDefaultCollision"])
            setp(c,{"bUseDefaultCollision":False,"bodyInstance":{"collisionEnabled":"NoCollision","collisionProfileName":"NoCollision"}})
            t=r["xform"];d=trace(t["location"]["x"],t["location"]["y"]);assert d is not None
            t["location"]["z"]=200-d+t["scale"]["z"]*50
            assert api(A+"set_actor_transform",{"actor":r["actor"],"xform":t,"worldspace":True});setp(c,p)
            done.append({"actor":r["actor"],"xform":t})
        write("trees_done.json",done)
        return {"existing_trees_aligned_to_ground":len(done)}
    if MODE=="furniture":
        base="D:/UEProject/ArcheoDig/Saved/Level6StreetArt/"
        plan=json.loads(api(F+"read_file",{"file_path":base+"street.json"}))["parts"]
        old=json.loads(api(F+"read_file",{"file_path":base+"street_done.json"}));origin=api(A+"get_actor_transform",{"actor":old["actor"]})
        groups={23:[],25:[],27:[]};pots=0;before=[]
        for i,p in enumerate(plan):
            if "Bench" not in p["name"] and "Planter" not in p["name"]:continue
            if "Bench" in p["name"]:bid=25
            else:bid=[23,25,27][pots//4];pots+=1
            c=old["components"][i];v=props(c,["relativeLocation","relativeRotation"]);groups[bid].append((c,v));before.append({"component":c,"properties":v})
        write("furniture_before.json",before)
        moves=[]
        for i in range(2):moves+=read("prepared_"+str(i)+".json")
        for bid,rows in groups.items():
            r=next(r for r in moves if r["id"]==bid);a,b=r["transform"],r["xform"];delta=b["rotation"]["yaw"]-a["rotation"]["yaw"];angle=delta*math.pi/180;co,si=math.cos(angle),math.sin(angle)
            for c,v in rows:
                q=dict(v["relativeLocation"]);x=q["x"]+origin["location"]["x"]-a["location"]["x"];y=q["y"]+origin["location"]["y"]-a["location"]["y"]
                q["x"]=b["location"]["x"]+co*x-si*y-origin["location"]["x"];q["y"]=b["location"]["y"]+si*x+co*y-origin["location"]["y"]
                rot=dict(v["relativeRotation"]);rot["yaw"]+=delta;setp(c,{"relativeLocation":q,"relativeRotation":rot})
        return {"existing_furniture_components_relocated":len(before)}
    if MODE=="preserve":
        if INDEX==0:
            rows=read("models.json")
            for r in rows:
                assert same(api(A+"get_actor_transform",{"actor":r["actor"]}),r["transform"]),r["label"]
                for m in r["meshes"]:assert props(m["component"],["staticMesh","overrideMaterials"])==m["properties"],r["label"]
            return {"main_building_groups_unchanged":len(rows)}
        if INDEX==1:
            rows=json.loads(api(F+"read_file",{"file_path":"D:/UEProject/ArcheoDig/Saved/Level6Replan/BoundaryRoads/private_before.json"}))
            for r in rows:assert same(api(A+"get_actor_transform",{"actor":r["actor"]}),r["transform"]),r["label"]
            safety=json.loads(api(F+"read_file",{"file_path":"D:/UEProject/ArcheoDig/Saved/Level6Replan/BoundaryRoads/safety_created.json"}))
            for r in safety:
                assert same(api(A+"get_actor_transform",{"actor":r["actor"]}),r["xform"])
                c=api(A+"get_root_component",{"actor":r["actor"]});p=props(c,["bodyInstance"])
                assert p["bodyInstance"]["collisionEnabled"]=="QueryAndPhysics" and p["bodyInstance"]["collisionProfileName"]=="BlockAll"
            return {"private_street_parts_unchanged":len(rows),"continuous_boundary_blockers_unchanged":len(safety)}
        for i in range(11):
            for r in read("prepared_"+str(i)+".json"):assert same(api(A+"get_actor_transform",{"actor":r["actor"]}),r["xform"]),r["label"]
        return {"background_targets_verified":88}
    if MODE in ["check_routes","check_entries"]:
        if MODE=="check_routes":rows=read("route_probes.json")[INDEX*30:(INDEX+1)*30]
        else:
            tests=[("Museum",8.8,-24),("University",45.73,7),("Library",47.9,43),("TownHall",51.2,78),("Dormitory",46,-29),("Rudy",-19.1,-24),("Graham",-2.8,33),("Cafe",-54.8,13),("Hospital",4.6,78),("Car",-30,63.1),("Store",41.8,-80),("Bus",39.5,-80),("PrivateStreet",-25,-73.55),("MarketCourt",-8,10),("EastCourt",33.5,39.5),("WestCourt",-49,80),("ArrivalMews",64,-90),("QuietSpur",-53,54.5)]
            rows=[{"route":n,"point":[x,y]} for n,x,y in tests]
        blocked=[];missing=[];heights=[]
        for p in rows:
            x,y=p["point"];b={"min":{"x":x*100-35,"y":y*100-35,"z":27},"max":{"x":x*100+35,"y":y*100+35,"z":205},"isValid":True}
            hit=api(S+"find_actors",{"name":"","tag":"","collision_channels":["ObjectTypeQuery1","ObjectTypeQuery2"],"bounds":b})
            if hit:blocked.append({"probe":p,"hits":[api(A+"get_label",{"actor":a}) for a in hit]})
            d=trace(x*100,y*100)
            if d is None or d<155 or d>177:missing.append({"probe":p,"distance":d})
            else:heights.append(200-d)
        result={"probes":len(rows),"blocked":blocked,"missing_floor":missing,"height_range_cm":[min(heights),max(heights)] if heights else []}
        write(MODE+"_"+str(INDEX)+".json",result)
        return result
    if MODE=="save":
        pie=read("pie_result.json");assert pie["passed"] and len(pie["tests"])==6 and all(t["passed"] for t in pie["tests"])
        graph=read("connectivity.json");assert graph["connected"]==graph["route_and_private_points"] and not graph["unreached"]
        assert sum(len(read("retired_"+str(i)+".json")) for i in range(6))==297
        for i in range(4):
            r=read("check_routes_"+str(i)+".json");assert not r["blocked"] and not r["missing_floor"]
        r=read("check_entries_0.json");assert not r["blocked"] and not r["missing_floor"]
        for r in read("surfaces.json"):
            b=api(A+"get_actor_bounds",{"actor":r["actor"]});assert abs(b["max"]["z"]-25)<.01,r["layer"]
            assert props(r["root"],["staticMesh","overrideMaterials"])=={"staticMesh":{"refPath":asset(r["layer"])},"overrideMaterials":r["properties"]["overrideMaterials"]}
        paths=[L]+[asset(v).split(".")[0] for v in ["market","primary","plazas","secondary","alleys","curbs","park","accent","support"]]
        assert api(F+"save_assets",{"asset_paths":paths})
        assert all(not api(F+"is_dirty",{"asset_path":p}) for p in paths)
        return {"level_saved":True,"assets_saved":len(paths),"level_dirty":False}
    raise ValueError(MODE)
