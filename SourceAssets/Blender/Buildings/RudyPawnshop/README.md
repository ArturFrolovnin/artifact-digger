# Uncle Rudy's pawnshop

Historical model/import notes. The current level layout may differ. Preview images and old diagnostic reports were removed during cleanup; use the existing scripts for fresh checks. See `SourceAssets/Blender/README.md` for current source locations.

Approved exterior preserved from the open Blender scene on 2026-10-05.

- Editable source: `Source/RudyPawnshop.blend` (51 mesh assemblies, 4 editable text objects).
- Export: `Source/SM_RudyPawnshop.fbx` (55 mesh objects, lettering converted on temporary copies).
- Unreal mesh: `/Game/Art/Models/Buildings/RudyPawnshop/SM_RudyPawnshop`.
- 28 materials in `Materials/`; 16,875 imported triangles.
- Body footprint: 10 x 8 m; complete bounds: 12.66855 x 10.06 x 9.85 m.
- Level: `/Game/TestLevel/Level_6/level_6_create_map`; existing actor `BO_Pawnshop` replaced in place.
- Placement: (1600, 3500, 24) cm, yaw 90 degrees, scale (1, 1, 1). Entrance faces -X.
- FBX: -Y forward, Z up, unit scale baked from metres to centimetres.
- UV0 uses face projection to provide non-degenerate tangent coordinates; material colours and geometry are unchanged.

`Source/export_fbx.py` runs in the open Blender scene and preserves editable lettering.
`Source/finish_ue_import.py` runs inside Unreal Editor Python to update the existing mesh and restore its material assignments.
`Source/Scripts/build_rudy.py` is the original construction script; do not rerun over the existing building.

## Ground-floor interior — 2026-11-12

The existing source now contains a fitted pawnshop interior. The exterior footprint,
roof and exterior material names are retained. The entrance leaf is separate and
shown open in Blender. The former solid ground-floor mass is hollowed using editable
Boolean cutters; window/entrance openings and a new staircase are included.
Only a stairwell and closed apartment entrance were added upstairs, not living rooms.

Interior: planked floor, burgundy runner, timber ceiling beams, three pendants,
counter with glass display, register, ledger, task lamp, standalone glass cabinet,
four stocked shelving units, cameras, radios, books, boxes, watches, rings, coins,
safe, card drawers, stool, notices, plants and RUDY'S PAWN lettering.
The player route and stair headroom were checked numerically; no screenshots or
renders were generated. Main mesh: 74,465 triangles; entrance door: 380 triangles.
All three storefront openings extend through the full wall thickness; nine ray
checks confirm that only the transparent panes remain across the window apertures.

### Prepared files and manual UE import

- `Source/RudyPawnshop.blend`: authoritative editable model.
- `Source/SM_RudyPawnshop.fbx`: building and interior, **without the movable door**.
  Reimport `/Game/Art/Models/Buildings/RudyPawnshop/SM_RudyPawnshop` in place.
- `Source/SM_RudyPawnshop_Door_Entrance.fbx`: closed door in hinge-local coordinates.
  Import as `/Game/Art/Models/Buildings/RudyPawnshop/Parts/SM_RudyPawnshop_Door_Entrance`.
  Combine its mesh and lettering; reuse the existing four exterior materials.
- `Source/model_config.json`: paths and door pivot. Door placement relative to the
  building in UE centimetres: **(66.5, 409, 36.5)**, closed yaw **0**, scale **1**.
  Rotate the door around its local Z axis. No actor or Blueprint has been created.
- `Source/interior_materials.json`: six interior materials, now created and assigned
  in the existing UE `Materials/` folder. All 28 original assignments are preserved.

For `RUDY_INT_Clear_Glass` in Unreal, use **Translucent**, **Surface ForwardShading**,
opacity **0.12**, roughness **0.12**, metallic **0**, two-sided **true**, and no
distorting refraction (IOR **1.0**). FBX alone does not reproduce a complete Unreal
translucent shader. Glass has a separate slot on storefront panes and both displays.
`RUDY_INT_Amber_Light` uses its amber colour multiplied by emission strength **5**.
Lamp geometry/emissive material is included; level light actors are not included.

The static building uses **Use Complex Collision As Simple**. Its two automatic
enclosing hulls were removed from the existing UE mesh on 2026-11-12 because they
blocked entry. Give the movable door its own simple collision. The fix was saved
only to `SM_RudyPawnshop`; the 34 material assignments and actor transform were
preserved. UE line traces confirm a clear entrance and hall, with blocking floor
and walls. No PIE character movement test was performed.

`Source/export_fbx.py` exports both FBXs from temporary copies, preserves editable
text/modifiers, excludes construction cutters and restores selection. The door is
not duplicated in the main FBX. `Source/model_interior.py` records the one-time
construction edit and intentionally refuses to run over an existing interior.
`Source/finish_ue_import.py` now reads `model_config.json` by default and uses the
existing configured import workflow for both building and separate door. Run it
inside Unreal Editor Python after exporting. It disables automatic hull creation,
reuses existing materials, creates missing interior materials from the manifest,
restores the building's complex collision and refreshes physics. Only automatically
generated simple hulls may be removed; authored collision causes the import to
stop for review. Door collision remains independent. Diagnostics go to
`Saved/BlenderToUE/rudypawnshop_import.json`.

The user imported the building FBX. The follow-ups repaired collision and replaced
the six WorldGridMaterial fallback slots with compiled interior materials. The
entrance door is now imported at its exact `Parts/SM_RudyPawnshop_Door_Entrance`
path, with the four existing exterior materials and one simple convex collision.
Its hinge-local bounds are X 0..143, Y -9..32.5, Z 0..229 cm (380 triangles).
The glass material is two-sided Translucent with SurfacePerPixelLighting and opacity
0.12. No mesh slots remain assigned to WorldGridMaterial. The updated full importer
has not been executed against the live assets here; the asset repairs used MCP.
No levels, actors or Blueprints were edited or saved.
