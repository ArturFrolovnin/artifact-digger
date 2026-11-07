"""Twelve specific Level_6 blockout volumes; existing scene actors are read-only.

Run small batches through Unreal MCP ProgrammaticToolset, selecting MODE/INDEX.
"""
import json

MODE = "preflight"
INDEX = 0
LEVEL = "/Game/TestLevel/Level_6/level_6_create_map"
BASE = "D:/UEProject/ArcheoDig/Saved/Level6Replan/BackgroundStage3/"
FOLDER = "CityBlockout/08_BackgroundBuildings"


def api(tool, args):
    return execute_tool(tool, json.dumps(args))


def read(name):
    return json.loads(api("editor_toolset.toolsets.asset.AssetTools.read_file", {"file_path": BASE+name})["returnValue"].lstrip("\ufeff"))


def write(name, data):
    api("editor_toolset.toolsets.asset.AssetTools.write_file", {"file_path": BASE+name, "content": json.dumps(data)})


def transform(actor):
    return api("editor_toolset.toolsets.actor.ActorTools.get_actor_transform", {"actor": actor})["returnValue"]


def matches(a, b):
    return (all(abs(a["location"][k]-b["location"][k]) < .01 for k in a["location"])
            and all(abs((a["rotation"][k]-b["rotation"][k]+180) % 360-180) < .001 for k in a["rotation"])
            and all(abs(a["scale"][k]-b["scale"][k]) < .000001 for k in a["scale"]))


def properties(component, names):
    return json.loads(api("editor_toolset.toolsets.object.ObjectTools.get_properties", {"instance": component, "properties": names})["returnValue"])


def overlap(box):
    return api("editor_toolset.toolsets.scene.SceneTools.find_actors", {
        "name": "", "tag": "", "collision_channels": ["ObjectTypeQuery1", "ObjectTypeQuery2"], "bounds": box})["returnValue"]


def run():
    assert api("editor_toolset.toolsets.scene.SceneTools.get_current_level", {})["returnValue"] == LEVEL
    assert read("preflight.json")["ready"]
    if MODE == "preflight":
        conflicts = []
        for item in read("items.json"):
            r = item["rect"]
            box = {"min": {"x": r[0]*100-5, "y": r[2]*100-5, "z": item["base"]*100+30},
                   "max": {"x": r[1]*100+5, "y": r[3]*100+5, "z": (item["base"]+item["height"])*100}, "isValid": True}
            hits = overlap(box)
            if hits:
                conflicts.append({"building": item["name"], "hits": hits})
        write("native_preflight.json", {"conflicts": conflicts})
        return {"candidates": 12, "conflicts": conflicts}
    if MODE == "create":
        assert not read("native_preflight.json")["conflicts"]
        items, created = read("create_"+str(INDEX)+".json"), []
        protected = set(read("protected_paths.json"))
        try:
            for item in items:
                found = api("editor_toolset.toolsets.scene.SceneTools.find_actors", {"name": item["name"], "tag": "", "collision_channels": []})["returnValue"]
                assert not found, item["name"]
                actor = api("editor_toolset.toolsets.scene.SceneTools.add_to_scene_from_asset", {
                    "asset_path": "/Engine/BasicShapes/Cube.Cube", "name": item["name"],
                    "xform": item["xform"], "snap_to_ground": False})["returnValue"]
                assert actor["refPath"].startswith(LEVEL+".") and actor["refPath"] not in protected
                created.append({"actor": actor, "item": item})
                component = api("editor_toolset.toolsets.actor.ActorTools.get_root_component", {"actor": actor})["returnValue"]
                assert api("editor_toolset.toolsets.object.ObjectTools.set_properties", {
                    "instance": component, "values": json.dumps({"overrideMaterials": [{"refPath": item["material"]}], "canCharacterStepUpOn": "ECB_No"})})["returnValue"]
                api("editor_toolset.toolsets.scene.SceneTools.set_actor_folder", {"actor": actor, "folder_path": FOLDER})
                assert matches(transform(actor), item["xform"]), item["name"]
                p = properties(component, ["staticMesh", "overrideMaterials", "bodyInstance"])
                assert p["staticMesh"]["refPath"] == "/Engine/BasicShapes/Cube.Cube"
                assert p["overrideMaterials"] == [{"refPath": item["material"]}]
                assert p["bodyInstance"]["collisionProfileName"] == "BlockAll" and not p["bodyInstance"]["bSimulatePhysics"]
                b = api("editor_toolset.toolsets.actor.ActorTools.get_actor_bounds", {"actor": actor})["returnValue"]
                assert abs(b["min"]["z"]-item["base"]*100) < .01
                assert abs(b["max"]["z"]-b["min"]["z"]-item["height"]*100) < .01
        except Exception:
            for row in reversed(created):
                api("editor_toolset.toolsets.scene.SceneTools.remove_from_scene", {"actor": row["actor"]})
            raise
        write("created_"+str(INDEX)+".json", created)
        actual = api("editor_toolset.toolsets.scene.SceneTools.get_actors_in_folder", {"folder_path": FOLDER, "recursive": False})["returnValue"]
        return {"batch": INDEX, "created": len(created), "actual_background_count": len(actual)}
    if MODE == "verify_existing":
        kind = "model" if INDEX < 5 else "road"
        batch = INDEX if INDEX < 5 else INDEX-5
        rows = read(kind+"_before_"+str(batch)+".json")
        for row in rows:
            assert matches(transform(row["actor"]), row["transform"]), row["label"]
            if kind == "model":
                for mesh in row["meshes"]:
                    assert properties(mesh["component"], ["staticMesh", "overrideMaterials"]) == mesh["properties"], row["label"]
        write("verified_"+str(INDEX)+".json", {"type": kind, "unchanged": len(rows)})
        return {"type": kind, "unchanged": len(rows), "batch": batch}
    if MODE == "check_spaces":
        blocked, unsupported = [], []
        for alley in read("alleys.json"):
            a, b = alley["a"], alley["b"]
            rx = .9 if abs(a[0]-b[0]) < .01 else 0
            ry = .9 if abs(a[1]-b[1]) < .01 else 0
            box = {"min": {"x": (min(a[0],b[0])-rx)*100, "y": (min(a[1],b[1])-ry)*100, "z": 40},
                   "max": {"x": (max(a[0],b[0])+rx)*100, "y": (max(a[1],b[1])+ry)*100, "z": 250}, "isValid": True}
            hits = overlap(box)
            if hits:
                blocked.append({"space": alley["name"], "hits": hits})
            for t in [0,.25,.5,.75,1]:
                x=(a[0]+(b[0]-a[0])*t)*100; y=(a[1]+(b[1]-a[1])*t)*100
                floor = overlap({"min": {"x": x-10, "y": y-10, "z": -5}, "max": {"x": x+10, "y": y+10, "z": 39}, "isValid": True})
                if not floor:
                    unsupported.append(alley["name"])
        court = read("courtyard.json")["point"]
        box={"min":{"x":court[0]*100-40,"y":court[1]*100-40,"z":40},"max":{"x":court[0]*100+40,"y":court[1]*100+40,"z":250},"isValid":True}
        if overlap(box):
            blocked.append({"space":"QuietCourtyard"})
        write("spaces_checked.json", {"alleys": 5, "blocked": blocked, "unsupported": unsupported, "courtyard_clear": not overlap(box)})
        return {"alleys": 5, "blocked": blocked, "unsupported": unsupported}
    if MODE == "check_bodies":
        created=[r for i in range(3) for r in read("created_"+str(i)+".json")]
        conflicts=[]
        for row in created:
            item=row["item"]; r=item["rect"]
            box={"min":{"x":r[0]*100+1,"y":r[2]*100+1,"z":item["base"]*100+30},
                 "max":{"x":r[1]*100-1,"y":r[3]*100-1,"z":(item["base"]+item["height"])*100-1},"isValid":True}
            other=[a for a in overlap(box) if a["refPath"]!=row["actor"]["refPath"]]
            if other:
                conflicts.append({"building":item["name"],"hits":other})
        main=None
        for i in range(5):
            for row in read("road_before_"+str(i)+".json"):
                if row["label"]=="RC_MainStreet":
                    main=row
        assert main
        b=main["bounds"]
        box={"min":{"x":b["min"]["x"]+1,"y":b["min"]["y"],"z":26},
             "max":{"x":b["max"]["x"]-1,"y":b["max"]["y"],"z":250},"isValid":True}
        main_hits=overlap(box)
        result={"checked":len(created),"conflicts":conflicts,"main_street_blockers":main_hits}
        write("bodies_checked.json",result)
        return result
    if MODE == "save":
        counts = read("input_counts.json")
        verified = [read("verified_"+str(i)+".json") for i in range(10)]
        assert sum(r["unchanged"] for r in verified if r["type"]=="model") == counts["models"]
        assert sum(r["unchanged"] for r in verified if r["type"]=="road") == counts["roads"]
        spaces = read("spaces_checked.json")
        assert not spaces["blocked"] and not spaces["unsupported"] and spaces["courtyard_clear"]
        bodies=read("bodies_checked.json")
        assert bodies["checked"]==12 and not bodies["conflicts"] and not bodies["main_street_blockers"]
        for row in read("support_before.json"):
            assert matches(transform(row["actor"]), row["transform"]), row["label"]
        created = [row for i in range(3) for row in read("created_"+str(i)+".json")]
        assert len(created) == 12
        actual = api("editor_toolset.toolsets.scene.SceneTools.get_actors_in_folder", {"folder_path": FOLDER, "recursive": False})["returnValue"]
        assert {a["refPath"] for a in actual} == {r["actor"]["refPath"] for r in created}
        assert all(matches(transform(r["actor"]),r["item"]["xform"]) for r in created)
        assert api("editor_toolset.toolsets.asset.AssetTools.save_assets", {"asset_paths": [LEVEL]})["returnValue"]
        assert not api("editor_toolset.toolsets.asset.AssetTools.is_dirty", {"asset_path": LEVEL})["returnValue"]
        result={"status":"SUCCESS","background_buildings":12,"alleys":5,"dead_ends":1,"existing_models_unchanged":counts["models"],"existing_path_elements_unchanged":counts["roads"],"uncovered_corridors":5,"saved":True}
        write("result.json",result)
        return result
    raise ValueError(MODE)
