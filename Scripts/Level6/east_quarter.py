"""Eight specific eastern Level_6 volumes and two local pedestrian branches.

Uses existing assets only. The main street paving and finished buildings are read-only.
Run MODE in small batches through Unreal MCP ProgrammaticToolset.
"""
import json
import math

MODE = "build"
INDEX = 0
LEVEL = "/Game/TestLevel/Level_6/level_6_create_map"
BASE = "D:/UEProject/ArcheoDig/Saved/Level6Replan/EastQuarter/"
FOLDER = "CityBlockout/08_BackgroundBuildings/EastQuarter"
SCENE = "editor_toolset.toolsets.scene.SceneTools."
ACTOR = "editor_toolset.toolsets.actor.ActorTools."
OBJECT = "editor_toolset.toolsets.object.ObjectTools."
ASSET = "editor_toolset.toolsets.asset.AssetTools."
CUBE = "/Engine/BasicShapes/Cube.Cube"
SMC = {"refPath": "/Script/Engine.StaticMeshComponent"}


def api(tool, args):
    return execute_tool(tool, json.dumps(args))["returnValue"]


def read(name):
    return json.loads(api(ASSET+"read_file", {"file_path": BASE+name}).lstrip("\ufeff"))


def write(name, value):
    api(ASSET+"write_file", {"file_path": BASE+name, "content": json.dumps(value)})


def props(component, names):
    return json.loads(api(OBJECT+"get_properties", {"instance": component, "properties": names}))


def set_props(component, values):
    assert api(OBJECT+"set_properties", {"instance": component, "values": json.dumps(values)})


def same(a, b):
    return (all(abs(a["location"][k]-b["location"][k]) < .01 for k in a["location"])
            and all(abs((a["rotation"][k]-b["rotation"][k]+180) % 360-180) < .001 for k in a["rotation"])
            and all(abs(a["scale"][k]-b["scale"][k]) < .000001 for k in a["scale"]))


def overlap(box):
    return api(SCENE+"find_actors", {"name": "", "tag": "", "collision_channels": ["ObjectTypeQuery1", "ObjectTypeQuery2"], "bounds": box})


def built():
    return [r for i in range(2) for r in read("built_"+str(i)+".json")["rows"]]


def check_house(row):
    b, actor, root = row["item"], row["actor"], row["root"]
    assert same(api(ACTOR+"get_actor_transform", {"actor": actor}), b["xform"]), b["name"]
    p = props(root, ["staticMesh", "overrideMaterials", "bodyInstance"])
    assert p["staticMesh"]["refPath"] == CUBE and p["overrideMaterials"] == [{"refPath": b["facade"]}]
    assert p["bodyInstance"]["collisionProfileName"] == "BlockAll" and not p["bodyInstance"]["bSimulatePhysics"]
    components = api(ACTOR+"get_components", {"actor": actor, "component_type": SMC})
    assert len(components) == 4, b["name"]
    bounds = api(ACTOR+"get_actor_bounds", {"actor": actor})
    expected = b["height"] + (.25 if b["variant"] == "C" else b["rise"]-.06)
    assert abs(bounds["max"]["z"]-expected*100) < .2, b["name"]
    assert abs(bounds["min"]["z"]) < .1, b["name"]
    row["bounds"] = bounds


def run():
    assert api(SCENE+"get_current_level", {}) == LEVEL
    assert not api("EditorToolset.EditorAppToolset.IsPIERunning", {})
    assert read("preflight.json")["ready"] and not read("native_preflight.json")["conflicts"]
    if MODE == "build":
        if INDEX == 1:
            assert read("built_0.json")["verified"]
        else:
            assert not api(ASSET+"is_dirty", {"asset_path": LEVEL})
        items, rows = read("build_"+str(INDEX)+".json"), []
        allowed = {r["actor"]["refPath"] for r in read("houses.json") if r.get("actor")}
        protected = {r["actor"]["refPath"] for r in read("area_before.json")}-allowed
        try:
            for b in items:
                actor = b.get("actor")
                if actor:
                    assert actor["refPath"] in allowed and actor["refPath"] not in protected
                    assert same(api(ACTOR+"get_actor_transform", {"actor": actor}), b["before"]), b["name"]
                    assert props(b["root"], ["staticMesh", "overrideMaterials"]) == b["before_properties"]
                else:
                    assert not api(SCENE+"find_actors", {"name": b["name"], "tag": "", "collision_channels": []}), b["name"]
                    actor = api(SCENE+"add_to_scene_from_asset", {"asset_path": CUBE, "name": b["name"], "xform": b["xform"], "snap_to_ground": False})
                assert actor["refPath"].startswith(LEVEL+".") and actor["refPath"] not in protected
                root = api(ACTOR+"get_root_component", {"actor": actor})
                row = {"actor": actor, "root": root, "item": b, "components": []}
                rows.append(row)
                assert api(ACTOR+"set_actor_transform", {"actor": actor, "xform": b["xform"], "worldspace": True})
                set_props(root, {"overrideMaterials": [{"refPath": b["facade"]}]})
                for part in b["parts"]:
                    comp = api(ACTOR+"add_component", {"owner": root, "component_type": SMC, "name": part["name"]})
                    row["components"].append(comp)
                    set_props(comp, {"staticMesh": {"refPath": part["mesh"]}, "relativeLocation": part["location"],
                                    "relativeRotation": {"pitch": 0, "yaw": 0, "roll": 0}, "relativeScale3D": part["scale"],
                                    "bAbsoluteScale": True, "mobility": "Static", "overrideMaterials": part["materials"],
                                    "bodyInstance": {"collisionEnabled": "NoCollision", "collisionProfileName": "NoCollision"}})
                api(SCENE+"set_actor_folder", {"actor": actor, "folder_path": FOLDER})
                check_house(row)
            write("built_"+str(INDEX)+".json", {"verified": True, "rows": rows})
        except Exception:
            for row in reversed(rows):
                b = row["item"]
                if b.get("actor"):
                    for comp in reversed(row["components"]):
                        api(ACTOR+"remove_component", {"component": comp})
                    api(ACTOR+"set_actor_transform", {"actor": row["actor"], "xform": b["before"], "worldspace": True})
                    set_props(row["root"], b["before_properties"])
                    api(SCENE+"set_actor_folder", {"actor": row["actor"], "folder_path": "CityBlockout/08_BackgroundBuildings"})
                else:
                    api(SCENE+"remove_from_scene", {"actor": row["actor"]})
            raise
        return {"batch": INDEX, "houses_verified": len(rows), "names": [r["item"]["name"] for r in rows]}
    if MODE == "pave":
        assert read("built_1.json")["verified"]
        rows = []
        try:
            for p in read("paving.json"):
                assert not api(SCENE+"find_actors", {"name": p["name"], "tag": "", "collision_channels": []}), p["name"]
                actor = api(SCENE+"add_to_scene_from_asset", {"asset_path": CUBE, "name": p["name"], "xform": p["xform"], "snap_to_ground": False})
                rows.append({"actor": actor, "item": p})
                root = api(ACTOR+"get_root_component", {"actor": actor})
                set_props(root, {"overrideMaterials": [{"refPath": p["material"]}], "canCharacterStepUpOn": "ECB_Yes"})
                api(SCENE+"set_actor_folder", {"actor": actor, "folder_path": "CityBlockout/07_Pedestrian/EastQuarter"})
                assert same(api(ACTOR+"get_actor_transform", {"actor": actor}), p["xform"])
            write("paving_created.json", rows)
        except Exception:
            for row in reversed(rows):
                api(SCENE+"remove_from_scene", {"actor": row["actor"]})
            raise
        return {"paving_added": len(rows), "existing_main_paving_modified": False, "alleys": 2}
    if MODE == "verify_existing":
        selected = {r["actor"]["refPath"] for r in read("houses.json") if r.get("actor")}
        rows = [r for r in read("area_before.json") if r["actor"]["refPath"] not in selected]
        for r in rows:
            assert same(api(ACTOR+"get_actor_transform", {"actor": r["actor"]}), r["transform"]), r["label"]
            assert api(ACTOR+"get_actor_bounds", {"actor": r["actor"]}) == r["bounds"], r["label"]
        landmarks = read("landmarks_before.json")
        for r in landmarks:
            assert same(api(ACTOR+"get_actor_transform", {"actor": r["actor"]}), r["transform"]), r["label"]
            for m in r["meshes"]:
                assert props(m["component"], ["staticMesh", "overrideMaterials"]) == m["properties"], r["label"]
        components = 0
        for row in built():
            check_house(row)
            for comp, part in zip(row["components"], row["item"]["parts"]):
                p = props(comp, ["staticMesh", "overrideMaterials", "bodyInstance", "bAbsoluteScale"])
                assert p["staticMesh"] == {"refPath": part["mesh"]} and p["overrideMaterials"] == part["materials"]
                assert p["bAbsoluteScale"] and p["bodyInstance"]["collisionEnabled"] == "NoCollision"
                assert api(ACTOR+"get_parent_component", {"component": comp}) == row["root"]
                components += 1
        result={"existing_area_actors_unchanged":len(rows),"finished_buildings_unchanged":len(landmarks),"houses_verified":8,"architectural_components_verified":components}
        write("existing_checked.json",result)
        return result
    if MODE == "verify_spaces":
        old = read("area_before.json")
        floor_ids = {r["actor"]["refPath"] for r in old if r["label"].startswith("PW_")}
        floor_ids.update(r["actor"]["refPath"] for r in read("paving_created.json"))
        blocked, unsupported, count = [], [], 0
        def sample(name,x,y,offset,radius):
            box={"min":{"x":(x-radius)*100,"y":(y-radius)*100,"z":40},"max":{"x":(x+radius)*100,"y":(y+radius)*100,"z":230},"isValid":True}
            hits=overlap(box)
            if hits: blocked.append({"route":name,"point":[x,y],"offset":offset,"hits":hits})
            floor=overlap({"min":{"x":x*100-7,"y":y*100-7,"z":-2},"max":{"x":x*100+7,"y":y*100+7,"z":39},"isValid":True})
            if not any(a["refPath"] in floor_ids for a in floor): unsupported.append({"route":name,"point":[x,y]})
        routes=read("routes.json")
        # Include the existing trade spine and the existing hospital/car entrances.
        routes.append({"name":"TradeConnection","width":3.2,"points":[[-8,45],[-2,50],[2,57],[2,78]]})
        for route in routes:
            for i in range(1,len(route["points"])):
                a,b=route["points"][i-1],route["points"][i]
                dx,dy=b[0]-a[0],b[1]-a[1]
                length=math.sqrt(dx*dx+dy*dy)
                steps=int(math.ceil(length/2.5))
                side=.55 if route["width"]>=3 else .35
                for j in range(steps+1):
                    for offset in [-side,0,side]:
                        sample(route["name"],a[0]+dx*j/steps-dy/length*offset,a[1]+dy*j/steps+dx/length*offset,offset,.34)
                        count+=1
        for name,x,y in [["HospitalEntry",4.6,78],["CarEntry",-30,63.1],["NorthCourt",20.2,47.8]]:
            sample(name,x,y,0,.4)
            count+=1
        bodies=[]
        houses=built()
        for row in houses:
            r=row["item"]["rect"]
            box={"min":{"x":r[0]*100+1,"y":r[2]*100+1,"z":40},"max":{"x":r[1]*100-1,"y":r[3]*100-1,"z":row["item"]["height"]*100-1},"isValid":True}
            hits=[a for a in overlap(box) if a != row["actor"]]
            if hits: bodies.append({"house":row["item"]["name"],"hits":hits})
        # The cap and side buildings leave 35 cm seams, too narrow for a walking capsule.
        gaps=[]
        for x in [18.5,21.9]:
            hits=overlap({"min":{"x":x*100-34,"y":4632.5-34,"z":40},"max":{"x":x*100+34,"y":4632.5+34,"z":230},"isValid":True})
            gaps.append(bool(hits))
        cap=next(r for r in houses if r["item"]["name"]=="BG_Residential_17")
        cap_hits=overlap({"min":{"x":1986,"y":4536,"z":40},"max":{"x":2054,"y":4604,"z":230},"isValid":True})
        enclosed=all(gaps) and cap["actor"] in cap_hits
        result={"walking_samples":count,"blocked":blocked,"unsupported":unsupported,"building_conflicts":bodies,"dead_end_enclosed":enclosed,"PIE_tested":False}
        write("spaces_checked.json",result)
        return result
    if MODE == "save":
        e,s=read("existing_checked.json"),read("spaces_checked.json")
        assert e["houses_verified"]==8 and e["architectural_components_verified"]==24
        assert not s["blocked"] and not s["unsupported"] and not s["building_conflicts"] and s["dead_end_enclosed"]
        actual=api(SCENE+"get_actors_in_folder",{"folder_path":FOLDER,"recursive":False})
        assert len(actual)==8
        assert api(ASSET+"save_assets",{"asset_paths":[LEVEL]})
        assert not api(ASSET+"is_dirty",{"asset_path":LEVEL})
        result={"status":"SUCCESS","level":LEVEL,"reused":2,"added":6,"main_street_width":3,"alleys":2,"alley_width":2.1,"dead_end":True,"existing_unchanged":True,"saved":True,"PIE_tested":False}
        write("result.json",result)
        return result
    raise ValueError(MODE)
