# Mia Raine house transfer

Source: `Source/MiaHouse_Blockout.blend`. Existing editable scene retained without architectural changes or backup copies.

FBX files: `Source/SM_MiaHouse_{Blockout,Fence,Garden,Pathways}.fbx`.
UE meshes: `/Game/TestLevel/Level_6/Blender/MiaHouse/SM_MiaHouse_{Blockout,Fence,Garden,Pathways}`.
Materials: `/Game/TestLevel/Level_6/Blender/MiaHouse/Materials/`.

Import completed and saved: four Static Mesh assets, one parameterized master material and 33 material instances. All 52 mesh material slots verified. Original Base Color, Roughness and Metallic values verified for all 33 instances; emissive values transferred. Office glass uses translucent blending with opacity 0.15 to approximate source transmission 0.85. Import scale is 1 and normals are imported. Mesh bounds match evaluated Blender dimensions within 0.001 cm. UE removes degenerate triangles during import/build; triangle counts are recorded in `Source/ue_import_report.txt`. This is numeric validation, not completed in-level visual review.

Export uses metres, -Y forward, Z up, FBX_SCALE_NONE, unit conversion enabled, no cameras/lights/animation. Evaluated temporary meshes preserve modifiers and source geometry. Normals are recalculated and zero-area faces removed on export objects only. `Source/export_fbx.py` transfers the current scene; it does not generate a house. Validation and the original material values are in `Source/export_validation.txt` and `Source/material_manifest.txt`.

Main foundation footprint: 8.17 x 10.17 m. House including porches, roof and side veranda: 11.049225 x 14.735000 x 6.315000 m. Garden footprint: 14 x 16 m. Fence top: 1.245 m above source ground. Window flower boxes remain with the house; freestanding garden, flower beds and exterior props are in Garden. Fence and gate are in Fence; paving is in Pathways. All meshes share the original ground-centre coordinate system.

## Placement completed after user approval

Read-only inspection of the current `/Game/TestLevel/Level_6/level_6_create_map` confirms:

| Plot | UE X bounds (cm) | UE Y bounds (cm) |
|---|---|---|
| PlayerHouse | -4200 to -2600 | 1400 to 2800 |
| Neighbor_2 | -4200 to -2600 | -1300 to 100 |
| Neighbor_4 | -4200 to -2600 | 4000 to 5400 |

The 3 m roads HomeAccess_107.5 (Y 600 to 900) and HomeAccess_133.5 (Y 3200 to 3500), plus their sidewalks, separate the player from both nearby plots. The second residential row is across Residential_4p5m. Thus no existing neighboring plot satisfies the documented shared-boundary requirement.

The user approved moving Mia next to the player and removing the separating northern road segment. Neighbor_4 was assigned to Mia and its plot centre moved from (-3400,4700,19) to (-3400,3500,19) cm. The 14 x 16 m plot now shares the boundary Y=2800 cm with PlayerHouse. BO_Neighbor_4 was replaced in place and renamed MiaHouse_Blockout. Final house/environment transform: Location (-3400,3500,24) cm, Yaw +90 degrees, Scale (1,1,1). Entry faces -X towards the residential sidewalk.

HomeAccess_133.5 was shortened to the centre of Residential_4p5m at X=-4600 cm. Remaining road bounds: X=-6900..-4600, Y=3200..3500 cm; remaining sidewalk: X=-7000..-4600, Y=3100..3600 cm. Southern endpoints and widths were retained. Other roads were not changed.

Removed only the old Neighbor_4 pathway and its five fence actors. The player's eight plot/house/path/fence actors retain their exact original transforms. Shared player fence BO_FenceSide_PlayerHouse1 remains intact. A placement-specific SM_MiaHouse_Fence_SharedBoundary omits only the source LeftBoundary_* objects to avoid a duplicate shared fence; the full original fence asset and editable blend remain unchanged. The gate is preserved in its original closed pose; interactive opening is not implemented by this transfer.

Placed house, garden, pathways and fence retain unit scale and fit inside the plot within 0.001 cm numerical tolerance. Their collision uses complex-as-simple to avoid a combined convex hull blocking the yard. All four material slots on the fence variant are assigned. Source and FBX for the variant: Source/export_shared_fence.py and Source/SM_MiaHouse_Fence_SharedBoundary.fbx. Placement data: Source/placement_report.txt.

Level_6 and changed meshes saved. No screenshots, renders or Review folder were created. Numeric bounds and unchanged-player checks passed; visual review is left to the user in the UE viewport, with the camera positioned to show both houses.
