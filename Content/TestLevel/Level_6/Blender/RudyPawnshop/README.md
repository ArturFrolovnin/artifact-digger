# Uncle Rudy's pawnshop

Approved exterior preserved from the open Blender scene on 2026-10-05.

- Editable source: `Source/RudyPawnshop.blend` (51 mesh assemblies, 4 editable text objects).
- Export: `Source/SM_RudyPawnshop.fbx` (55 mesh objects, lettering converted on temporary copies).
- Unreal mesh: `/Game/TestLevel/Level_6/Blender/RudyPawnshop/SM_RudyPawnshop`.
- 28 materials in `Materials/`; 16,875 imported triangles.
- Body footprint: 10 x 8 m; complete bounds: 12.66855 x 10.06 x 9.85 m.
- Level: `/Game/TestLevel/Level_6/level_6_create_map`; existing actor `BO_Pawnshop` replaced in place.
- Placement: (1600, 3500, 24) cm, yaw 90 degrees, scale (1, 1, 1). Entrance faces -X.
- FBX: -Y forward, Z up, unit scale baked from metres to centimetres.
- UV0 uses face projection to provide non-degenerate tangent coordinates; material colours and geometry are unchanged.

`Source/export_fbx.py` runs in the open Blender scene and preserves editable lettering.
`Source/finish_ue_import.py` runs inside Unreal Editor Python to update the existing mesh and restore its material assignments.
`Source/Scripts/build_rudy.py` is the original construction script; do not rerun over the existing building.

The model is an exterior; no interior was added.
