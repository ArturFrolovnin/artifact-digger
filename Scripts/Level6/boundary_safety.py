"""Four continuous safety strips around the existing Level_6 ground slab."""
import json
LEVEL="/Game/TestLevel/Level_6/level_6_create_map"
BASE="D:/UEProject/ArcheoDig/Saved/Level6Replan/BoundaryRoads/"
S="editor_toolset.toolsets.scene.SceneTools."
A="editor_toolset.toolsets.actor.ActorTools."
O="editor_toolset.toolsets.object.ObjectTools."
F="editor_toolset.toolsets.asset.AssetTools."
def api(t,a):return execute_tool(t,json.dumps(a))["returnValue"]
def run():
    assert api(S+"get_current_level",{})==LEVEL
    # A rolled-back task-owned attempt can leave the level package dirty.
    assert not api(S+"find_actors",{"name":"Boundary_Safety_","tag":"","collision_channels":[]})
    assert not api("EditorToolset.EditorAppToolset.IsPIERunning",{})
    exits=[]
    for name in ["Exit","Portal","Teleport","Travel","Trigger"]:
        exits.extend(api(S+"find_actors",{"name":name,"tag":"","collision_channels":[]}))
    # Inside faces at X +/-79.2 m and Y +/-99.2 m, safely within the slab.
    spec=[("XMin",[-79.6,0,2],[.8,200.8,24]),("XMax",[79.6,0,2],[.8,200.8,24]),("YMin",[0,-99.6,2],[160.8,.8,24]),("YMax",[0,99.6,2],[160.8,.8,24])]
    rows=[]
    try:
        for name,p,d in spec:
            t={"location":dict(zip(["x","y","z"],[v*100 for v in p])),"rotation":{"pitch":0,"yaw":0,"roll":0},"scale":dict(zip(["x","y","z"],d))}
            # No ordinary colliding actor may occupy the thin strip above ground.
            q={"min":{"x":p[0]*100-d[0]*50+1,"y":p[1]*100-d[1]*50+1,"z":40},"max":{"x":p[0]*100+d[0]*50-1,"y":p[1]*100+d[1]*50-1,"z":1400},"isValid":True}
            hits=api(S+"find_actors",{"name":"","tag":"","collision_channels":["ObjectTypeQuery1","ObjectTypeQuery2"],"bounds":q})
            assert not [h for h in hits if h not in [r["actor"] for r in rows]],name
            actor=api(S+"add_to_scene_from_asset",{"asset_path":"/Engine/BasicShapes/Cube.Cube","name":"Boundary_Safety_"+name,"xform":t,"snap_to_ground":False})
            rows.append({"actor":actor,"xform":t,"name":name})
            root=api(A+"get_root_component",{"actor":actor})
            assert api(O+"set_properties",{"instance":root,"values":json.dumps({"bVisible":False,"bHiddenInGame":True,"bGenerateOverlapEvents":False,"bodyInstance":{"collisionProfileName":"BlockAll","collisionEnabled":"QueryAndPhysics","bSimulatePhysics":False}})})
            api(S+"set_actor_folder",{"actor":actor,"folder_path":"CityBlockout/10_Boundary/Safety"})
            p=json.loads(api(O+"get_properties",{"instance":root,"properties":["bVisible","bHiddenInGame","bodyInstance"]}))
            assert not p["bVisible"] and p["bHiddenInGame"] and p["bodyInstance"]["collisionProfileName"]=="BlockAll"
            rows[-1]["bounds"]=api(A+"get_actor_bounds",{"actor":actor})
        traces=0
        for z in [50,180,350]:
            for f in [-.97,-.5,0,.5,.97]:
                pairs=[([78.5,f*98, z/100],[82,f*98,z/100]),([-78.5,f*98,z/100],[-82,f*98,z/100]),([f*78,98.5,z/100],[f*78,102,z/100]),([f*78,-98.5,z/100],[f*78,-102,z/100])]
                for a,b in pairs:
                    distance=api(S+"trace_world",{"start":dict(zip(["x","y","z"],[v*100 for v in a])),"end":dict(zip(["x","y","z"],[v*100 for v in b]))})
                    assert distance is not None and 65<=distance<=75,{"start":a,"distance":distance}
                    traces+=1
        assert rows[0]["bounds"]["max"]["y"]>rows[3]["bounds"]["max"]["y"]
        assert rows[2]["bounds"]["max"]["x"]>rows[1]["bounds"]["max"]["x"]
        api(F+"write_file",{"file_path":BASE+"safety_created.json","content":json.dumps(rows)})
        result={"continuous_sides":4,"corner_overlaps":True,"base_z_cm":-1000,"top_z_cm":1400,"trace_checks":traces,"dangerous_gaps":0,"exit_candidates":exits}
        api(F+"write_file",{"file_path":BASE+"safety_checked.json","content":json.dumps(result)})
    except Exception:
        for r in reversed(rows):api(S+"remove_from_scene",{"actor":r["actor"]})
        raise
    assert api(F+"save_assets",{"asset_paths":[LEVEL]})
    assert not api(F+"is_dirty",{"asset_path":LEVEL})
    return result
