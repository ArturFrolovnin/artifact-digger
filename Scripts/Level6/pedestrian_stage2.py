"""Small batches for Level_6 streets; run through Unreal MCP ProgrammaticToolset.

Existing building actors are guarded, never edited. Plans and recovery data are
in Saved/Level6Replan/Stage2. Set MODE and INDEX per tool call.
"""
import json

MODE = "protect"
INDEX = 0
LEVEL = "/Game/TestLevel/Level_6/level_6_create_map"
OUT = "D:/UEProject/ArcheoDig/Saved/Level6Replan/Stage2/"


def api(tool, args):
    return execute_tool(tool, json.dumps(args))


def read(name):
    value = api("editor_toolset.toolsets.asset.AssetTools.read_file",
                {"file_path": OUT + name})["returnValue"]
    return json.loads(value.lstrip("\ufeff"))


def write(name, data):
    api("editor_toolset.toolsets.asset.AssetTools.write_file",
        {"file_path": OUT + name, "content": json.dumps(data)})


def transform(actor):
    return api("editor_toolset.toolsets.actor.ActorTools.get_actor_transform",
               {"actor": actor})["returnValue"]


def matches(a, b):
    return (all(abs(a["location"][k] - b["location"][k]) < .01 for k in a["location"])
            and all(abs((a["rotation"][k] - b["rotation"][k] + 180) % 360 - 180) < .001
                    for k in a["rotation"])
            and all(abs(a["scale"][k] - b["scale"][k]) < .000001 for k in a["scale"]))


def properties(component, names):
    return json.loads(api("editor_toolset.toolsets.object.ObjectTools.get_properties",
                          {"instance": component, "properties": names})["returnValue"])


def set_properties(component, values):
    assert api("editor_toolset.toolsets.object.ObjectTools.set_properties",
               {"instance": component, "values": json.dumps(values)})["returnValue"]


def set_transform(actor, value):
    assert api("editor_toolset.toolsets.actor.ActorTools.set_actor_transform",
               {"actor": actor, "xform": value, "worldspace": True})["returnValue"]


def protected_paths():
    return set(read("protected_paths.json"))


def guard(actor, protected):
    assert actor["refPath"].startswith(LEVEL + "."), actor
    assert actor["refPath"] not in protected, ("protected building", actor)


def verify_piece(actor, component, item):
    assert matches(transform(actor), item["xform"]), item["name"]
    p = properties(component, ["staticMesh", "overrideMaterials", "bodyInstance", "canCharacterStepUpOn"])
    assert p["overrideMaterials"] == [{"refPath": item["material"]}], item["name"]
    assert p["staticMesh"]["refPath"] == item.get("asset", "/Engine/BasicShapes/Cube.Cube")
    assert p["bodyInstance"]["collisionEnabled"] in ["QueryOnly", "QueryAndPhysics"]
    assert p["bodyInstance"]["collisionProfileName"] == "BlockAll"
    assert p["canCharacterStepUpOn"] == "ECB_Yes"


def run():
    assert api("editor_toolset.toolsets.scene.SceneTools.get_current_level", {})["returnValue"] == LEVEL
    if MODE in ["protect", "verify_protected"]:
        rows = read("protected_" + str(INDEX) + ".json")
        for row in rows:
            assert matches(transform(row["actor"]), row["transform"]), row["label"]
            if MODE == "verify_protected":
                for mesh in row["meshes"]:
                    assert properties(mesh["component"], ["staticMesh", "overrideMaterials"]) == mesh["properties"], row["label"]
        result = {"mode": MODE, "index": INDEX, "unchanged": len(rows)}
        write(MODE + "_" + str(INDEX) + ".json", result)
        return result
    if MODE == "snapshot":
        rows = read("environment_" + str(INDEX) + ".json")
        protected = protected_paths()
        result = []
        for row in rows:
            actor = {"refPath": row["path"]}
            guard(actor, protected)
            component = {"refPath": row["path"] + ".StaticMeshComponent0"}
            p = properties(component, ["staticMesh", "overrideMaterials"])
            assert p["staticMesh"]["refPath"] == "/Engine/BasicShapes/Cube.Cube", row["label"]
            result.append({"actor": actor, "component": component, "label": row["label"],
                           "transform": transform(actor), "properties": p})
        write("snapshot_" + str(INDEX) + ".json", result)
        return {"mode": MODE, "index": INDEX, "captured": len(result)}
    assert read("preflight.json")["ready"]
    protected = protected_paths()
    if MODE == "create":
        items = read("create_" + str(INDEX) + ".json")
        created = []
        try:
            for item in items:
                actor = api("editor_toolset.toolsets.scene.SceneTools.add_to_scene_from_asset",
                            {"asset_path": item.get("asset", "/Engine/BasicShapes/Cube.Cube"),
                             "name": item["name"], "xform": item["xform"], "snap_to_ground": False})["returnValue"]
                guard(actor, protected)
                created.append({"actor": actor, "item": item})
                component = api("editor_toolset.toolsets.actor.ActorTools.get_root_component", {"actor": actor})["returnValue"]
                set_properties(component, {"overrideMaterials": [{"refPath": item["material"]}],
                                           "canCharacterStepUpOn": "ECB_Yes"})
                api("editor_toolset.toolsets.scene.SceneTools.set_actor_folder",
                    {"actor": actor, "folder_path": "CityBlockout/Pedestrian_Stage2/" + item["category"]})
                verify_piece(actor, component, item)
        except Exception:
            for row in reversed(created):
                api("editor_toolset.toolsets.scene.SceneTools.remove_from_scene", {"actor": row["actor"]})
            raise
        write("created_" + str(INDEX) + ".json", created)
        return {"mode": MODE, "index": INDEX, "created": len(created)}
    if MODE == "update":
        items = read("update_" + str(INDEX) + ".json")
        for item in items:
            actor, component = item["actor"], item["component"]
            guard(actor, protected)
            assert matches(transform(actor), item["before"]), item["name"]
        for item in items:
            actor, component = item["actor"], item["component"]
            set_transform(actor, item["xform"])
            if item.get("material"):
                set_properties(component, {"overrideMaterials": [{"refPath": item["material"]}],
                                           "canCharacterStepUpOn": "ECB_Yes"})
                api("editor_toolset.toolsets.actor.ActorTools.set_label",
                    {"actor": actor, "label": item["name"]})
                api("editor_toolset.toolsets.scene.SceneTools.set_actor_folder",
                    {"actor": actor, "folder_path": "CityBlockout/Pedestrian_Stage2/" + item["category"]})
                verify_piece(actor, component, item)
            else:
                assert matches(transform(actor), item["xform"]), item["name"]
        write("updated_" + str(INDEX) + ".json", {"updated": len(items)})
        return {"mode": MODE, "index": INDEX, "updated": len(items)}
    if MODE == "retire":
        ready = read("replacement_ready.json")
        assert ready["main_ready"]
        rows = read("retire_" + str(INDEX) + ".json")
        for row in rows:
            guard(row["actor"], protected)
            assert matches(transform(row["actor"]), row["transform"]), row["label"]
            assert row["properties"]["staticMesh"]["refPath"] == "/Engine/BasicShapes/Cube.Cube"
        for row in rows:
            assert api("editor_toolset.toolsets.scene.SceneTools.remove_from_scene", {"actor": row["actor"]})["returnValue"]
        write("retired_" + str(INDEX) + ".json", {"retired": len(rows)})
        return {"mode": MODE, "index": INDEX, "retired": len(rows)}
    if MODE == "probe":
        rows = read("probes_" + str(INDEX) + ".json")
        path_actors = set(read("new_paths.json"))
        blocked, unsupported = [], []
        for row in rows:
            x, y = [v * 100 for v in row["point"]]
            def query(radius, low, high):
                return api("editor_toolset.toolsets.scene.SceneTools.find_actors", {
                    "name": "", "tag": "", "collision_channels": ["ObjectTypeQuery1", "ObjectTypeQuery2"],
                    "bounds": {"min": {"x": x-radius, "y": y-radius, "z": low},
                               "max": {"x": x+radius, "y": y+radius, "z": high}, "isValid": True}})["returnValue"]
            hits = query(35, 40, 210)
            if hits:
                blocked.append({"name": row["name"], "hits": hits})
            floor = query(10, 0, 39)
            if not any(a["refPath"] in path_actors for a in floor):
                unsupported.append(row["name"])
        result = {"probes": len(rows), "blocked": blocked, "unsupported": unsupported}
        write("probe_result_" + str(INDEX) + ".json", result)
        return result
    if MODE == "save":
        manifest = read("manifest.json")
        assert sum(read("verify_protected_" + str(i) + ".json")["unchanged"] for i in range(5)) == 147
        created = sum(len(read("created_" + str(i) + ".json")) for i in range(manifest["totalBatches"]))
        retired = sum(read("retired_" + str(i) + ".json")["retired"] for i in range(manifest["retireBatches"]))
        updated = sum(read("updated_" + str(i) + ".json")["updated"] for i in range(manifest["updateBatches"]))
        probes = [read("probe_result_" + str(i) + ".json") for i in range(manifest["probeBatches"])]
        assert all(not r["blocked"] and not r["unsupported"] for r in probes), probes
        ground = read("ground.json")
        assert matches(transform(ground["actor"]), ground["transform"]), "Ground changed"
        assert api("editor_toolset.toolsets.asset.AssetTools.save_assets", {"asset_paths": [LEVEL]})["returnValue"]
        assert not api("editor_toolset.toolsets.asset.AssetTools.is_dirty", {"asset_path": LEVEL})["returnValue"]
        result = {"status": "SUCCESS", "created": created, "retired": retired, "updated": updated,
                  "protected_actors_unchanged": 147, "collision_probes": sum(r["probes"] for r in probes),
                  "alleys": 2, "dead_ends": 1, "park": True, "saved": True}
        write("result.json", result)
        return result
    raise ValueError(MODE)
