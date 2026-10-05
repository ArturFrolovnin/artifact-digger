# Building assets

Keep each building in its own named folder. Do not put building materials or meshes in this root.

- `RudyPawnshop/`: Uncle Rudy's pawnshop; `SM_RudyPawnshop`, `Materials/`, editable Blender and FBX under `Source/`.
- `Dormitory/`: campus dormitory; `SM_Dormitory_Blockout`, `Materials/`, editable Blender and FBX under `Source/`.
- `Museum/`: current editable museum and FBX under `Source/`, dedicated `Materials/` and `Scripts/`; see its README for import/placement status.

Building-specific scripts are kept inside each building's folder; see its README for the script location and usage.
Move Unreal assets through the editor so references remain valid.
Diagnostic reports use `.txt` to avoid Unreal treating JSON reports as DataTables.

## Dormitory import status

BO_Dormitory replaced in place in level_6_create_map:
location (5700,7400,24) cm; yaw 90 degrees; scale (1,1,1).
Ground aligns with the plot top at 24 cm; entry points towards -X.
UE import combines meshes into one Static Mesh, source blend remains separate.
Map and imported assets saved. No additional detail or interior added.


## Visual validation note

Geometry and units are validated between Blender and UE, but viewport colors are not expected to match 1:1.
Blender AgX/viewport lighting and Unreal exposure/tonemapping produce noticeably different results, and FBX does not preserve Blender shaders exactly.

For this blockout workflow:
- Blender is the editable geometry/source scene;
- UE5 is the final visual check for scale, silhouette and material perception;
- prefer simple Base Color / Roughness / Metallic materials until the building design is locked.
