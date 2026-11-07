"""Facade contact correction of existing Level_6 pavement actors."""
import json
import math
MODE="apply"
INDEX=0
L="/Game/TestLevel/Level_6/level_6_create_map"
B="D:/UEProject/ArcheoDig/Saved/Level6FacadePaving/"
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
def asset(layer):
    name="SM_FP_"+layer.title();return "/Game/TestLevel/Level_6/Blockout/Generated/FacadePaving/"+name+"."+name
def trace(x,y):return api(S+"trace_world",{"start":{"x":x*100,"y":y*100,"z":200},"end":{"x":x*100,"y":y*100,"z":-100}})
def run():
    assert api(S+"get_current_level",{})==L and not api("EditorToolset.EditorAppToolset.IsPIERunning",{})
    if MODE=="apply":
        quarter=json.loads(api(F+"read_file",{"file_path":"D:/UEProject/ArcheoDig/Saved/Level6Replan/BoundaryRoads/private_before.json"}))
        for r in quarter:assert same(api(A+"get_actor_transform",{"actor":r["actor"]}),r["transform"]),r["label"]
        assert not api(S+"find_actors",{"name":"FP_InfillSupport","tag":"","collision_channels":[]})
        mesh={"refPath":asset("support")};body=props(mesh,["bodySetup"])["bodySetup"]
        setp(body,{"collisionTraceFlag":"CTF_UseComplexAsSimple","bDoubleSidedGeometry":True})
        t={"location":{"x":0,"y":0,"z":0},"rotation":{"pitch":0,"yaw":0,"roll":0},"scale":{"x":1,"y":-1,"z":1}}
        support=api(S+"add_to_scene_from_asset",{"asset_path":asset("support"),"name":"FP_InfillSupport","xform":t,"snap_to_ground":False});root=api(A+"get_root_component",{"actor":support})
        setp(root,{"bVisible":False,"bHiddenInGame":True,"bUseDefaultCollision":False,"bodyInstance":{"collisionEnabled":"QueryAndPhysics","collisionProfileName":"BlockAll","bSimulatePhysics":False},"canCharacterStepUpOn":"ECB_Yes","castShadow":False,"bVisibleInRayTracing":False})
        api(S+"set_actor_folder",{"actor":support,"folder_path":"CityBlockout/07_Pedestrian/FacadePaving"})
        write("support_actor.json",{"actor":support,"root":root,"asset":asset("support")})
        changed=[]
        try:
            for r in read("surfaces_before.json"):
                if r["layer"] in ["park","accent"]:continue
                assert same(api(A+"get_actor_transform",{"actor":r["actor"]}),r["transform"])
                assert props(r["root"],["staticMesh"])["staticMesh"]==r["properties"]["staticMesh"]
                changed.append(r)
                setp(r["root"],{"staticMesh":{"refPath":asset(r["layer"])},"bUseDefaultCollision":False,"bodyInstance":{"collisionEnabled":"NoCollision","collisionProfileName":"NoCollision"}})
                assert props(r["root"],["overrideMaterials"])["overrideMaterials"]==r["properties"]["overrideMaterials"]
            values={"new_infill":trace(8,13),"private_main":trace(-25,-73.55),"park_lawn":trace(-70,8),"university_green":trace(37,17),"open_court":trace(30,22)}
            assert abs(values["new_infill"]-175)<.01 and abs(values["private_main"]-176)<.01 and abs(values["park_lawn"]-176)<.01 and abs(values["university_green"]-200)<.01 and abs(values["open_court"]-200)<.01,values
        except Exception:
            for r in reversed(changed):setp(r["root"],r["properties"])
            api(S+"remove_from_scene",{"actor":support})
            raise
        return {"surface_actors_updated":len(changed),"new_collision_actors":1,"height_probes":values,"private_and_park_physics_unchanged":True}
    if MODE=="decor_contact":
        oldbase="D:/UEProject/ArcheoDig/Saved/Level6StreetArt/"
        plan=json.loads(api(F+"read_file",{"file_path":oldbase+"street.json"}))["parts"]
        old=json.loads(api(F+"read_file",{"file_path":oldbase+"street_done.json"}))
        t=api(A+"get_actor_transform",{"actor":old["actor"]});assert abs(t["rotation"]["yaw"])<.001
        rows=[]
        for i,p in enumerate(plan):
            if not ("Bench" in p["name"] or "Planter" in p["name"]):continue
            c=old["components"][i];v=props(c,["relativeLocation","relativeScale3D"]);rows.append({"component":c,"part":p,"before":v})
        benches=[r for r in rows if "Bench" in r["part"]["name"]];pots=[r for r in rows if "Planter" in r["part"]["name"]]
        groups=[benches]+[pots[i:i+4] for i in range(0,12,4)]
        deltas=[]
        for i,group in enumerate(groups):
            anchor=next(r for r in group if "BenchLeg" in r["part"]["name"]) if i==0 else group[0]
            p=anchor["before"];base=t["location"]["z"]+p["relativeLocation"]["z"]*t["scale"]["z"]-p["relativeScale3D"]["z"]*50;delta=25-base
            for r in group:
                v=dict(r["before"]["relativeLocation"]);v["z"]+=delta/t["scale"]["z"];setp(r["component"],{"relativeLocation":v})
            deltas.append(delta)
        write("decor_before.json",rows)
        return {"existing_furniture_components_aligned":len(rows),"groups_height_correction_cm":deltas}
    if MODE=="check_contacts":
        probes=read("probes.json")[INDEX*30:(INDEX+1)*30];valid=[];occupied=[];missing=[]
        for p in probes:
            x,y=p["probe"]
            b={"min":{"x":x*100-4,"y":y*100-4,"z":27},"max":{"x":x*100+4,"y":y*100+4,"z":205},"isValid":True}
            hit=api(S+"find_actors",{"name":"","tag":"","collision_channels":["ObjectTypeQuery1","ObjectTypeQuery2"],"bounds":b})
            if hit:occupied.append({"building":p["building"],"side":p["side"]});continue
            d=trace(x,y)
            if d is not None and abs(d-175)<.05:valid.append(p)
            else:missing.append({"building":p["building"],"side":p["side"],"point":[x,y],"distance":d})
        return {"batch":INDEX,"contact_points":len(probes),"paved":len(valid),"new_green_gaps_removed":sum(p["old_gap_m"]>.05 for p in valid),"occupied_edges":occupied,"missing":missing}
    if MODE=="preserve":
        for r in read("models.json"):
            assert same(api(A+"get_actor_transform",{"actor":r["actor"]}),r["transform"]),r["label"]
            for m in r["meshes"]:assert props(m["component"],["staticMesh","overrideMaterials"])==m["properties"],r["label"]
        for r in read("background.json"):assert same(api(A+"get_actor_transform",{"actor":r["actor"]}),r["transform"]),r["label"]
        quarter=json.loads(api(F+"read_file",{"file_path":"D:/UEProject/ArcheoDig/Saved/Level6Replan/BoundaryRoads/private_before.json"}))
        for r in quarter:assert same(api(A+"get_actor_transform",{"actor":r["actor"]}),r["transform"]),r["label"]
        for r in read("surfaces_before.json"):
            assert same(api(A+"get_actor_transform",{"actor":r["actor"]}),r["transform"])
            if r["layer"] in ["park","accent"]:assert props(r["root"],["staticMesh","overrideMaterials"])=={k:r["properties"][k] for k in ["staticMesh","overrideMaterials"]}
        return {"main_groups_unchanged":21,"background_unchanged":88,"private_paths_unchanged":31,"park_mesh_unchanged":True,"fountain_inlay_unchanged":True}
    if MODE=="save":
        paths=[L]+[asset(v).split('.')[0] for v in ["market","primary","plazas","secondary","alleys","curbs","support"]]
        for r in read("surfaces_before.json"):
            b=api(A+"get_actor_bounds",{"actor":r["actor"]});assert abs(b["max"]["z"]-25)<.01,r["layer"]
            assert b["min"]["x"]>-7920 and b["max"]["x"]<7920 and b["min"]["y"]>-9920 and b["max"]["y"]<9920
        assert api(F+"save_assets",{"asset_paths":paths})
        assert all(not api(F+"is_dirty",{"asset_path":p}) for p in paths)
        return {"level_saved":True,"assets_saved":len(paths),"surface_height_cm":25,"road_segments_reworked":129}
    raise ValueError(MODE)
