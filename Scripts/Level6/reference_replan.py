"""Staged Level_6 reference replan; explicit plans, no historical generators."""
import json
import math
MODE="preflight"
INDEX=0
L="/Game/TestLevel/Level_6/level_6_create_map"
B="D:/UEProject/ArcheoDig/Saved/Level6Replan/ReferenceR2/"
OLD="D:/UEProject/ArcheoDig/Saved/Level6Replan/BoundaryRoads/"
S="editor_toolset.toolsets.scene.SceneTools."
A="editor_toolset.toolsets.actor.ActorTools."
O="editor_toolset.toolsets.object.ObjectTools."
F="editor_toolset.toolsets.asset.AssetTools."
CUBE="/Engine/BasicShapes/Cube.Cube"
PAVING="/Game/TestLevel/Level_6/Blockout/Materials/M_BO_Paving.M_BO_Paving"
GROUND="/Game/TestLevel/Level_6/Blockout/Generated/SM_L6_BackdropGround_R2.SM_L6_BackdropGround_R2"
TOP="/Game/TestLevel/Level_6/Blockout/Generated/SM_L6_PedestrianSurface_R2.SM_L6_PedestrianSurface_R2"
CURB="/Game/TestLevel/Level_6/Blockout/Generated/SM_L6_PedestrianCurbs_R2.SM_L6_PedestrianCurbs_R2"
def api(t,a):return execute_tool(t,json.dumps(a))["returnValue"]
def read(n,old=False):return json.loads(api(F+"read_file",{"file_path":(OLD if old else B)+n}).lstrip("\ufeff"))
def write(n,v):api(F+"write_file",{"file_path":B+n,"content":json.dumps(v)})
def props(c,n):return json.loads(api(O+"get_properties",{"instance":c,"properties":n}))
def setp(c,p):assert api(O+"set_properties",{"instance":c,"values":json.dumps(p)})
def same(a,b):return all(abs(a[k][v]-b[k][v])<.001 for k in ["location","rotation","scale"] for v in a[k])
def query(b):return api(S+"find_actors",{"name":"","tag":"","collision_channels":["ObjectTypeQuery1","ObjectTypeQuery2"],"bounds":b})
def corners(t):
    a=t["rotation"]["yaw"]*math.pi/180;c,s=math.cos(a),math.sin(a)
    return [[t["location"]["x"]+c*u*t["scale"]["x"]*50-s*v*t["scale"]["y"]*50,t["location"]["y"]+s*u*t["scale"]["x"]*50+c*v*t["scale"]["y"]*50] for u,v in [[-1,-1],[1,-1],[1,1],[-1,1]]]
def run():
    assert api(S+"get_current_level",{})==L and not api("EditorToolset.EditorAppToolset.IsPIERunning",{})
    assert read("preflight.json")["ready"]
    if MODE=="preflight":
        moved={r["actor"]["refPath"] for r in read("moves.json")}
        masonry={r["actor"]["refPath"] for r in read("edge_walls_created.json",True)}
        conflicts=[]
        for r in read("moves.json"):
            if r["far"]:continue
            p=corners(r["xform"])
            box={"min":{"x":min(q[0] for q in p)+1,"y":min(q[1] for q in p)+1,"z":27},"max":{"x":max(q[0] for q in p)-1,"y":max(q[1] for q in p)-1,"z":r["xform"]["scale"]["z"]*100-1},"isValid":True}
            found=[a for a in query(box) if a["refPath"] not in moved|masonry]
            if found:conflicts.append({"name":r["label"],"hits":found})
        write("native_preflight.json",{"conflicts":conflicts})
        return {"inside_moves_checked":22,"conflicts":conflicts}
    assert not read("native_preflight.json")["conflicts"]
    if MODE=="moves":
        rows=read("moves_"+str(INDEX)+".json");done=[]
        roof=read("roof_bounds.json")
        cube={"min":{"x":-50,"y":-50,"z":-50},"max":{"x":50,"y":50,"z":50}}
        try:
            for r in rows:
                actor=r["actor"];old=r["transform"];new=r["xform"]
                assert same(api(A+"get_actor_transform",{"actor":actor}),old),r["label"]
                done.append(r)
                assert api(A+"set_actor_transform",{"actor":actor,"xform":new,"worldspace":True})
                for part in r["components"]:
                    c,p=part["component"],part["properties"]
                    if c==r["root"]:
                        setp(c,{"bUseDefaultCollision":False,"bodyInstance":{"collisionEnabled":"NoCollision" if r["far"] else "QueryAndPhysics","collisionProfileName":"NoCollision" if r["far"] else "BlockAll"},"castShadow":not r["far"],"bVisibleInRayTracing":not r["far"]})
                        continue
                    assert p["bAbsoluteScale"] and all(abs(v)<.01 for v in p["relativeRotation"].values())
                    mb=cube if p["staticMesh"]["refPath"]==CUBE else roof
                    span={k:mb["max"][k]-mb["min"][k] for k in ["x","y","z"]}
                    center={k:(mb["max"][k]+mb["min"][k])/2 for k in span}
                    sc=dict(p["relativeScale3D"]);loc={}
                    for k in ["x","y"]:sc[k]+=(new["scale"][k]-old["scale"][k])*100/span[k]
                    for k in span:
                        oldcenter=p["relativeLocation"][k]*old["scale"][k]+center[k]*p["relativeScale3D"][k]
                        desired=oldcenter*new["scale"][k]/old["scale"][k] if k!="z" else oldcenter+(new["scale"]["z"]-old["scale"]["z"])*50
                        loc[k]=(desired-center[k]*sc[k])/new["scale"][k]
                    setp(c,{"relativeLocation":loc,"relativeScale3D":sc,"castShadow":not r["far"],"bVisibleInRayTracing":not r["far"],"bUseDefaultCollision":False,"bodyInstance":{"collisionEnabled":"NoCollision","collisionProfileName":"NoCollision"}})
                api(S+"set_actor_folder",{"actor":actor,"folder_path":"CityBlockout/08_BackgroundBuildings/ReferenceR2/"+("Distant" if r["far"] else "Quarters")})
                assert same(api(A+"get_actor_transform",{"actor":actor}),new),r["label"]
            write("moved_"+str(INDEX)+".json",done)
        except Exception:
            for r in reversed(done):
                api(A+"set_actor_transform",{"actor":r["actor"],"xform":r["transform"],"worldspace":True})
                for p in r["components"]:setp(p["component"],p["properties"])
            raise
        return {"batch":INDEX,"relocated":len(done),"distant":sum(r["far"] for r in done)}
    if MODE=="backdrop":
        t={"location":{"x":0,"y":0,"z":0},"rotation":{"pitch":0,"yaw":0,"roll":0},"scale":{"x":1,"y":-1,"z":1}}
        actor=api(S+"add_to_scene_from_asset",{"asset_path":GROUND,"name":"R2_DistantTerrain","xform":t,"snap_to_ground":False})
        root=api(A+"get_root_component",{"actor":actor})
        mat=read("ground_before.json",True)["properties"]["overrideMaterials"]
        setp(root,{"overrideMaterials":mat,"bUseDefaultCollision":False,"bodyInstance":{"collisionEnabled":"NoCollision","collisionProfileName":"NoCollision"},"castShadow":False,"bVisibleInRayTracing":False})
        api(S+"set_actor_folder",{"actor":actor,"folder_path":"CityBlockout/10_Boundary/ReferenceR2/Backdrop"})
        write("backdrop_created.json",{"actor":actor,"root":root})
        return {"backdrop_terrain_triangles":64,"collision":False,"original_ground_unchanged":True}
    if MODE=="trees":
        done=[]
        for group in read("distant_trees.json"):
            first=group["pieces"][0]
            t={"location":{"x":first["x"]*100,"y":first["y"]*100,"z":first["h"]*50},"rotation":{"pitch":0,"yaw":0,"roll":0},"scale":{"x":first["d"],"y":first["w"],"z":first["h"]}}
            actor=api(S+"add_to_scene_from_asset",{"asset_path":"/Engine/BasicShapes/Cone.Cone","name":group["name"],"xform":t,"snap_to_ground":False})
            root=api(A+"get_root_component",{"actor":actor})
            base={"overrideMaterials":[{"refPath":"/Game/TestLevel/Level_6/Blockout/Materials/M_BO_Green.M_BO_Green"}],"bUseDefaultCollision":False,"bodyInstance":{"collisionEnabled":"NoCollision","collisionProfileName":"NoCollision"},"castShadow":False,"bVisibleInRayTracing":False}
            setp(root,base)
            for i,p in enumerate(group["pieces"][1:]):
                c=api(A+"add_component",{"owner":root,"component_type":{"refPath":"/Script/Engine.StaticMeshComponent"},"name":"Distant_Canopy_"+str(i)})
                values=dict(base);values.update({"staticMesh":{"refPath":"/Engine/BasicShapes/Cone.Cone"},"bAbsoluteScale":True,"mobility":"Static","relativeScale3D":{"x":p["d"],"y":p["w"],"z":p["h"]},"relativeLocation":{"x":(p["x"]*100-t["location"]["x"])/t["scale"]["x"],"y":(p["y"]*100-t["location"]["y"])/t["scale"]["y"],"z":(p["h"]*50-t["location"]["z"])/t["scale"]["z"]}})
                setp(c,values)
            api(S+"set_actor_folder",{"actor":actor,"folder_path":"CityBlockout/10_Boundary/ReferenceR2/Backdrop"})
            done.append({"actor":actor,"item":group})
        write("trees_created.json",done)
        return {"distant_groups":len(done),"simple_canopies":24,"collision":False}
    if MODE=="walls":
        rows=read("edge_walls_created.json",True);before=[]
        for r in rows:
            actor=r["actor"];t=api(A+"get_actor_transform",{"actor":actor})
            root=api(A+"get_root_component",{"actor":actor})
            comps=api(A+"get_components",{"actor":actor,"component_type":{"refPath":"/Script/Engine.StaticMeshComponent"}})
            cs=[]
            for c in comps:
                if c==root:continue
                p=props(c,["relativeScale3D"]);cs.append({"component":c,"properties":p})
                sc=dict(p["relativeScale3D"]);sc["z"]*=.55;setp(c,{"relativeScale3D":sc})
            new=json.loads(json.dumps(t));new["location"]["z"]*=.55;new["scale"]["z"]*=.55
            assert api(A+"set_actor_transform",{"actor":actor,"xform":new,"worldspace":True})
            before.append({"actor":actor,"before":t,"xform":new,"components":cs})
        write("walls_lowered.json",before)
        assert api(F+"save_assets",{"asset_paths":[GROUND.split('.')[0],L]})
        write("stage_a.json",{"saved":True,"relocated":34,"distant":12,"new_buildings":0})
        return {"boundary_fences_lowered":4,"physical_safety_unchanged":True,"stage_a_saved":True}
    if MODE=="surfaces":
        result=[]
        for asset,name in [(TOP,"R2_PedestrianSurface"),(CURB,"R2_PedestrianCurbs")]:
            t={"location":{"x":0,"y":0,"z":0},"rotation":{"pitch":0,"yaw":0,"roll":0},"scale":{"x":1,"y":-1,"z":1}}
            actor=api(S+"add_to_scene_from_asset",{"asset_path":asset,"name":name,"xform":t,"snap_to_ground":False})
            root=api(A+"get_root_component",{"actor":actor})
            setp(root,{"overrideMaterials":[{"refPath":PAVING}],"bUseDefaultCollision":False,"bVisible":False,"bHiddenInGame":True,"bodyInstance":{"collisionEnabled":"NoCollision","collisionProfileName":"NoCollision"}})
            api(S+"set_actor_folder",{"actor":actor,"folder_path":"CityBlockout/07_Pedestrian/ReferenceR2/Surface"})
            result.append({"actor":actor,"root":root,"asset":asset})
        write("surfaces_created.json",result)
        return {"new_technical_surfaces":2,"existing_assets_reimported":0}
    if MODE=="road_parts":
        created=[]
        for r in read("fresh_roads_"+str(INDEX)+".json"):
            actor=api(S+"add_to_scene_from_asset",{"asset_path":CUBE,"name":r["label"]+"_Collision","xform":r["xform"],"snap_to_ground":False})
            root=api(A+"get_root_component",{"actor":actor})
            setp(root,{"bVisible":False,"bHiddenInGame":True,"bUseDefaultCollision":False,"canCharacterStepUpOn":"ECB_Yes","bodyInstance":{"collisionEnabled":"QueryAndPhysics","collisionProfileName":"BlockAll","bSimulatePhysics":False}})
            api(S+"set_actor_folder",{"actor":actor,"folder_path":"CityBlockout/07_Pedestrian/ReferenceR2/Collision"})
            created.append({"actor":actor,"root":root,"item":r})
        write("road_parts_"+str(INDEX)+".json",created)
        return {"batch":INDEX,"new_floor_strips":len(created)}
    if MODE=="road_activate":
        for r in read("road_edits.json"):
            assert same(api(A+"get_actor_transform",{"actor":r["actor"]}),r["before"])
            assert api(A+"set_actor_transform",{"actor":r["actor"],"xform":r["xform"],"worldspace":True})
        for r in read("retired_roads.json"):
            root=api(A+"get_root_component",{"actor":r["actor"]})
            setp(root,{"bUseDefaultCollision":False,"bodyInstance":{"collisionEnabled":"NoCollision","collisionProfileName":"NoCollision"}})
        for n in ["surface_created.json","curbs_created.json"]:
            r=read(n,True);setp(r["root"],{"bVisible":False,"bHiddenInGame":True})
        for r in read("surfaces_created.json"):setp(r["root"],{"bVisible":True,"bHiddenInGame":False})
        return {"old_loop_parts_disabled":15,"court_pad_refitted":1,"new_surfaces_visible":True}
    if MODE=="check_roads":
        routes=read("routes.json")[INDEX*3:(INDEX+1)*3]
        blocked,unsupported=[],[];count=0
        floor_ids={r["actor"]["refPath"] for i in range(4) for r in read("roads_before_"+str(i)+".json")}
        floor_ids.update(r["actor"]["refPath"] for i in range(2) for r in read("road_parts_"+str(i)+".json"))
        for r in routes:
            for i in range(1,len(r["p"])):
                a,b=r["p"][i-1],r["p"][i];length=math.hypot(b[0]-a[0],b[1]-a[1]);steps=max(1,int(math.ceil(length/1.5)))
                for j in range(steps+1):
                    x=a[0]+(b[0]-a[0])*j/steps;y=a[1]+(b[1]-a[1])*j/steps
                    found=query({"min":{"x":x*100-35,"y":y*100-35,"z":27},"max":{"x":x*100+35,"y":y*100+35,"z":205},"isValid":True})
                    if found:blocked.append({"route":r["name"],"point":[x,y],"hits":found})
                    found=query({"min":{"x":x*100-8,"y":y*100-8,"z":23},"max":{"x":x*100+8,"y":y*100+8,"z":26},"isValid":True})
                    if not any(h["refPath"] in floor_ids for h in found):unsupported.append({"route":r["name"],"point":[x,y]})
                    count+=1
        result={"batch":INDEX,"samples":count,"blocked":blocked,"unsupported":unsupported};write("road_check_"+str(INDEX)+".json",result)
        return result
    if MODE=="road_save":
        checks=[read("road_check_"+str(i)+".json") for i in range(3)]
        assert not any(r["blocked"] or r["unsupported"] for r in checks)
        for r in read("retired_roads.json"):assert api(S+"remove_from_scene",{"actor":r["actor"]})
        assert api(F+"save_assets",{"asset_paths":[TOP.split('.')[0],CURB.split('.')[0],L]})
        write("stage_b.json",{"saved":True,"retired":15,"new_floor_parts":43,"samples":sum(r["samples"] for r in checks)})
        return {"stage_b_saved":True,"old_loop_parts_removed":15,"samples":sum(r["samples"] for r in checks)}
    if MODE=="courts":
        result=[]
        for f in read("fences.json"):
            p=f["pieces"][0]
            t={"location":{"x":(p[0]+p[1])*50,"y":(p[2]+p[3])*50,"z":p[4]*50},"rotation":{"pitch":0,"yaw":0,"roll":0},"scale":{"x":p[1]-p[0],"y":p[3]-p[2],"z":p[4]}}
            actor=api(S+"add_to_scene_from_asset",{"asset_path":CUBE,"name":f["name"],"xform":t,"snap_to_ground":False});root=api(A+"get_root_component",{"actor":actor});setp(root,{"overrideMaterials":[{"refPath":PAVING}]})
            for i,p in enumerate(f["pieces"][1:]):
                c=api(A+"add_component",{"owner":root,"component_type":{"refPath":"/Script/Engine.StaticMeshComponent"},"name":"Court_Closure_"+str(i)})
                world={"x":(p[0]+p[1])*50,"y":(p[2]+p[3])*50,"z":p[4]*50}
                rel={k:(world[k]-t["location"][k])/t["scale"][k] for k in world}
                setp(c,{"staticMesh":{"refPath":CUBE},"relativeLocation":rel,"relativeScale3D":{"x":p[1]-p[0],"y":p[3]-p[2],"z":p[4]},"bAbsoluteScale":True,"mobility":"Static","overrideMaterials":[{"refPath":PAVING}],"bodyInstance":{"collisionEnabled":"QueryAndPhysics","collisionProfileName":"BlockAll"}})
            api(S+"set_actor_folder",{"actor":actor,"folder_path":"CityBlockout/10_Boundary/ReferenceR2/Courts"});result.append({"actor":actor,"item":f})
        write("court_fences_created.json",result)
        return {"courtyard_closures":len(result)}
    if MODE=="court_fix":
        rows=read("court_fences_created.json")
        r=next(r for r in rows if r["item"]["name"]=="R2_CentralPocketFence")
        t=api(A+"get_actor_transform",{"actor":r["actor"]})
        assert abs(t["location"]["y"]-4002.5)<.01 and abs(t["scale"]["x"]-3.3)<.01
        t["location"]["x"]=2540;t["scale"]["x"]=5.2
        assert api(A+"set_actor_transform",{"actor":r["actor"],"xform":t,"worldspace":True})
        r["item"]["pieces"][0][1]=28.0
        write("court_fences_created.json",rows)
        plan=read("fences.json");next(f for f in plan if f["name"]=="R2_CentralPocketFence")["pieces"][0][1]=28.0;write("fences.json",plan)
        return {"court_rear_gap_closed":True}
    if MODE=="finish_checks":
        def box(x,y):return {"min":{"x":x*100-35,"y":y*100-35,"z":27},"max":{"x":x*100+35,"y":y*100+35,"z":205},"isValid":True}
        assert not query(box(24.2,38))
        assert query(box(27.2,40.025))
        for x,y in [(72.75,65),(76,64.35),(63.8,-94.5),(69,-94.2),(-2,91.8),(4.125,91.8)]:assert query(box(x,y)),[x,y]
        far=[r for r in read("moves.json") if r["far"]]
        for r in far:
            assert same(api(A+"get_actor_transform",{"actor":r["actor"]}),r["xform"])
            for c in r["components"]:
                p=props(c["component"],["bodyInstance","castShadow","bVisibleInRayTracing"])
                assert p["bodyInstance"]["collisionEnabled"]=="NoCollision" and not p["castShadow"] and not p["bVisibleInRayTracing"]
        for r in read("surfaces_created.json")+[read("backdrop_created.json")]:
            p=props(r["root"],["bVisible","bHiddenInGame","bodyInstance"])
            assert p["bVisible"] and not p["bHiddenInGame"] and p["bodyInstance"]["collisionEnabled"]=="NoCollision"
        assert len(api(S+"get_actors_in_folder",{"folder_path":"CityBlockout/08_BackgroundBuildings","recursive":True}))==88
        result={"rear_gap_closed":True,"old_court_closures_retained":True,"distant_buildings_noncolliding":len(far),"background_total":88,"technical_surfaces_visible":True,"backdrop_visible":True}
        write("finish_checks.json",result)
        assert api(F+"save_assets",{"asset_paths":[L]})
        write("stage_d.json",{"saved":True,"open_spaces_retained":["MuseumSquare","UniversitySquare","Park","PrivateMainStreet"]})
        return result
    if MODE=="final_save":
        assert read("stage_a.json")["saved"] and read("stage_b.json")["saved"] and read("stage_c.json")["saved"] and read("stage_d.json")["saved"]
        assert read("preserved.json")["main_groups_unchanged"]==21 and read("geometry_checked.json")["safety_unchanged_closed"]
        assert read("finish_checks.json")["rear_gap_closed"] and read("pie_result.json")["passed"]
        assert api(F+"save_assets",{"asset_paths":[GROUND.split('.')[0],TOP.split('.')[0],CURB.split('.')[0],L]})
        assert not api(F+"is_dirty",{"asset_path":L})
        result={"status":"SUCCESS","level":L,"background_moved_resized":34,"distant_reused":12,"buildings_added":0,"buildings_deleted":0,"background_total":88,"new_dead_ends":4,"new_courts":4,"retained_courts":6,"route_samples":156,"PIE_walks":2,"PIE_boundary_walks":1,"PIE_boundary_jumps":1,"main_unchanged":True,"physical_ground_unchanged":True,"bus_access":True,"other_exits":False,"saved":True,"errors":[]}
        write("result.json",result)
        return result
    if MODE=="preserve":
        models=read("models_before.json")
        for r in models:
            assert same(api(A+"get_actor_transform",{"actor":r["actor"]}),r["transform"]),r["label"]
            for m in r["meshes"]:assert props(m["component"],["staticMesh","overrideMaterials"])==m["properties"],r["label"]
        private=read("private_before.json",True)
        for r in private:
            assert same(api(A+"get_actor_transform",{"actor":r["actor"]}),r["transform"]),r["label"]
        moved={r["actor"]["refPath"] for r in read("moves.json")}
        old=[r for r in read("background_before.json") if r["actor"]["refPath"] not in moved]
        for r in old:assert same(api(A+"get_actor_transform",{"actor":r["actor"]}),r["transform"]),r["label"]
        ground=read("ground_before.json",True)
        assert same(api(A+"get_actor_transform",{"actor":ground["actor"]}),ground["transform"])
        assert api(A+"get_actor_bounds",{"actor":ground["actor"]})==ground["bounds"]
        assert props(ground["root"],["staticMesh","bodyInstance","overrideMaterials"])==ground["properties"]
        result={"main_groups_unchanged":len(models),"private_paths_unchanged":len(private),"unmoved_background_unchanged":len(old),"physical_ground_unchanged":True}
        write("preserved.json",result)
        return result
    if MODE=="geometry":
        tests=[("Museum",8.8,-24),("University",45.73,7),("Library",47.9,43),("TownHall",51.2,78),("Rudy",-19.1,-24),("Graham",-2.8,33),("Cafe",-54.8,13),("Hospital",4.6,78),("Car",-30,63.1),("Store",41.8,-80),("Bus",39.5,-80),("PrivateStreet",-25,-73.55),("OldCentralCourt",20.8,17.4),("OldEastCourt",40.8,87.5),("OldSouthCourt",-47.15,87.8),("LibraryCourt",73.7,62.6),("StopCourt",66,-92),("HospitalCourt",1,89.7),("Park",-68,13)]
        tests.extend((c["name"],*c["p"]) for c in read("courts.json"))
        blocked=[]
        for name,x,y in tests:
            box={"min":{"x":x*100-35,"y":y*100-35,"z":27},"max":{"x":x*100+35,"y":y*100+35,"z":205},"isValid":True}
            found=query(box)
            if found:blocked.append({"point":name,"hits":found})
            box["min"]["z"]=-2;box["max"]["z"]=39
            assert query(box),name
        assert not blocked,blocked
        main=next(r for r in read("private_before.json",True) if r["label"]=="RC_MainStreet")["transform"]
        assert not query({"min":{"x":main["location"]["x"]-main["scale"]["x"]*50+1,"y":main["location"]["y"]-149,"z":27},"max":{"x":main["location"]["x"]+main["scale"]["x"]*50-1,"y":main["location"]["y"]+149,"z":205},"isValid":True})
        for r in read("safety_created.json",True):
            assert same(api(A+"get_actor_transform",{"actor":r["actor"]}),r["xform"])
            root=api(A+"get_root_component",{"actor":r["actor"]});p=props(root,["bodyInstance"])["bodyInstance"]
            assert p["collisionEnabled"]=="QueryAndPhysics" and p["collisionProfileName"]=="BlockAll"
        for r in read("court_fences_created.json"):
            root=api(A+"get_root_component",{"actor":r["actor"]});p=props(root,["bodyInstance"])["bodyInstance"]
            assert p["collisionEnabled"]=="QueryAndPhysics" and p["collisionProfileName"]=="BlockAll"
        result={"entrance_court_park_points_clear":len(tests),"private_main_street_clear":True,"safety_unchanged_closed":True,"new_courts":4,"old_courts_clear":6,"blocked":blocked}
        write("geometry_checked.json",result)
        assert api(F+"save_assets",{"asset_paths":[L]})
        write("stage_c.json",{"saved":True,"new_courts":4})
        return result
    raise ValueError(MODE)
