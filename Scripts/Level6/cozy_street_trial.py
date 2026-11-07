"""Seven specific background houses around the existing central pedestrian route.

Run small batches through Unreal MCP. No mesh asset or finished building edits.
"""
import json
import math

MODE = "build"
INDEX = 0
LEVEL = "/Game/TestLevel/Level_6/level_6_create_map"
BASE = "D:/UEProject/ArcheoDig/Saved/Level6Replan/CozyStreet/"
FOLDER = "CityBlockout/08_BackgroundBuildings/CozyStreet"
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


def find(name):
    return api(SCENE+"find_actors", {"name": name, "tag": "", "collision_channels": []})


def overlap(box):
    return api(SCENE+"find_actors", {"name": "", "tag": "", "collision_channels": ["ObjectTypeQuery1", "ObjectTypeQuery2"], "bounds": box})


def verify_house(row):
    b, actor, root = row["item"], row["actor"], row["root"]
    assert same(api(ACTOR+"get_actor_transform", {"actor": actor}), b["xform"]), b["name"]
    p = props(root, ["staticMesh", "overrideMaterials", "bodyInstance"])
    assert p["staticMesh"]["refPath"] == CUBE and p["overrideMaterials"] == [{"refPath": b["facade"]}]
    assert p["bodyInstance"]["collisionProfileName"] == "BlockAll" and not p["bodyInstance"]["bSimulatePhysics"]
    components = api(ACTOR+"get_components", {"actor": actor, "component_type": SMC})
    assert len(components) == 1+len(b["parts"]), b["name"]
    bounds = api(ACTOR+"get_actor_bounds", {"actor": actor})
    expected = b["height"] + (.6 if b["variant"] == "C" else b["rise"]-.06)
    assert abs(bounds["max"]["z"]-expected*100) < .2, {"house": b["name"], "bounds": bounds, "expected": expected}
    assert abs(bounds["min"]["z"]) < .1, b["name"]
    row["bounds"] = bounds


def run():
    assert api(SCENE+"get_current_level", {}) == LEVEL
    assert read("preflight.json")["ready"] and not read("native_preflight.json")["conflicts"]
    if MODE == "build":
        if INDEX == 1:
            assert read("built_0.json")["verified"]
        items, rows = read("build_"+str(INDEX)+".json"), []
        protected = set(read("protected_paths.json"))
        allowed = {r["actor"]["refPath"] for r in read("buildings.json") if r.get("actor")}
        try:
            for b in items:
                actor = b.get("actor")
                if actor:
                    assert actor["refPath"] in allowed and actor["refPath"] not in protected
                    assert same(api(ACTOR+"get_actor_transform", {"actor": actor}), b["before"]), b["name"]
                    assert props(b["root"], ["staticMesh", "overrideMaterials"]) == b["before_properties"]
                else:
                    assert not find(b["name"]), b["name"]
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
                    assert api(ACTOR+"get_parent_component", {"component": comp}) == root
                api(SCENE+"set_actor_folder", {"actor": actor, "folder_path": FOLDER})
                verify_house(row)
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
        return {"batch": INDEX, "houses_verified": len(rows), "components": sum(len(r["components"]) for r in rows), "names": [r["item"]["name"] for r in rows]}
    if MODE == "pave":
        assert read("built_1.json")["verified"]
        rows = []
        try:
            for p in read("paving.json"):
                assert not find(p["name"]), p["name"]
                actor = api(SCENE+"add_to_scene_from_asset", {"asset_path": CUBE, "name": p["name"], "xform": p["xform"], "snap_to_ground": False})
                rows.append({"actor": actor, "item": p})
                root = api(ACTOR+"get_root_component", {"actor": actor})
                set_props(root, {"overrideMaterials": [{"refPath": p["material"]}], "canCharacterStepUpOn": "ECB_Yes"})
                api(SCENE+"set_actor_folder", {"actor": actor, "folder_path": "CityBlockout/07_Pedestrian/CozyStreet"})
                assert same(api(ACTOR+"get_actor_transform", {"actor": actor}), p["xform"])
            write("paving_created.json", rows)
        except Exception:
            for row in reversed(rows):
                api(SCENE+"remove_from_scene", {"actor": row["actor"]})
            raise
        return {"paving_added": len(rows), "alley_width": 1.8, "forecourt": True}
    if MODE == "verify_architecture":
        rows = [r for i in range(2) for r in read("built_"+str(i)+".json")["rows"]]
        checked = 0
        for row in rows:
            verify_house(row)
            for comp, part in zip(row["components"], row["item"]["parts"]):
                p = props(comp, ["staticMesh", "overrideMaterials", "bodyInstance", "bAbsoluteScale", "relativeLocation", "relativeScale3D", "mobility"])
                assert p["staticMesh"] == {"refPath": part["mesh"]} and p["overrideMaterials"] == part["materials"], part["name"]
                assert p["bAbsoluteScale"] and p["mobility"] == "Static", part["name"]
                assert p["bodyInstance"]["collisionEnabled"] == "NoCollision" and not p["bodyInstance"]["bSimulatePhysics"], part["name"]
                assert all(abs(p["relativeLocation"][k]-part["location"][k]) < .01 for k in part["location"]), part["name"]
                assert all(abs(p["relativeScale3D"][k]-part["scale"][k]) < .00001 for k in part["scale"]), part["name"]
                checked += 1
        result = {"houses": len(rows), "components_verified": checked, "collision_bodies": len(rows), "decorative_collision": False}
        write("architecture_checked.json", result)
        return result
    if MODE == "verify_existing":
        selected = {r["actor"]["refPath"] for r in read("buildings.json") if r.get("actor")}
        landmarks = read("landmark_before.json")
        unselected = [r for r in read("background_before.json") if r["actor"]["refPath"] not in selected]
        roads = read("road_before.json")
        for row in landmarks+unselected+roads:
            assert same(api(ACTOR+"get_actor_transform", {"actor": row["actor"]}), row["transform"]), row["label"]
            if row in landmarks:
                for mesh in row["meshes"]:
                    assert props(mesh["component"], ["staticMesh", "overrideMaterials"]) == mesh["properties"], row["label"]
            elif row in unselected:
                assert props(row["root"], ["staticMesh", "overrideMaterials"]) == row["properties"], row["label"]
        assert any(r["label"] == "RC_MainStreet" for r in roads)
        result = {"landmarks_unchanged": len(landmarks), "other_background_unchanged": len(unselected), "existing_paths_unchanged": len(roads), "residential_main_street_unchanged": True}
        write("existing_checked.json", result)
        return result
    if MODE == "verify_spaces":
        roads = read("road_before.json")
        paving = read("paving_created.json")
        floor_ids = {r["actor"]["refPath"] for r in roads+paving}
        blocked, unsupported, samples = [], [], []
        def sample(name, x, y, radius=.35, require_paving=True):
            box = {"min": {"x": (x-radius)*100, "y": (y-radius)*100, "z": 40}, "max": {"x": (x+radius)*100, "y": (y+radius)*100, "z": 230}, "isValid": True}
            hits = overlap(box)
            if hits:
                blocked.append({"space": name, "point": [x,y], "hits": hits})
            if require_paving:
                floor = overlap({"min": {"x": x*100-8, "y": y*100-8, "z": -2}, "max": {"x": x*100+8, "y": y*100+8, "z": 39}, "isValid": True})
                if not any(a["refPath"] in floor_ids for a in floor):
                    unsupported.append({"space": name, "point": [x,y]})
            samples.append([name,x,y])
        # Three parallel walking lanes, including the existing slight bends.
        route = [[1.5,-8],[-3,-1],[-7,8],[-8,21],[-8,45]]
        for i in range(1,len(route)):
            a,b = route[i-1],route[i]
            dx,dy=b[0]-a[0],b[1]-a[1]
            length=math.sqrt(dx*dx+dy*dy)
            steps=int(math.ceil(length/3))
            for j in range(steps+1):
                for side in [-.7,0,.7]:
                    sample("MainStreet", a[0]+dx*j/steps-dy/length*side, a[1]+dy*j/steps+dx/length*side)
        for j in range(7):
            sample("CafeAlley", -13.25+j, 6.2, .55)
        for p in [[-5.9,30.6],[-5.9,35.4],[-2.3,35.5],[-4,33],[-2.8,33]]:
            sample("GrahamForecourt", p[0],p[1],.3)
        # Existing main building entrances: no work was performed on their geometry.
        for p in [[8.8,-24],[-2.8,33],[-54.8,13]]:
            sample("LandmarkApproach",p[0],p[1],.3,False)
        bodies=[]
        houses = [r for i in range(2) for r in read("built_"+str(i)+".json")["rows"]]
        for row in houses:
            p=row["item"]["polygon"]
            box={"min":{"x":min(q[0] for q in p)*100+1,"y":min(q[1] for q in p)*100+1,"z":40},"max":{"x":max(q[0] for q in p)*100-1,"y":max(q[1] for q in p)*100-1,"z":row["item"]["height"]*100-1},"isValid":True}
            hits=[a for a in overlap(box) if a != row["actor"]]
            if hits:
                bodies.append({"house":row["item"]["name"],"hits":hits})
        main=next(r for r in roads if r["label"] == "RC_MainStreet")
        b=main["bounds"]
        private_hits=overlap({"min":{"x":b["min"]["x"]+1,"y":b["min"]["y"]+1,"z":40},"max":{"x":b["max"]["x"]-1,"y":b["max"]["y"]-1,"z":230},"isValid":True})
        result={"walking_samples":len(samples),"blocked":blocked,"unsupported":unsupported,"building_conflicts":bodies,"private_street_blockers":private_hits,"PIE_tested":False}
        write("spaces_checked.json",result)
        return result
    if MODE == "save":
        a,e,s=read("architecture_checked.json"),read("existing_checked.json"),read("spaces_checked.json")
        assert a["houses"] == 7 and a["components_verified"] == 95
        assert e["residential_main_street_unchanged"]
        assert not s["blocked"] and not s["unsupported"] and not s["building_conflicts"] and not s["private_street_blockers"]
        actual=api(SCENE+"get_actors_in_folder",{"folder_path":FOLDER,"recursive":False})
        assert len(actual)==7
        assert api(ASSET+"save_assets",{"asset_paths":[LEVEL]})
        assert not api(ASSET+"is_dirty",{"asset_path":LEVEL})
        result={"status":"SUCCESS","level":LEVEL,"existing_background_reused":5,"new_buildings":2,"variants":3,"street_width":3.2,"alley_width":1.8,"forecourt_added":True,"saved":True,"PIE_tested":False}
        write("result.json",result)
        return result
    raise ValueError(MODE)
