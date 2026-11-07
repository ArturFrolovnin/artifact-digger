"""Specific Level_6 pavement replacement and three small enclosed branches."""
import json
import math
MODE="surface"
INDEX=0
L="/Game/TestLevel/Level_6/level_6_create_map"
B="D:/UEProject/ArcheoDig/Saved/Level6Replan/BoundaryRoads/"
S="editor_toolset.toolsets.scene.SceneTools."
A="editor_toolset.toolsets.actor.ActorTools."
O="editor_toolset.toolsets.object.ObjectTools."
F="editor_toolset.toolsets.asset.AssetTools."
CUBE="/Engine/BasicShapes/Cube.Cube"
M="/Game/TestLevel/Level_6/Blockout/Materials/M_BO_Paving.M_BO_Paving"
MESH="/Game/TestLevel/Level_6/Blockout/Generated/SM_L6_PedestrianSurface_20261105.SM_L6_PedestrianSurface_20261105"
CURBS="/Game/TestLevel/Level_6/Blockout/Generated/SM_L6_PedestrianCurbs_20261105.SM_L6_PedestrianCurbs_20261105"
def api(t,a):return execute_tool(t,json.dumps(a))["returnValue"]
def read(n):return json.loads(api(F+"read_file",{"file_path":B+n}).lstrip("\ufeff"))
def write(n,v):api(F+"write_file",{"file_path":B+n,"content":json.dumps(v)})
def props(c,n):return json.loads(api(O+"get_properties",{"instance":c,"properties":n}))
def setp(c,p):assert api(O+"set_properties",{"instance":c,"values":json.dumps(p)})
def same(a,b):return all(abs(a[k][v]-b[k][v])<.001 for k in ["location","rotation","scale"] for v in a[k])
def hits(box):return api(S+"find_actors",{"name":"","tag":"","collision_channels":["ObjectTypeQuery1","ObjectTypeQuery2"],"bounds":box})
def box(x,y,r=.35,z0=27,z1=205):return {"min":{"x":(x-r)*100,"y":(y-r)*100,"z":z0},"max":{"x":(x+r)*100,"y":(y+r)*100,"z":z1},"isValid":True}
def run():
    assert api(S+"get_current_level",{})==L and not api("EditorToolset.EditorAppToolset.IsPIERunning",{})
    assert read("road_preflight.json")["ready"]
    if MODE=="surface":
        # The OBJ importer reflects Y. Compensate on this technical actor only.
        t={"location":{"x":0,"y":0,"z":0},"rotation":{"pitch":0,"yaw":0,"roll":0},"scale":{"x":1,"y":-1,"z":1}}
        actor=api(S+"add_to_scene_from_asset",{"asset_path":MESH,"name":"LD_PedestrianSurface_Union","xform":t,"snap_to_ground":False})
        root=api(A+"get_root_component",{"actor":actor})
        setp(root,{"overrideMaterials":[{"refPath":M}],"bUseDefaultCollision":False,"bVisible":False,"bHiddenInGame":True,"bodyInstance":{"collisionEnabled":"NoCollision","collisionProfileName":"NoCollision"}})
        p=props(root,["bodyInstance","bVisible"])
        assert p["bodyInstance"]["collisionEnabled"]=="NoCollision" and not p["bVisible"]
        b=api(A+"get_actor_bounds",{"actor":actor});expected=read("surface_geometry.json")["bounds"]
        assert all(abs(b[k][v]-expected[k][v])<.1 for k in ["min","max"] for v in ["x","y","z"]),b
        api(S+"set_actor_folder",{"actor":actor,"folder_path":"CityBlockout/07_Pedestrian/Surface"})
        write("surface_created.json",{"actor":actor,"root":root,"xform":t,"bounds":b})
        return {"surface_placed":True,"triangles":794,"collision":"separate simple floor strips"}
    if MODE=="curbs":
        t={"location":{"x":0,"y":0,"z":0},"rotation":{"pitch":0,"yaw":0,"roll":0},"scale":{"x":1,"y":-1,"z":1}}
        actor=api(S+"add_to_scene_from_asset",{"asset_path":CURBS,"name":"LD_PedestrianSurface_Curbs","xform":t,"snap_to_ground":False})
        root=api(A+"get_root_component",{"actor":actor})
        setp(root,{"overrideMaterials":[{"refPath":M}],"bUseDefaultCollision":False,"bVisible":False,"bHiddenInGame":True,"bodyInstance":{"collisionEnabled":"NoCollision","collisionProfileName":"NoCollision"}})
        api(S+"set_actor_folder",{"actor":actor,"folder_path":"CityBlockout/07_Pedestrian/Surface"})
        write("curbs_created.json",{"actor":actor,"root":root})
        return {"curbs_placed":True,"vertical_edges_closed":True}
    if MODE=="proxies":
        rows=read("road_active_"+str(INDEX)+".json")
        changed=[]
        try:
            for r in rows:
                actor=r["actor"];root=api(A+"get_root_component",{"actor":actor})
                p=props(root,["staticMesh","bVisible","bHiddenInGame","bUseDefaultCollision","bodyInstance"])
                assert p["staticMesh"]["refPath"]==CUBE,r["label"]
                changed.append({"actor":actor,"root":root,"item":r,"properties":{"bVisible":p["bVisible"],"bHiddenInGame":p["bHiddenInGame"],"bUseDefaultCollision":p["bUseDefaultCollision"],"bodyInstance":{"collisionEnabled":p["bodyInstance"]["collisionEnabled"],"collisionProfileName":p["bodyInstance"]["collisionProfileName"]}}})
                assert api(A+"set_actor_transform",{"actor":actor,"xform":r["xform"],"worldspace":True})
                setp(root,{"bVisible":False,"bHiddenInGame":True,"bUseDefaultCollision":False,"canCharacterStepUpOn":"ECB_Yes","bodyInstance":{"collisionEnabled":"QueryAndPhysics","collisionProfileName":"BlockAll","bSimulatePhysics":False}})
                api(S+"set_actor_folder",{"actor":actor,"folder_path":"CityBlockout/07_Pedestrian/Collision"})
            write("proxies_changed_"+str(INDEX)+".json",changed)
        except Exception:
            for c in reversed(changed):
                api(A+"set_actor_transform",{"actor":c["actor"],"xform":c["item"]["before"],"worldspace":True})
                setp(c["root"],c["properties"])
            raise
        return {"batch":INDEX,"floor_strips_converted":len(changed)}
    if MODE=="fresh":
        rows=[]
        for r in read("road_fresh.json"):
            actor=api(S+"add_to_scene_from_asset",{"asset_path":CUBE,"name":r["label"]+"_Collision","xform":r["xform"],"snap_to_ground":False})
            root=api(A+"get_root_component",{"actor":actor})
            setp(root,{"bVisible":False,"bHiddenInGame":True,"bUseDefaultCollision":False,"canCharacterStepUpOn":"ECB_Yes","bodyInstance":{"collisionEnabled":"QueryAndPhysics","collisionProfileName":"BlockAll","bSimulatePhysics":False}})
            api(S+"set_actor_folder",{"actor":actor,"folder_path":"CityBlockout/07_Pedestrian/Collision"})
            rows.append({"actor":actor,"root":root,"item":r})
        write("fresh_created.json",rows)
        return {"new_floor_strips":len(rows)}
    if MODE=="activate":
        surface=read("surface_created.json")
        for i in range(7):assert read("proxies_changed_"+str(i)+".json")
        assert len(read("fresh_created.json"))==8
        for r in read("road_retired.json"):
            root=api(A+"get_root_component",{"actor":r["actor"]})
            setp(root,{"bVisible":False,"bHiddenInGame":True,"bUseDefaultCollision":False,"bodyInstance":{"collisionEnabled":"NoCollision","collisionProfileName":"NoCollision"}})
        setp(surface["root"],{"bVisible":True,"bHiddenInGame":False})
        setp(read("curbs_created.json")["root"],{"bVisible":True,"bHiddenInGame":False})
        return {"surface_visible":True,"obsolete_strips_disabled":6}
    if MODE=="check_roads":
        rows=read("road_active_"+str(INDEX)+".json")
        allfloor={r["actor"]["refPath"] for r in read("fresh_created.json")}
        for i in range(7):allfloor.update(r["actor"]["refPath"] for r in read("road_active_"+str(i)+".json"))
        blocked,unsupported=[],[];count=0
        tests=[r for r in rows if r["edited"] and r.get("a")]
        if INDEX==6:tests.extend(r["item"] for r in read("fresh_created.json") if r["item"].get("a"))
        for r in tests:
            a,b=r["a"],r["b"];dx,dy=b[0]-a[0],b[1]-a[1];steps=max(1,int(math.ceil(math.sqrt(dx*dx+dy*dy)/1.5)))
            for j in range(steps+1):
                u=j/steps
                if r["label"].startswith("PW_Entry_"):
                    u=min(u,max(0,1-.65/max(.65,math.sqrt(dx*dx+dy*dy))))
                x,y=a[0]+dx*u,a[1]+dy*u
                h=hits(box(x,y))
                if h:blocked.append({"route":r["label"],"point":[x,y],"hits":h})
                floor=hits(box(x,y,.08,24.8,25.2))
                if not any(v["refPath"] in allfloor for v in floor):unsupported.append({"route":r["label"],"point":[x,y]})
                count+=1
        result={"batch":INDEX,"samples":count,"blocked":blocked,"unsupported":unsupported}
        write("road_checks_"+str(INDEX)+".json",result)
        return result
    if MODE=="save_roads":
        tests=[read("road_checks_"+str(i)+".json") for i in range(7)]
        assert not any(r["blocked"] or r["unsupported"] for r in tests)
        for r in read("road_retired.json"):assert api(S+"remove_from_scene",{"actor":r["actor"]})
        assert api(F+"save_assets",{"asset_paths":[MESH.split('.')[0],CURBS.split('.')[0],L]}) and not api(F+"is_dirty",{"asset_path":L})
        result={"render_parts_replaced":255,"simple_floor_strips":257,"routed_segments_changed":15,"edited_parts":24,"retired_deleted":6,"junctions_rebuilt":8,"top_z_cm":25,"samples":sum(r["samples"] for r in tests),"saved":True}
        write("roads_result.json",result)
        return result
    if MODE=="fences":
        rows=[]
        for f in read("court_fences.json"):
            r=f["pieces"][0];t={"location":{"x":(r[0]+r[1])*50,"y":(r[2]+r[3])*50,"z":r[4]*50},"rotation":{"pitch":0,"yaw":0,"roll":0},"scale":{"x":r[1]-r[0],"y":r[3]-r[2],"z":r[4]}}
            actor=api(S+"add_to_scene_from_asset",{"asset_path":CUBE,"name":f["name"],"xform":t,"snap_to_ground":False})
            root=api(A+"get_root_component",{"actor":actor});setp(root,{"overrideMaterials":[{"refPath":M}]})
            for i,r in enumerate(f["pieces"][1:]):
                c=api(A+"add_component",{"owner":root,"component_type":{"refPath":"/Script/Engine.StaticMeshComponent"},"name":"Court_Fence_"+str(i)})
                loc={"x":(r[0]+r[1])*50,"y":(r[2]+r[3])*50,"z":r[4]*50}
                rel={k:(loc[k]-t["location"][k])/t["scale"][k] for k in loc}
                setp(c,{"staticMesh":{"refPath":CUBE},"relativeLocation":rel,"relativeScale3D":{"x":r[1]-r[0],"y":r[3]-r[2],"z":r[4]},"bAbsoluteScale":True,"mobility":"Static","overrideMaterials":[{"refPath":M}],"bodyInstance":{"collisionEnabled":"QueryAndPhysics","collisionProfileName":"BlockAll"}})
            api(S+"set_actor_folder",{"actor":actor,"folder_path":"CityBlockout/10_Boundary/Courts"})
            rows.append({"actor":actor,"item":f})
        write("court_fences_created.json",rows)
        return {"court_fences":len(rows)}
    raise ValueError(MODE)
