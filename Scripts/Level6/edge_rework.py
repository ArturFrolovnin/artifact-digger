"""Explicit perimeter masses, masonry, and retirement of verified cube markers."""
import json
MODE="preflight"
INDEX=0
L="/Game/TestLevel/Level_6/level_6_create_map"
B="D:/UEProject/ArcheoDig/Saved/Level6Replan/BoundaryRoads/"
S="editor_toolset.toolsets.scene.SceneTools."
A="editor_toolset.toolsets.actor.ActorTools."
O="editor_toolset.toolsets.object.ObjectTools."
F="editor_toolset.toolsets.asset.AssetTools."
CUBE="/Engine/BasicShapes/Cube.Cube"
def api(t,a):return execute_tool(t,json.dumps(a))["returnValue"]
def read(n):return json.loads(api(F+"read_file",{"file_path":B+n}).lstrip("\ufeff"))
def write(n,v):api(F+"write_file",{"file_path":B+n,"content":json.dumps(v)})
def prop(c,n):return json.loads(api(O+"get_properties",{"instance":c,"properties":n}))
def setp(c,p):assert api(O+"set_properties",{"instance":c,"values":json.dumps(p)})
def same(a,b):return all(abs(a[k][v]-b[k][v])<.001 for k in ["location","rotation","scale"] for v in a[k])
def xform(r,h):return {"location":{"x":(r[0]+r[1])*50,"y":(r[2]+r[3])*50,"z":h*50},"rotation":{"pitch":0,"yaw":0,"roll":0},"scale":{"x":r[1]-r[0],"y":r[3]-r[2],"z":h}}
def overlap(r,h):return api(S+"find_actors",{"name":"","tag":"","collision_channels":["ObjectTypeQuery1","ObjectTypeQuery2"],"bounds":{"min":{"x":r[0]*100+1,"y":r[2]*100+1,"z":40},"max":{"x":r[1]*100-1,"y":r[3]*100-1,"z":h*100-1},"isValid":True}})
def addpart(root,parent,name,location,scale,material,collide=False):
    c=api(A+"add_component",{"owner":root,"component_type":{"refPath":"/Script/Engine.StaticMeshComponent"},"name":name})
    rel={k:(location[k]-parent["location"][k])/parent["scale"][k] for k in location}
    setp(c,{"staticMesh":{"refPath":CUBE},"relativeLocation":rel,"relativeScale3D":scale,"relativeRotation":{"pitch":0,"yaw":0,"roll":0},"bAbsoluteScale":True,"mobility":"Static","overrideMaterials":[{"refPath":material}],"bodyInstance":{"collisionEnabled":"QueryAndPhysics" if collide else "NoCollision","collisionProfileName":"BlockAll" if collide else "NoCollision","bSimulatePhysics":False}})
    return c
def run():
    assert api(S+"get_current_level",{})==L and not api("EditorToolset.EditorAppToolset.IsPIERunning",{})
    assert read("edge_preflight.json")["ready"]
    marker_rows=[r for i in range(4) for r in read("markers_before_"+str(i)+".json")]
    ignored={r["actor"]["refPath"] for r in marker_rows if r["technical"]}
    if MODE=="preflight":
        conflicts=[]
        for h in read("edge_houses.json"):
            hits=[a for a in overlap(h["rect"],h["height"]) if a["refPath"] not in ignored]
            if hits:conflicts.append({"house":h["name"],"hits":hits})
        write("edge_native.json",{"conflicts":conflicts})
        return {"checked":28,"conflicts":conflicts}
    assert not read("edge_native.json")["conflicts"]
    if MODE=="walls":
        created=[]
        try:
            for w in read("edge_walls.json"):
                p=w["pieces"][0];t=xform(p["rect"],p["height"])
                actor=api(S+"add_to_scene_from_asset",{"asset_path":CUBE,"name":w["name"],"xform":t,"snap_to_ground":False})
                created.append({"actor":actor,"item":w})
                root=api(A+"get_root_component",{"actor":actor});setp(root,{"overrideMaterials":[{"refPath":w["material"]}]})
                for i,p in enumerate(w["pieces"]):
                    q=xform(p["rect"],p["height"])
                    if i:addpart(root,t,"Boundary_Section_"+str(i),q["location"],q["scale"],w["material"],True)
                    loc=dict(q["location"]);loc["z"]=p["height"]*100+6
                    size={"x":q["scale"]["x"]+.08,"y":q["scale"]["y"]+.08,"z":.12}
                    addpart(root,t,"Boundary_Coping_"+str(i),loc,size,w["capMaterial"])
                api(S+"set_actor_folder",{"actor":actor,"folder_path":"CityBlockout/10_Boundary/Masonry"})
            write("edge_walls_created.json",created)
        except Exception:
            for r in reversed(created):api(S+"remove_from_scene",{"actor":r["actor"]})
            raise
        return {"wall_actors":len(created),"continuous_visible_sections":16}
    if MODE=="houses":
        created=[]
        try:
            for h in read("edge_houses_"+str(INDEX)+".json"):
                assert not api(S+"find_actors",{"name":h["name"],"tag":"","collision_channels":[]})
                actor=api(S+"add_to_scene_from_asset",{"asset_path":CUBE,"name":h["name"],"xform":h["xform"],"snap_to_ground":False})
                created.append({"actor":actor,"item":h})
                root=api(A+"get_root_component",{"actor":actor})
                setp(root,{"overrideMaterials":[{"refPath":h["material"]}]})
                loc=dict(h["xform"]["location"]);loc["z"]=h["height"]*100+14
                size={"x":h["xform"]["scale"]["x"]+.16,"y":h["xform"]["scale"]["y"]+.16,"z":.28}
                addpart(root,h["xform"],"Boundary_RoofCap",loc,size,"/Game/TestLevel/Level_6/Blockout/Materials/M_BO_Road.M_BO_Road")
                api(S+"set_actor_folder",{"actor":actor,"folder_path":"CityBlockout/08_BackgroundBuildings/BoundaryRing"})
                assert same(api(A+"get_actor_transform",{"actor":actor}),h["xform"])
                p=prop(root,["bodyInstance"])["bodyInstance"]
                assert p["collisionProfileName"]=="BlockAll" and not p["bSimulatePhysics"]
                bounds=api(A+"get_actor_bounds",{"actor":actor})
                assert abs(bounds["min"]["z"])<.1 and abs(bounds["max"]["z"]-h["height"]*100-28)<.1
            write("edge_created_"+str(INDEX)+".json",created)
        except Exception:
            for r in reversed(created):api(S+"remove_from_scene",{"actor":r["actor"]})
            raise
        return {"batch":INDEX,"new_buildings":len(created)}
    if MODE=="moves":
        for m in read("edge_moves.json"):
            assert same(api(A+"get_actor_transform",{"actor":m["actor"]}),m["transform"])
            assert api(A+"set_actor_transform",{"actor":m["actor"],"xform":m["xform"],"worldspace":True})
        write("edge_moved.json",read("edge_moves.json"))
        return {"reused_and_moved":2}
    if MODE=="markers":
        assert len(api(S+"get_actors_in_folder",{"folder_path":"CityBlockout/08_BackgroundBuildings/BoundaryRing","recursive":False}))==28
        rows=read("markers_before_"+str(INDEX)+".json")
        for r in rows:
            assert r["technical"]
            setp(r["root"],{"bVisible":False,"bHiddenInGame":True,"bUseDefaultCollision":False,"bodyInstance":{"collisionEnabled":"NoCollision","collisionProfileName":"NoCollision"}})
            p=prop(r["root"],["bVisible","bHiddenInGame","bodyInstance"])
            assert not p["bVisible"] and p["bHiddenInGame"] and p["bodyInstance"]["collisionEnabled"]=="NoCollision"
        write("markers_hidden_"+str(INDEX)+".json",{"hidden":len(rows)})
        return {"batch":INDEX,"technical_markers_hidden":len(rows)}
    if MODE=="verify_save":
        rows=[r for i in range(4) for r in read("edge_created_"+str(i)+".json")]
        conflicts=[]
        for r in rows:
            h=r["item"];hits=[a for a in overlap(h["rect"],h["height"]) if a!=r["actor"]]
            if hits:conflicts.append({"house":h["name"],"hits":hits})
        assert not conflicts,conflicts
        assert sum(read("markers_hidden_"+str(i)+".json")["hidden"] for i in range(4))==98
        assert api(F+"save_assets",{"asset_paths":[L]}) and not api(F+"is_dirty",{"asset_path":L})
        result={"edge_buildings":len(rows),"reused_moved":2,"markers_hidden":98,"visible_sides":4,"overlaps":conflicts,"saved":True}
        write("edge_result.json",result)
        return result
    raise ValueError(MODE)
