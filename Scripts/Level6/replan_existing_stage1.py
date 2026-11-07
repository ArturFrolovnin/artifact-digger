"""Run with Unreal MCP ProgrammaticToolset.execute_tool_script in the open editor.

Only moves existing actors. Baselines, plans and restore data live in Saved.
X is north, Y is east, units are centimetres. PHASE is supplied per MCP call.
"""
import copy
import json
import math

PHASE = "inspect_residential"
LEVEL = "/Game/TestLevel/Level_6/level_6_create_map"
OUT = "D:/UEProject/ArcheoDig/Saved/Level6Replan/"
# Group envelope centres in metres; retain all Z values and actor scales.
TARGETS = {
    "ConspiracyHouse": (20, -80, 0),
    "HippieCoupleHouse": (20, -66, 0),
    "SlackerFriendsHouse": (-3, -80, 0),
    "IntellectualGrandpaHouse": (-3, -66, 0),
    "RelaxedNeighborHouse": (-26, -80, 0),
    "CreatorCoupleHouse": (-26, -66, 0),
    "PlayerHouse": (-49, -80, 0),
    "MiaHouse": (-49, -66, 0),
    "University": (60, 7, 0),
    "Dormitory": (60, -29, 0),
    "Library": (60, 43, 0),
    "TownHall": (60, 78, 0),
    "Museum": (22, -24, 0),
    "Hospital": (15, 78, 180),
    "RudyPawnshop": (-13, -24, 0),
    "GrahamShop": (5, 33, 90),
    "GeneralStore": (47, -80, 0),
    "CafeBar": (-43, 13, 90),
    "CarDealership": (-30, 77, 180),
    "BusStop": (37, -80, 0),
    "Fountain": (5, -24, 0),
}
RESIDENTIAL = list(TARGETS)[:8]
CIVIC = list(TARGETS)[8:14]
COMMERCIAL = list(TARGETS)[14:20]


def api(tool, args):
    return execute_tool(tool, json.dumps(args))


def read(name):
    data = api("editor_toolset.toolsets.asset.AssetTools.read_file",
               {"file_path": OUT + name})["returnValue"]
    return json.loads(data.lstrip("\ufeff"))


def write(name, data):
    api("editor_toolset.toolsets.asset.AssetTools.write_file",
        {"file_path": OUT + name, "content": json.dumps(data)})


def transform(actor):
    return api("editor_toolset.toolsets.actor.ActorTools.get_actor_transform",
               {"actor": actor})["returnValue"]


def set_transform(actor, xform):
    assert api("editor_toolset.toolsets.actor.ActorTools.set_actor_transform",
               {"actor": actor, "xform": xform, "worldspace": True})["returnValue"]


def mesh_properties(component):
    return json.loads(api("editor_toolset.toolsets.object.ObjectTools.get_properties",
                          {"instance": component,
                           "properties": ["staticMesh", "overrideMaterials"]})["returnValue"])


def envelope(rows):
    return {side: {axis: fn(r["bounds"][side][axis] for r in rows)
                   for axis in ["x", "y", "z"]}
            for side, fn in [("min", min), ("max", max)]}


def close(a, b, tolerance=0.01):
    return (all(abs(a["location"][k] - b["location"][k]) < tolerance for k in a["location"])
            and all(abs((a["rotation"][k] - b["rotation"][k] + 180) % 360 - 180) < 0.001
                    for k in a["rotation"])
            and all(abs(a["scale"][k] - b["scale"][k]) < 0.000001 for k in a["scale"]))


def planned(group):
    name = group["name"]
    x, y, turn = TARGETS[name]
    b = group["bounds"]
    cx = (b["min"]["x"] + b["max"]["x"]) / 2
    cy = (b["min"]["y"] + b["max"]["y"]) / 2
    c, s = math.cos(math.radians(turn)), math.sin(math.radians(turn))
    plans = []
    corners = []
    for row in group["rows"]:
        target = copy.deepcopy(row["transform"])
        p = target["location"]
        px, py = p["x"] - cx, p["y"] - cy
        p["x"], p["y"] = x * 100 + c * px - s * py, y * 100 + s * px + c * py
        target["rotation"]["yaw"] += turn
        # Normalise yaw to the editor's [-180,180] representation.
        target["rotation"]["yaw"] = (target["rotation"]["yaw"] + 180) % 360 - 180
        plans.append({"actor": row["actor"], "before": row["transform"],
                      "target": target, "move_root": not row.get("parent")})
        for a in ["min", "max"]:
            for d in ["min", "max"]:
                px, py = row["bounds"][a]["x"] - cx, row["bounds"][d]["y"] - cy
                corners.append((x * 100 + c * px - s * py, y * 100 + s * px + c * py))
    rect = [min(p[0] for p in corners), max(p[0] for p in corners),
            min(p[1] for p in corners), max(p[1] for p in corners)]
    return {"name": name, "actors": plans, "rect": rect}


def verify(group, plan):
    for row, step in zip(group["rows"], plan["actors"]):
        assert close(transform(row["actor"]), step["target"]), row["label"]
        for mesh in row["meshes"]:
            assert mesh_properties(mesh["component"]) == mesh["properties"], row["label"]
    return len(plan["actors"])


def run():
    assert api("editor_toolset.toolsets.scene.SceneTools.get_current_level", {})["returnValue"] == LEVEL
    action, section = PHASE.split("_", 1)
    names = {"residential": RESIDENTIAL, "civic": CIVIC,
             "commercial": COMMERCIAL, "fountain": ["Fountain"]}[section]
    if action == "inspect":
        result = []
        for name in names:
            # The live inventory was already captured through Unreal MCP.
            g = read("stage1_live_" + name + ".json")
            roots = {r["root"]["refPath"] for r in g["rows"] if r.get("root")}
            assert all(not r.get("parent") or r["parent"]["refPath"] in roots
                       for r in g["rows"]), (name, "external attachment")
            p = planned(g)
            write("stage1_plan_" + name + ".json", p)
            result.append({"name": name, "actors": len(g["rows"]),
                           "bounds_before": g["bounds"], "target_rect": p["rect"]})
        return {"phase": PHASE, "groups": result}
    assert action == "apply"
    preflight = read("stage1_preflight.json")
    assert preflight["ready"] and not preflight["overlaps"]
    groups = [read("stage1_live_" + name + ".json") for name in names]
    plans = [read("stage1_plan_" + name + ".json") for name in names]
    # Reject stale plans before any change.
    for g, p in zip(groups, plans):
        for row, step in zip(g["rows"], p["actors"]):
            assert close(transform(row["actor"]), step["before"]), row["label"]
    changed = []
    try:
        for plan in plans:
            for step in plan["actors"]:
                if step["move_root"]:
                    changed.append(step)
                    set_transform(step["actor"], step["target"])
        count = sum(verify(g, p) for g, p in zip(groups, plans))
    except Exception:
        for step in reversed(changed):
            set_transform(step["actor"], step["before"])
        assert all(close(transform(s["actor"]), s["before"]) for s in changed)
        raise
    saved = api("editor_toolset.toolsets.asset.AssetTools.save_assets",
                {"asset_paths": [LEVEL]})["returnValue"]
    dirty = api("editor_toolset.toolsets.asset.AssetTools.is_dirty",
                {"asset_path": LEVEL})["returnValue"]
    assert saved and not dirty, (saved, dirty)
    result = {"phase": PHASE, "buildings": len(names), "actors": count,
              "transforms_verified": True, "mesh_materials_verified": True, "saved": True}
    write("stage1_result_" + section + ".json", result)
    return result
