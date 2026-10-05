# Museum — Blender export and UE import

Current editable source: `Source/Museum_Blockout.blend`.
FBX geometry: `Source/SM_Museum_Blockout.fbx`.
Older museum sources are preserved in `Source/Archive/`.
Museum-specific scripts: `Scripts/`. Historical build/refinement scripts are archived recipes, not needed to export the current scene.

## Validated Blender export

- Existing design retained; 553 separate geometry objects plus `Museum_ROOT`.
- Metres, unit scale 1. Root position/rotation zero, scale (1,1,1).
- Full bounds including mouldings: 31.07596 × 24.55275 × 12.48 m.
- Ground minimum Z = 0.
- FBX: -Y forward, Z up; `FBX_SCALE_NONE`, `apply_unit_scale=True`, global scale 1.
- Transforms and modifiers baked on temporary export meshes only; editable text/curves retained in source.
- Normals recalculated; open window surfaces oriented outward. 147 zero-area faces removed on temporary copies; zero remain.
- Camera, Light, ROOT and other helpers excluded. No animation.
- Basic projection UVs only; not a production UV pass.
- Validation: `Source/export_validation.txt`; material values: `Materials/material_manifest.txt`.

## UE delivery status

Import and placement completed on 2026-10-05; mesh, materials and level saved.
Mesh: `/Game/TestLevel/Level_6/Blender/Museum/SM_Museum_Blockout` (71,200 triangles).
Materials: `/Game/TestLevel/Level_6/Blender/Museum/Materials/`:
`MUS_Stone`, `MUS_Stone_Trim`, `MUS_Stone_Base`, `MUS_Roof`,
`MUS_Glass`, `MUS_Glass_Cupola`, `MUS_Glass_Warm`, `MUS_Wood`,
`MUS_Metal`, `MUS_Metal_Gold`, `MUS_Banner`, `MUS_Recess`, `MUS_Lantern_Amber`.
Import and actor scale: 1. UE local bounds (cm):
min (-1553.7981,-1105.2751,0), max (1553.7981,1350,1248).
Materials use simple base color / roughness / metallic values and two-sided rendering for open decorative surfaces.

Verified placement target: `BO_Museum` in `/Game/TestLevel/Level_6/level_6_create_map`.
Its original block centre is (2300,600,574) cm, plot surface Z = 24 cm.
Placed mesh root: (2300,600,24) cm, yaw 90 degrees, entrance toward -X and park.
World ground min Z = 24 cm; verified against plot surface.
Neighboring actor transforms and museum plot remain unchanged. Only the BO_Museum mesh/transform was replaced.
The roof eaves slightly exceed the original 30 m plot width; no building scale adjustment is intended.
Player-height (camera Z = 184 cm) and overall three-quarter views inspected in UE.
No intersections with adjacent buildings or road surfaces observed. Colours are brighter under the current UE daylight; no design/material matching pass was performed.
Reports: `Source/ue_import_report.txt`, `Source/placement_report.txt`.
