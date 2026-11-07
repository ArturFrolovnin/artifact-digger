"""One Level_6 composition pass: explicit A/B/C/D plans, checked sector saves.

No asset creation, imports, finished-model edits, or general city generation.
"""
import json
import math

MODE = "build"
SECTOR = "A"
LEVEL = "/Game/TestLevel/Level_6/level_6_create_map"
BASE = "D:/UEProject/ArcheoDig/Saved/Level6Replan/GlobalFill/"
FOLDER = "CityBlockout/08_BackgroundBuildings/GlobalFill"
PAVING = "CityBlockout/07_Pedestrian/GlobalFill"
SCENE = "editor_toolset.toolsets.scene.SceneTools."
ACTOR = "editor_toolset.toolsets.actor.ActorTools."
OBJECT = "editor_toolset.toolsets.object.ObjectTools."
ASSET = "editor_toolset.toolsets.asset.AssetTools."
CUBE = "/Engine/BasicShapes/Cube.Cube"
SMC = {"refPath": "/Script/Engine.StaticMeshComponent"}


def api(t, a):
    return execute_tool(t, json.dumps(a))["returnValue"]


def read(n):
    return json.loads(api(ASSET+"read_file", {"file_path": BASE+n}).lstrip("\ufeff"))


def write(n, v):
    api(ASSET+"write_file", {"file_path": BASE+n, "content": json.dumps(v)})


def props(c, names):
    return json.loads(api(OBJECT+"get_properties", {"instance": c, "properties": names}))


def set_props(c, values):
    assert api(OBJECT+"set_properties", {"instance": c, "values": json.dumps(values)})


def same(a, b):
    return (all(abs(a["location"][k]-b["location"][k]) < .01 for k in a["location"])
            and all(abs((a["rotation"][k]-b["rotation"][k]+180) % 360-180) < .001 for k in a["rotation"])
            and all(abs(a["scale"][k]-b["scale"][k]) < .000001 for k in a["scale"]))


def native(box):
    return api(SCENE+"find_actors", {"name": "", "tag": "", "collision_channels": ["ObjectTypeQuery1", "ObjectTypeQuery2"], "bounds": box})


def poly(t):
    angle=t["rotation"]["yaw"]*math.pi/180
    c,s=math.cos(angle),math.sin(angle)
    dx,dy=t["scale"]["x"]/2,t["scale"]["y"]/2
    x,y=t["location"]["x"]/100,t["location"]["y"]/100
    return [[x+c*u*dx-s*v*dy,y+s*u*dx+c*v*dy] for u,v in [[-1,-1],[1,-1],[1,1],[-1,1]]]


def overlaps(a,b):
    for p in [a,b]:
        for i in range(len(p)):
            v,w=p[i],p[(i+1)%len(p)]
            n=[v[1]-w[1],w[0]-v[0]]
            aa=[q[0]*n[0]+q[1]*n[1] for q in a]
            bb=[q[0]*n[0]+q[1]*n[1] for q in b]
            if min(aa)>=max(bb)-.00001 or min(bb)>=max(aa)-.00001:
                return False
    return True


def check_house(row):
    h,a,c=row["item"],row["actor"],row["root"]
    assert same(api(ACTOR+"get_actor_transform", {"actor": a}),h["xform"]),h["name"]
    p=props(c,["staticMesh","overrideMaterials","bodyInstance"])
    assert p["staticMesh"]["refPath"]==CUBE and p["overrideMaterials"]==[{"refPath":h["facade"]}]
    assert p["bodyInstance"]["collisionProfileName"]=="BlockAll" and not p["bodyInstance"]["bSimulatePhysics"]
    assert len(api(ACTOR+"get_components",{"actor":a,"component_type":SMC}))==3,h["name"]
    bounds=api(ACTOR+"get_actor_bounds",{"actor":a})
    expected=h["height"]+(.25 if h["variant"]=="C" else h["rise"]-.06)
    assert abs(bounds["min"]["z"])<.1 and abs(bounds["max"]["z"]-expected*100)<.2,h["name"]
    row["bounds"]=bounds


def run():
    assert api(SCENE+"get_current_level",{})==LEVEL
    assert not api("EditorToolset.EditorAppToolset.IsPIERunning",{})
    assert read("preflight.json")["ready"] and not read("native_preflight.json")["conflicts"]
    if MODE=="build":
        assert not api(ASSET+"is_dirty",{"asset_path":LEVEL})
        if SECTOR!="A":
            previous={"B":"A","C":"B","D":"C","C2":"D"}[SECTOR]
            assert read("saved_"+previous+".json")["saved"]
        allowed={h["actor"]["refPath"] for h in read("houses.json") if h.get("actor")}
        protected={r["actor"]["refPath"] for r in read("models_before.json")+read("background_before.json")}-allowed
        rows=[]
        try:
            for h in read("houses_"+SECTOR+".json"):
                a=h.get("actor")
                if a:
                    assert a["refPath"] in allowed and a["refPath"] not in protected
                    assert same(api(ACTOR+"get_actor_transform",{"actor":a}),h["before"]),h["name"]
                    assert props(h["root"],["staticMesh","overrideMaterials"])==h["before_properties"]
                else:
                    assert not api(SCENE+"find_actors",{"name":h["name"],"tag":"","collision_channels":[]}),h["name"]
                    a=api(SCENE+"add_to_scene_from_asset",{"asset_path":CUBE,"name":h["name"],"xform":h["xform"],"snap_to_ground":False})
                assert a["refPath"].startswith(LEVEL+".") and a["refPath"] not in protected
                c=api(ACTOR+"get_root_component",{"actor":a})
                row={"actor":a,"root":c,"item":h,"components":[]}
                rows.append(row)
                assert api(ACTOR+"set_actor_transform",{"actor":a,"xform":h["xform"],"worldspace":True})
                set_props(c,{"overrideMaterials":[{"refPath":h["facade"]}]})
                for part in h["parts"]:
                    component=api(ACTOR+"add_component",{"owner":c,"component_type":SMC,"name":part["name"]})
                    row["components"].append(component)
                    set_props(component,{"staticMesh":{"refPath":part["mesh"]},"relativeLocation":part["location"],"relativeRotation":{"pitch":0,"yaw":0,"roll":0},"relativeScale3D":part["scale"],"bAbsoluteScale":True,"mobility":"Static","overrideMaterials":part["materials"],"bodyInstance":{"collisionEnabled":"NoCollision","collisionProfileName":"NoCollision"}})
                api(SCENE+"set_actor_folder",{"actor":a,"folder_path":FOLDER+"/"+SECTOR})
                check_house(row)
            write("built_"+SECTOR+".json",rows)
        except Exception:
            for row in reversed(rows):
                h=row["item"]
                if h.get("actor"):
                    for c in reversed(row["components"]):api(ACTOR+"remove_component",{"component":c})
                    api(ACTOR+"set_actor_transform",{"actor":row["actor"],"xform":h["before"],"worldspace":True})
                    set_props(row["root"],h["before_properties"])
                    api(SCENE+"set_actor_folder",{"actor":row["actor"],"folder_path":"CityBlockout/08_BackgroundBuildings"})
                else:api(SCENE+"remove_from_scene",{"actor":row["actor"]})
            raise
        return {"sector":SECTOR,"houses":len(rows),"new":sum(not r["item"].get("actor") for r in rows),"reused":sum(bool(r["item"].get("actor")) for r in rows)}
    if MODE=="pave":
        assert read("built_"+SECTOR+".json")
        rows=[]
        try:
            for p in read("paving_"+SECTOR+".json"):
                assert not api(SCENE+"find_actors",{"name":p["name"],"tag":"","collision_channels":[]}),p["name"]
                a=api(SCENE+"add_to_scene_from_asset",{"asset_path":CUBE,"name":p["name"],"xform":p["xform"],"snap_to_ground":False})
                rows.append({"actor":a,"item":p})
                c=api(ACTOR+"get_root_component",{"actor":a})
                set_props(c,{"overrideMaterials":[{"refPath":p["material"]}],"canCharacterStepUpOn":"ECB_Yes"})
                api(SCENE+"set_actor_folder",{"actor":a,"folder_path":PAVING+"/"+SECTOR})
                assert same(api(ACTOR+"get_actor_transform",{"actor":a}),p["xform"]),p["name"]
            write("paving_created_"+SECTOR+".json",rows)
        except Exception:
            for r in reversed(rows):api(SCENE+"remove_from_scene",{"actor":r["actor"]})
            raise
        return {"sector":SECTOR,"new_paving":len(rows)}
    if MODE=="verify":
        houses=read("built_"+SECTOR+".json")
        paving=read("paving_created_"+SECTOR+".json")
        conflicts=[]
        for row in houses:
            check_house(row)
            h=row["item"];r=h["rect"]
            box={"min":{"x":r[0]*100+1,"y":r[2]*100+1,"z":40},"max":{"x":r[1]*100-1,"y":r[3]*100-1,"z":h["height"]*100-1},"isValid":True}
            hits=[a for a in native(box) if a!=row["actor"]]
            if hits:conflicts.append({"house":h["name"],"hits":hits})
            for c,part in zip(row["components"],h["parts"]):
                p=props(c,["staticMesh","overrideMaterials","bodyInstance","bAbsoluteScale"])
                assert p["staticMesh"]=={"refPath":part["mesh"]} and p["overrideMaterials"]==part["materials"]
                assert p["bAbsoluteScale"] and p["bodyInstance"]["collisionEnabled"]=="NoCollision"
        floor_ids={r["actor"]["refPath"] for r in paving}
        for i in range(3):floor_ids.update(r["actor"]["refPath"] for r in read("roads_before_"+str(i)+".json"))
        blocked,unsupported,segments,floor_samples=[],[],0,0
        for route in read("routes_"+SECTOR+".json"):
            for i in range(1,len(route["points"])):
                a,b=route["points"][i-1],route["points"][i]
                dx,dy=b[0]-a[0],b[1]-a[1]
                t={"location":{"x":(a[0]+b[0])*50,"y":(a[1]+b[1])*50,"z":0},"rotation":{"yaw":math.atan2(dy,dx)*180/math.pi},"scale":{"x":math.sqrt(dx*dx+dy*dy),"y":1.2}}
                p=poly(t)
                box={"min":{"x":min(q[0] for q in p)*100,"y":min(q[1] for q in p)*100,"z":40},"max":{"x":max(q[0] for q in p)*100,"y":max(q[1] for q in p)*100,"z":230},"isValid":True}
                for hit in native(box):
                    bounds=api(ACTOR+"get_actor_bounds",{"actor":hit})
                    q=[[bounds[k]["x"]/100,bounds[j]["y"]/100] for k,j in [["min","min"],["max","min"],["max","max"],["min","max"]]]
                    if overlaps(p,q):blocked.append({"route":route["name"],"actor":hit,"label":api(ACTOR+"get_label",{"actor":hit})})
                for u in [0,.25,.5,.75,1]:
                    x,y=(a[0]+dx*u)*100,(a[1]+dy*u)*100
                    hits=native({"min":{"x":x-8,"y":y-8,"z":-2},"max":{"x":x+8,"y":y+8,"z":39},"isValid":True})
                    if not any(h["refPath"] in floor_ids for h in hits):unsupported.append({"route":route["name"],"point":[x/100,y/100]})
                    floor_samples+=1
                segments+=1
        actual=api(SCENE+"get_actors_in_folder",{"folder_path":FOLDER+"/"+SECTOR,"recursive":False})
        actual_p=api(SCENE+"get_actors_in_folder",{"folder_path":PAVING+"/"+SECTOR,"recursive":False})
        assert {a["refPath"] for a in actual}=={r["actor"]["refPath"] for r in houses}
        assert {a["refPath"] for a in actual_p}=={r["actor"]["refPath"] for r in paving}
        result={"sector":SECTOR,"houses":len(houses),"new":sum(not r["item"].get("actor") for r in houses),"reused":sum(bool(r["item"].get("actor")) for r in houses),"paving":len(paving),"segments":segments,"floor_samples":floor_samples,"body_conflicts":conflicts,"blocked":blocked,"unsupported":unsupported}
        write("checked_"+SECTOR+".json",result)
        return result
    if MODE=="save":
        r=read("checked_"+SECTOR+".json")
        assert not r["body_conflicts"] and not r["blocked"] and not r["unsupported"]
        assert api(ASSET+"save_assets",{"asset_paths":[LEVEL]})
        assert not api(ASSET+"is_dirty",{"asset_path":LEVEL})
        r["saved"]=True
        write("saved_"+SECTOR+".json",r)
        return {"sector":SECTOR,"new":r["new"],"reused":r["reused"],"saved":True}
    if MODE=="preserve_models":
        rows=read("models_before.json")
        for r in rows:
            assert same(api(ACTOR+"get_actor_transform",{"actor":r["actor"]}),r["transform"]),r["label"]
            for m in r["meshes"]:assert props(m["component"],["staticMesh","overrideMaterials"])==m["properties"],r["label"]
        allowed={h["actor"]["refPath"] for h in read("houses.json") if h.get("actor")}
        bg=[r for r in read("background_before.json") if r["actor"]["refPath"] not in allowed]
        for r in bg:
            assert same(api(ACTOR+"get_actor_transform",{"actor":r["actor"]}),r["transform"]),r["label"]
            assert api(ACTOR+"get_actor_bounds",{"actor":r["actor"]})==r["bounds"],r["label"]
        result={"landmarks_unchanged":len(rows),"previous_background_unchanged":len(bg)}
        write("models_checked.json",result)
        return result
    if MODE=="preserve_roads":
        rows=read("roads_before_"+SECTOR+".json")
        for r in rows:assert same(api(ACTOR+"get_actor_transform",{"actor":r["actor"]}),r["transform"]),r["label"]
        write("roads_checked_"+SECTOR+".json",{"unchanged":len(rows)})
        return {"batch":SECTOR,"paths_unchanged":len(rows)}
    if MODE=="final":
        saved=[read("saved_"+s+".json") for s in ["A","B","C","D","C2"]]
        assert all(r["saved"] for r in saved)
        assert read("models_checked.json")["landmarks_unchanged"]==21
        assert sum(read("roads_checked_"+str(i)+".json")["unchanged"] for i in range(3))==214
        actual=api(SCENE+"get_actors_in_folder",{"folder_path":"CityBlockout/08_BackgroundBuildings","recursive":True})
        assert len(actual)==60
        assert sum(r["new"] for r in saved)==40 and sum(r["reused"] for r in saved)==5
        assert api(ASSET+"save_assets",{"asset_paths":[LEVEL]})
        assert not api(ASSET+"is_dirty",{"asset_path":LEVEL})
        result={"status":"SUCCESS","new_buildings":40,"reused":5,"sectors":4,"new_routes":len(read("routes.json")),"new_courts":len(read("courts.json")),"existing_paths_unchanged":214,"main_buildings_unchanged":True,"saved":True,"PIE_tested":False}
        write("result.json",result)
        return result
    raise ValueError(MODE)
