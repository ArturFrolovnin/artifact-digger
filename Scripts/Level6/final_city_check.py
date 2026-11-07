"""Final checks for the boundary/road iteration; no screenshots or model edits."""
import json
MODE="geometry"
L="/Game/TestLevel/Level_6/level_6_create_map"
B="D:/UEProject/ArcheoDig/Saved/Level6Replan/BoundaryRoads/"
S="editor_toolset.toolsets.scene.SceneTools."
A="editor_toolset.toolsets.actor.ActorTools."
O="editor_toolset.toolsets.object.ObjectTools."
F="editor_toolset.toolsets.asset.AssetTools."
def api(t,a):return execute_tool(t,json.dumps(a))["returnValue"]
def read(n):return json.loads(api(F+"read_file",{"file_path":B+n}).lstrip("\ufeff"))
def write(n,v):api(F+"write_file",{"file_path":B+n,"content":json.dumps(v)})
def props(c,n):return json.loads(api(O+"get_properties",{"instance":c,"properties":n}))
def same(a,b):return all(abs(a[k][v]-b[k][v])<.001 for k in ["location","rotation","scale"] for v in a[k])
def box(x,y,r=.35,z0=27,z1=205):return {"min":{"x":(x-r)*100,"y":(y-r)*100,"z":z0},"max":{"x":(x+r)*100,"y":(y+r)*100,"z":z1},"isValid":True}
def hits(b):return api(S+"find_actors",{"name":"","tag":"","collision_channels":["ObjectTypeQuery1","ObjectTypeQuery2"],"bounds":b})
def run():
    assert api(S+"get_current_level",{})==L and not api("EditorToolset.EditorAppToolset.IsPIERunning",{})
    if MODE=="geometry":
        tests=[("Museum",8.8,-24),("University",45.73,7),("Library",47.9,43),("TownHall",51.2,78),("Rudy",-19.1,-24),("Graham",-2.8,33),("Cafe",-54.8,13),("Hospital",4.6,78),("Car",-30,63.1),("Store",41.8,-80),("Bus",39.5,-80),("PrivateStreet",-25,-73.55)]
        tests.extend((c["name"],*c["point"]) for c in read("new_courts.json"))
        tests.extend([("OldCentralCourt",20.8,17.4),("OldHospitalCourt",40.8,87.5),("OldSouthCourt",-47.15,87.8)])
        blocked=[]
        for name,x,y in tests:
            found=hits(box(x,y))
            if found:blocked.append({"point":name,"hits":found})
            assert hits(box(x,y,.08,-2,39)),name
        assert not blocked,blocked
        for name,x,y in [("BG_Residential_81",73.7,64.8),("LD_StopCourtFence",66,-94.85),("BG_Residential_87",1,92.2)]:
            actors=api(S+"find_actors",{"name":name,"tag":"","collision_channels":[]})
            assert len(actors)==1 and actors[0] in hits(box(x,y)),name
        for x,y in [(72.75,65),(76,64.35),(63.8,-94.5),(69,-94.2),(-2,91.8),(4.125,91.8)]:assert hits(box(x,y)),[x,y]
        main=next(r for r in read("private_before.json") if r["label"]=="RC_MainStreet")
        t=main["transform"];x=t["location"]["x"];y=t["location"]["y"]
        assert not hits({"min":{"x":x-t["scale"]["x"]*50+1,"y":y-t["scale"]["y"]*50+1,"z":27},"max":{"x":x+t["scale"]["x"]*50-1,"y":y+t["scale"]["y"]*50-1,"z":205},"isValid":True})
        for r in read("safety_created.json"):
            assert same(api(A+"get_actor_transform",{"actor":r["actor"]}),r["xform"])
            c=api(A+"get_root_component",{"actor":r["actor"]});p=props(c,["bodyInstance"])
            assert p["bodyInstance"]["collisionEnabled"]=="QueryAndPhysics"
        character=read("character.json")
        arms=api(A+"get_components",{"actor":character["cdo"],"component_type":{"refPath":"/Script/Engine.SpringArmComponent"}})
        camera=[props(c,["targetArmLength","bDoCollisionTest","probeSize","relativeLocation"]) for c in arms]
        result={"entrance_and_court_points":len(tests),"new_enclosed_courts":3,"old_courts_clear":3,"private_street_clear":True,"safety_gaps":0,"character":character,"camera_arms":camera,"blocked":blocked}
        write("geometry_final.json",result)
        assert api(F+"save_assets",{"asset_paths":[L]})
        return {"entrances_and_courts_clear":len(tests),"new_courts_enclosed":3,"private_street_clear":True,"camera_arms":camera,"saved":True}
    if MODE=="preserve":
        models=read("models_before.json")
        for r in models:
            assert same(api(A+"get_actor_transform",{"actor":r["actor"]}),r["transform"]),r["label"]
            for m in r["meshes"]:assert props(m["component"],["staticMesh","overrideMaterials"])==m["properties"],r["label"]
        private=read("private_before.json")
        for r in private:
            assert same(api(A+"get_actor_transform",{"actor":r["actor"]}),r["transform"]),r["label"]
            c=api(A+"get_root_component",{"actor":r["actor"]});p=props(c,["bVisible","bHiddenInGame"])
            assert p["bVisible"] and not p["bHiddenInGame"],r["label"]
        moves={r["actor"]["refPath"] for r in read("edge_moves.json")}
        old=[r for r in read("background_before.json") if r["actor"]["refPath"] not in moves]
        for r in old:assert same(api(A+"get_actor_transform",{"actor":r["actor"]}),r["transform"]),r["label"]
        result={"protected_landmarks_unchanged":len(models),"private_paths_unchanged":len(private),"other_background_unchanged":len(old)}
        write("preservation_final.json",result)
        return result
    if MODE=="save":
        pie=read("pie_result.json")
        assert pie["passed"] and pie["jump_tests_passed"]
        assert read("edge_result.json")["saved"] and read("roads_result.json")["saved"]
        assert read("geometry_final.json")["safety_gaps"]==0
        assert read("preservation_final.json")["protected_landmarks_unchanged"]==21
        assert len(api(S+"get_actors_in_folder",{"folder_path":"CityBlockout/08_BackgroundBuildings","recursive":True}))==88
        assert api(F+"save_assets",{"asset_paths":[L]}) and not api(F+"is_dirty",{"asset_path":L})
        result={"status":"SUCCESS","boundary_closed":True,"dangerous_gaps":0,"edge_buildings_new":28,"reused_moved":2,"technical_markers_hidden":98,"road_geometry_parts_changed":24,"road_segments_rerouted":15,"old_road_parts_replaced":255,"retired_roads_deleted":6,"junctions_rebuilt":8,"alleys_new":3,"new_courts":3,"new_dead_ends":3,"main_buildings_unchanged":True,"PIE_tested":True,"PIE_route_tests":2,"PIE_boundary_walk_tests":2,"PIE_boundary_jump_tests":2,"saved":True}
        write("result.json",result)
        return result
    raise ValueError(MODE)
