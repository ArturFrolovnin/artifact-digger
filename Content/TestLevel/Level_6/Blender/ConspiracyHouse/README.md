# Conspiracy house transfer

Imported and placed on the user-approved Neighbor_1 plot. Assets and Level_6 saved.

## Source and export

- Editable source: `Source/ConspiracyHouse_Blockout.blend`.
- Source SHA256 before and after export: `7d6f560111404fd7a8ae5766571b71ff2a9b475e616ae0bd8634861757611fa7`.
- The source was subsequently saved again between sessions. SHA256 of the file retained for the final commit: `3cdfac7c7d4b503cbd6a357e13290459ab2ea11883577dc59652b95e0bd6b462`. Finalization preserves this file and does not re-export it; Blender is not connected in the final session, so source/export equality has not been revalidated after that save.
- The connected Blender scene was already saved at this path with no unsaved changes. Architecture, materials and source geometry were retained.
- FBX: `Source/SM_ConspiracyHouse_{Blockout,Equipment,Fence,Garden,Props,Pathways}.fbx`.
- UE: `/Game/TestLevel/Level_6/Blender/ConspiracyHouse/SM_ConspiracyHouse_{Blockout,Equipment,Fence,Garden,Props,Pathways}`.
- Materials: `/Game/TestLevel/Level_6/Blender/ConspiracyHouse/Materials/CH_*` (32 instances and an independent CH_Master).

Export follows the MiaHouse pipeline: metres, -Y forward, Z up, unit conversion, FBX_SCALE_NONE, no cameras/lights/animation. Evaluated temporary meshes preserve modifiers and curves. Normals were recalculated and 72 zero-area faces removed only on export copies. All temporary objects were removed afterward. No blend backup, image, render or Review directory was created.

Blockout contains the building, porch, workshop, chimney, gutters and downpipes. Equipment contains Antennas, Telescope, ExperimentalDevices and the two coax cables plus electrical junction. Fence, Garden, ExteriorProps and Pathways are exported separately. All six meshes share the source origin. Equipment is one grouped mesh; its individual devices remain editable in Blender.

The existing fence contains four coincident corner-post pairs: Fence_Post / .016, .007 / .025, .008 / .024, .015 / .033. These were retained to preserve the supplied model. No invalid coordinates were found.

## Validation

- Main body: 8 x 10 m.
- Building including porch, workshop, roof and chimney: 11.183455 x 13.085001 x 6.722500 m.
- Highest antenna point: 8.020000 m above source ground.
- Complete yard footprint: 14 x 16 m.
- Six meshes contain 201,255 triangles in total; each mesh triangle count exactly matches its export.
- Bounds match Blender after the expected Y-axis handedness conversion, maximum error 0.000090 cm.
- Import scale 1, imported normals, combined meshes, one LOD, Nanite disabled.
- All 46 material slots and all 32 instances' BaseColor, Roughness, Metallic, Opacity and Emissive values verified.
- Complex-as-simple collision avoids a single convex hull closing off the yard.
- All 39 intended UE assets saved and verified clean.
- Unreal's automatic content monitoring also created unwanted per-object assets under Source. Those assets were removed; source files were preserved and their hash rechecked. For later exports, account for auto-import monitoring before writing FBX under Content.

Detailed numeric reports: `Source/export_validation.txt`, `Source/material_manifest.txt`, `Source/ue_import_report.txt`. `Source/verify_import.py` is intended for Unreal ProgrammaticToolset execution, not standalone Python.

## Completed placement

The level is `/Game/TestLevel/Level_6/level_6_create_map`. The user approved Neighbor_1 for the conspiracy resident. Remaining unassigned blockouts are BO_Neighbor_2, 5, 6, 7 and 8; Mia occupies the former Neighbor_4, now BO_Plot_MiaHouse, beside BO_Plot_PlayerHouse.

Plot: **BO_Plot_Neighbor_1**. **BO_Neighbor_1** was replaced in place and renamed **ConspiracyHouse_Blockout**. Its old material override was cleared. Equipment, Fence, Garden, Props and Pathways are separate Static Mesh Actors under `CityBlockout/Residential/ConspiracyHouse`.

- Plot bounds: X -4200..-2600 cm, Y -3800..-2400 cm; top Z=24 cm (16 m along world X, 14 m along world Y).
- Final common transform: Location (-3400,-3100,24) cm, Yaw +90 degrees, Scale (1,1,1).
- Imported entrance faces local +Y; this yaw points it towards world -X and the residential street.
- The complete yard fits the plot at unit scale. Neighbor_1 is separated from the next plot, so it does not share Mia's player-boundary complication.

Removed only `BO_Path_Neighbor_1` and its five obsolete fence actors: `BO_FenceSide_Neighbor_1-1`, `BO_FenceSide_Neighbor_11`, `BO_FenceRear_Neighbor_1`, `BO_FenceFront_Neighbor_1-1`, `BO_FenceFront_Neighbor_11`. The plot base was retained. No shared boundary was removed.

All six actors fit the plot within 0.001 cm tolerance. The house bottom is at the plot top, Z=24 cm. No neighboring building or tree bounds overlap the plot. The other 368 actors retain their original labels and transforms; the level contains 374 actors after replacing six obsolete environment actors with five new ones. Final verification was repeated in the reopened level before saving.

The original gate remains closed and collidable. A trace hits its picket; a trace inside the gate toward the porch is clear. Interactive gate opening and a full player traversal test are not implemented by this transfer. No visual validation is claimed; screenshots were prohibited by the task. The viewport camera was positioned for the user's review.

`Source/placement_report.txt` records the original affected actors, compact checks for the protected actors, final transforms, bounds, collision traces and save status. `Source/finalize_placement.py` verifies this approved placement and saves its assets and Level_6 through Unreal ProgrammaticToolset. It does not generate or place geometry.
