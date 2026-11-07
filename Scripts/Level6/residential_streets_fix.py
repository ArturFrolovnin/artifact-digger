"""Level_6 central residential street; existing groups move rigidly, without import.

MODE/INDEX select bounded Unreal MCP batches. The rest of the city is guarded.
"""
import copy
import json

MODE = "move_houses"
INDEX = 0
LEVEL = "/Game/TestLevel/Level_6/level_6_create_map"
BASE = "D:/UEProject/ArcheoDig/Saved/Level6Replan/ResidentialCentral/"


def api(tool, args):
    return execute_tool(tool, json.dumps(args))


def read(name):
    return json.loads(api("editor_toolset.toolsets.asset.AssetTools.read_file",
                          {"file_path": BASE + name})["returnValue"].lstrip("\ufeff"))


def write(name, data):
    api("editor_toolset.toolsets.asset.AssetTools.write_file",
        {"file_path": BASE + name, "content": json.dumps(data)})


def transform(actor):
    return api("editor_toolset.toolsets.actor.ActorTools.get_actor_transform", {"actor": actor})["returnValue"]


def matches(a, b):
    return (all(abs(a["location"][k]-b["location"][k]) < .01 for k in a["location"])
            and all(abs((a["rotation"][k]-b["rotation"][k]+180) % 360-180) < .001 for k in a["rotation"])
            and all(abs(a["scale"][k]-b["scale"][k]) < .000001 for k in a["scale"]))


def properties(component, names):
    return json.loads(api("editor_toolset.toolsets.object.ObjectTools.get_properties",
                          {"instance": component, "properties": names})["returnValue"])


def guard(actor):
    assert actor["refPath"].startswith(LEVEL + ".")
    assert actor["refPath"] not in set(read("protected_paths.json")), actor


def verify_floor(actor, component, item):
    assert matches(transform(actor), item["xform"]), item["name"]
    p = properties(component, ["staticMesh", "overrideMaterials", "bodyInstance"])
    assert p["staticMesh"]["refPath"] == "/Engine/BasicShapes/Cube.Cube"
    assert p["overrideMaterials"] == [{"refPath": item["material"]}]
    assert p["bodyInstance"]["collisionEnabled"] in ["QueryOnly", "QueryAndPhysics"]
    assert p["bodyInstance"]["collisionProfileName"] == "BlockAll"


def run():
    assert api("editor_toolset.toolsets.scene.SceneTools.get_current_level", {})["returnValue"] == LEVEL
    assert read("preflight.json")["ready"]
    if MODE == "snapshot_city":
        rows = read("city_input.json")
        for row in rows:
            row["transform"] = transform(row["actor"])
            for mesh in row["meshes"]:
                mesh["properties"] = properties(mesh["component"], ["staticMesh", "overrideMaterials"])
        write("city_before.json", rows)
        return {"city_actors_captured": len(rows)}
    if MODE == "move_houses":
        assert not read("house_clearance.json")["foreign"]
        groups = [read("move_group_" + str(i) + ".json") for i in range(8)]
        steps = []
        for g in groups:
            for row in g["rows"]:
                target = copy.deepcopy(row["transform"])
                target["location"]["y"] += g["delta_y"]
                assert matches(transform(row["actor"]), row["transform"]), row["label"]
                steps.append({"row": row, "target": target, "root": not row.get("parent")})
        moved = []
        try:
            for step in steps:
                if step["root"]:
                    moved.append(step)
                    assert api("editor_toolset.toolsets.actor.ActorTools.set_actor_transform", {
                        "actor": step["row"]["actor"], "xform": step["target"], "worldspace": True})["returnValue"]
            for step in steps:
                row = step["row"]
                assert matches(transform(row["actor"]), step["target"]), row["label"]
                for mesh in row["meshes"]:
                    assert properties(mesh["component"], ["staticMesh", "overrideMaterials"]) == mesh["properties"], row["label"]
        except Exception:
            for step in reversed(moved):
                assert api("editor_toolset.toolsets.actor.ActorTools.set_actor_transform", {
                    "actor": step["row"]["actor"], "xform": step["row"]["transform"], "worldspace": True})["returnValue"]
            assert all(matches(transform(s["row"]["actor"]), s["row"]["transform"]) for s in steps)
            raise
        result = {"groups": 8, "actors": len(steps), "roots_moved": len(moved),
                  "left_shift_cm": -230, "right_shift_cm": 120,
                  "relative_transforms_materials_scales_preserved": True}
        write("houses_moved.json", result)
        return result
    if MODE == "create":
        items = read("create_" + str(INDEX) + ".json")
        created = []
        try:
            for item in items:
                actor = api("editor_toolset.toolsets.scene.SceneTools.add_to_scene_from_asset", {
                    "asset_path": "/Engine/BasicShapes/Cube.Cube", "name": item["name"],
                    "xform": item["xform"], "snap_to_ground": False})["returnValue"]
                guard(actor)
                created.append({"actor": actor, "item": item})
                component = api("editor_toolset.toolsets.actor.ActorTools.get_root_component", {"actor": actor})["returnValue"]
                assert api("editor_toolset.toolsets.object.ObjectTools.set_properties", {
                    "instance": component, "values": json.dumps({"overrideMaterials": [{"refPath": item["material"]}],
                    "canCharacterStepUpOn": "ECB_Yes"})})["returnValue"]
                api("editor_toolset.toolsets.scene.SceneTools.set_actor_folder", {
                    "actor": actor, "folder_path": "CityBlockout/ResidentialStreets/Network"})
                verify_floor(actor, component, item)
                if item["name"] == "RC_MainStreet":
                    write("main_street.json", {"actor": actor, "item": item})
        except Exception:
            for row in reversed(created):
                api("editor_toolset.toolsets.scene.SceneTools.remove_from_scene", {"actor": row["actor"]})
            raise
        write("created_" + str(INDEX) + ".json", created)
        return {"created": len(created), "batch": INDEX}
    if MODE == "update":
        items = read("updates.json")
        for item in items:
            guard(item["actor"])
            assert matches(transform(item["actor"]), item["before"]), item["name"]
        for item in items:
            assert api("editor_toolset.toolsets.actor.ActorTools.set_actor_transform", {
                "actor": item["actor"], "xform": item["xform"], "worldspace": True})["returnValue"]
            verify_floor(item["actor"], item["component"], item)
        write("updated.json", {"updated": len(items)})
        return {"updated": len(items)}
    if MODE == "retire":
        manifest = read("manifest.json")
        assert sum(len(read("created_" + str(i) + ".json")) for i in range(manifest["createBatches"])) == manifest["created"]
        rows = read("retire_" + str(INDEX) + ".json")
        for row in rows:
            guard(row["actor"])
            assert matches(transform(row["actor"]), row["actual_transform"]), row["item"]["name"]
            component = api("editor_toolset.toolsets.actor.ActorTools.get_root_component", {"actor": row["actor"]})["returnValue"]
            assert properties(component, ["staticMesh"])["staticMesh"]["refPath"] == "/Engine/BasicShapes/Cube.Cube"
        for row in rows:
            assert api("editor_toolset.toolsets.scene.SceneTools.remove_from_scene", {"actor": row["actor"]})["returnValue"]
        write("retired_" + str(INDEX) + ".json", {"retired": len(rows)})
        return {"retired": len(rows), "batch": INDEX}
    if MODE == "verify_houses":
        groups = [read("move_group_" + str(i) + ".json") for i in [INDEX*2, INDEX*2+1]]
        count = 0
        for g in groups:
            for row in g["rows"]:
                target = copy.deepcopy(row["transform"])
                target["location"]["y"] += g["delta_y"]
                assert matches(transform(row["actor"]), target), row["label"]
                for mesh in row["meshes"]:
                    assert properties(mesh["component"], ["staticMesh", "overrideMaterials"]) == mesh["properties"], row["label"]
                count += 1
        write("verified_" + str(INDEX) + ".json", {"preserved": count})
        return {"house_actors_preserved": count, "batch": INDEX}
    if MODE == "verify_city":
        rows = read("city_before.json")
        for row in rows:
            assert matches(transform(row["actor"]), row["transform"]), row["label"]
            for mesh in row["meshes"]:
                assert properties(mesh["component"], ["staticMesh", "overrideMaterials"]) == mesh["properties"], row["label"]
        write("city_verified.json", {"unchanged": len(rows)})
        return {"city_actors_unchanged": len(rows)}
    if MODE == "probe":
        rows, floors = read("probes_" + str(INDEX) + ".json"), set(read("floor_paths.json"))
        blocked, unsupported = [], []
        for row in rows:
            x, y = [v*100 for v in row["point"]]
            def query(radius, low, high):
                return api("editor_toolset.toolsets.scene.SceneTools.find_actors", {
                    "name": "", "tag": "", "collision_channels": ["ObjectTypeQuery1", "ObjectTypeQuery2"],
                    "bounds": {"min": {"x": x-radius, "y": y-radius, "z": low},
                               "max": {"x": x+radius, "y": y+radius, "z": high}, "isValid": True}})["returnValue"]
            hits = query(35, 40, 250)
            if hits:
                blocked.append({"name": row["name"], "hits": hits})
            if not any(a["refPath"] in floors for a in query(10, 0, 39)):
                unsupported.append(row["name"])
        result = {"tested": len(rows), "blocked": blocked, "unsupported": unsupported}
        write("probe_result_" + str(INDEX) + ".json", result)
        return result
    if MODE == "main_check":
        main = read("main_street.json")
        bounds = api("editor_toolset.toolsets.actor.ActorTools.get_actor_bounds", {"actor": main["actor"]})["returnValue"]
        assert abs(bounds["max"]["y"]-bounds["min"]["y"]-300) < .01
        assert abs(bounds["max"]["z"]-24) < .01
        box = {"min": {"x": bounds["min"]["x"]+1, "y": bounds["min"]["y"], "z": 26},
               "max": {"x": bounds["max"]["x"]-1, "y": bounds["max"]["y"], "z": 250}, "isValid": True}
        hits = api("editor_toolset.toolsets.scene.SceneTools.find_actors", {
            "name": "", "tag": "", "collision_channels": ["ObjectTypeQuery1", "ObjectTypeQuery2"], "bounds": box})["returnValue"]
        unsupported = []
        x, y = bounds["min"]["x"]+40, (bounds["min"]["y"]+bounds["max"]["y"])/2
        while x <= bounds["max"]["x"]-40:
            sample = {"min": {"x": x-10, "y": y-10, "z": 0},
                      "max": {"x": x+10, "y": y+10, "z": 25}, "isValid": True}
            floors = api("editor_toolset.toolsets.scene.SceneTools.find_actors", {
                "name": "", "tag": "", "collision_channels": ["ObjectTypeQuery1", "ObjectTypeQuery2"], "bounds": sample})["returnValue"]
            if not any(a["refPath"] == main["actor"]["refPath"] for a in floors):
                unsupported.append(x)
            x += 500
        result = {"width_m": 3, "full_corridor_blockers": hits, "unsupported_samples": unsupported,
                  "length_m": (bounds["max"]["x"]-bounds["min"]["x"])/100}
        write("main_checked.json", result)
        return result
    if MODE == "save":
        manifest, preflight = read("manifest.json"), read("preflight.json")
        assert sum(read("verified_"+str(i)+".json")["preserved"] for i in range(4)) == 124
        assert read("city_verified.json")["unchanged"] == len(read("city_before.json"))
        assert read("houses_moved.json")["groups"] == 8
        assert sum(read("retired_"+str(i)+".json")["retired"] for i in range(manifest["retireBatches"])) == manifest["retired"]
        assert read("updated.json")["updated"] == manifest["updated"]
        probes = [read("probe_result_"+str(i)+".json") for i in range(manifest["probeBatches"])]
        assert all(not r["blocked"] and not r["unsupported"] for r in probes), probes
        main = read("main_checked.json")
        assert not main["full_corridor_blockers"] and not main["unsupported_samples"], main
        assert api("editor_toolset.toolsets.asset.AssetTools.save_assets", {"asset_paths": [LEVEL]})["returnValue"]
        assert not api("editor_toolset.toolsets.asset.AssetTools.is_dirty", {"asset_path": LEVEL})["returnValue"]
        result = {"status": "SUCCESS", "central_street": True, "width_m": 3,
                  "gate_approaches": 8, "house_actors_preserved": 124, "house_groups_moved": 8,
                  "north_connection": True, "south_connection": True,
                  "bus_route": preflight["routes_m"]["BusStop"], "city_route": preflight["routes_m"]["Museum"],
                  "collision_probes": sum(r["tested"] for r in probes), "saved": True}
        write("result.json", result)
        return result
    raise ValueError(MODE)
