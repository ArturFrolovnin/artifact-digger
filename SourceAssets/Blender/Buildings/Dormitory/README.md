# Dormitory — editable building and first-floor interior

Roof underside repair: the existing main roof now has an 80 mm vertical shell
and the porch roof a 60 mm shell, with opaque undersides and edge faces. Original
upper surfaces and materials are preserved. New edge faces were fitted around
the existing ridge cap, fascia and frame geometry without coplanar overlaps.
Both roof meshes preserve source winding during export. Source and FBX checks
verify 324 underside samples and 324 upper-surface samples. The existing UE mesh
was updated in place; no other source mesh or material was changed.

Facade opacity repair: restored the missing foundation perimeter and 15 masonry
sections behind the front brick veneer, within the original building envelope.
An earlier entrance Boolean had removed this backing, leaving one-sided brick
quads exposed over empty space. Existing faces, bricks, windows and the entrance
opening were retained. The repaired plinth and front ground-floor wall now carry
`export_preserve_normals`, so the shared exporter retains their validated outward
winding instead of reversing clipped open surfaces. Source and reimported-FBX
backing, outward-facing foundation, facade and opening checks passed. The current
UE mesh was updated in place, preserving all 49 materials and collision settings.

Coplanar overlap cleanup: 2,847 overlapping face pairs were resolved across the
existing building. Hidden portions of 1,620 source faces were trimmed, including
the plaster beneath the four wooden room sills, window-frame joints, doorway
trim, panelling and furnishing details. No similarly facing planar overlaps
remain within the 0.22 mm audit tolerance. The remaining faces and UVs, material
slots, independent doors and overall dimensions were verified unchanged.
The editable blend and existing `SM_Dormitory_Blockout` were updated. All 49 UE
material assignments and collision settings are preserved. Passage, stair and
window-opening checks passed. No map file was saved or changed.

After the user's subsequent FBX reimport, UE materials were repaired in place.
All 49 slots on `SM_Dormitory_Blockout` now have assigned materials. The three
`DORM_INT_Entry_Window_*` materials include Thin Translucent glass. The twelve
`DORM_INT_PR_*` materials are instances of two shared UE parents, with source
linear colors, roughness, metallic and emission from `player_room_materials.json`.
Wood/fabric color grain is approximated in UE using UV noise; the subtle Blender
bump is not reproduced. These repairs change only material assets and slot
assignments, without reimporting geometry or modifying levels. The modelling
notes below describe the earlier Blender-only stages.

The player room is furnished in Blender only: bed and bedding, bedside cabinet,
desk and chair, wardrobe, bookcase, books, plants, rug, wood floor, lamps and
small personal belongings. Fixed geometry belongs to `DORM_INT_Interior`, with
eight `DORM_INT_PlayerRoom_*` edit groups. The hinged `DORM_INT_Door_Player`
is separate. Four existing room windows have clear glass and partially raised
wooden blinds. Eight Blender lights provide room lighting. Existing entrance
windows and unrelated meshes are preserved. No FBX or Unreal update.

The player-room shell is enclosed by a transverse plaster wall at y=-1.0 m,
from the existing doorway/landing wall to the outer left facade. Approximate
clear floor size is 6.42 x 7.60 m. The door opening remains functional.
The wall belongs to `DORM_INT_Interior`, vertex group
`DORM_INT_PlayerRoom_ClosingWall`. Blender only; no FBX or Unreal update.

Blender-only player-room preparation: the upper left landing passage now has
a 16 cm plaster partition and fixed wooden door lining, included in
`DORM_INT_Interior` (vertex group `DORM_INT_PlayerRoom_Partition`). Clear opening:
1.02 m wide and 2.10 m high above the landing. A separate door leaf and room
interior have now been added. These changes have not been exported or imported into Unreal.

Blender-only changes pending export: five entrance windows (two lower side
windows, two upper side windows and the central upper window) now have local
clear-glass material, 6 mm panes, inner sash, seals, splayed reveals and fitted
interior sills. Five opaque backing boxes were removed; other windows and their
shared materials are unchanged. Fixed trim remains in `DORM_INT_Interior`.
Eevee refraction and Material Preview are enabled for inspection. This window
refinement has NOT been exported to FBX or imported into Unreal.

Interior completed 2026-11-08 in the existing `Source/Dormitory_Blockout.blend`.
The 61 original exterior/entrance mesh objects are unchanged. The existing main
UE asset now includes the cream-plaster hall, wood panelling, tiled floors,
corridor, stairs, open atrium and upper landing. No rooms behind closed doors.

All fixed interior geometry is now one Blender object, `DORM_INT_Interior`, and
is included in the existing `SM_Dormitory_Blockout` asset. This includes furniture,
plants, rugs, lamp meshes and lettering. Source groups remain selectable through
vertex groups. Existing bevels and lettering were converted to mesh as part of
the requested modelling consolidation; the visible geometry/materials are preserved.
The obsolete four furnishing assets were removed through Unreal after checking
that they had no referencers.

Only doors remain in `Dormitory/Parts/`: `SM_Dormitory_Door_Left`,
`SM_Dormitory_Door_Right`, and `SM_Dormitory_InteriorDoor` (eight linked source instances).
Interior door closed transforms are stored in `Source/interior_layout.json`
in Blender metres and in the UE door asset metadata in centimetres. Conversion:
location `(100*x, -100*y, 100*z)`, yaw `-Blender Z rotation`. Door origin is on local +Z hinges.
The editable Blender lights are not UE light actors; no level assembly was performed.

Twelve shared interior materials supplement the existing exterior materials.
Fixed parts use complex-as-simple collision; movable doors use simple collision.
103 numerical passage/stair checks passed in Blender and on imported UE geometry.
Main mesh: 146,546 imported triangles, 34 material slots, original bounds preserved.
The FBX contains 146,710 triangles; the importer removed 164 microscopic interior
bevel/text triangles (total area below 0.0000007 m²). All retained triangles match
the exported geometry. The existing exterior meshes and all door objects are unchanged.
Stair tread overlap fixed: removed 14 hidden structural top faces coplanar with
the tile caps. All other interior faces, vertices, materials and UVs are unchanged.

`Source/Scripts/export_fbx.py` exports temporary evaluated copies of the saved
editable model, grouping parts by asset path and exporting one shared door template.
`add_first_floor_interior.py` records the one-time interior authoring operation;
do not rerun it or historical building generators against the completed model.
No levels, actors, Blueprints, screenshots, renders or Git commits were created/changed
by the interior operation. Diagnostic checks are in `Saved/BlenderToUE/`.

## Historical exterior and entry-door notes

Historical model/import notes. The current level layout may differ. Preview images and old diagnostic reports were removed during cleanup; use the existing scripts for fresh checks. See `SourceAssets/Blender/README.md` for current source locations.

Editable source: Source/Dormitory_Blockout.blend (59 fixed mesh assemblies and two entrance door leaves).
Export: Source/SM_Dormitory_Blockout.fbx (fixed building only, no door leaves/camera/light/root).
UE asset: /Game/Art/Models/Buildings/Dormitory/SM_Dormitory_Blockout.

Entrance doors prepared 2026-11-07: `Parts/SM_Dormitory_Door_Left` and
`Parts/SM_Dormitory_Door_Right`, each with four existing building materials.
Hinge pivots rotate about local +Z. Closed relative positions in UE centimetres:
left (-102.5, 907, 46.5), right (102.5, 907, 46.5), rotation (0,0,0), scale (1,1,1).
These positions are also stored in each door asset's metadata.
The fixed frame remains in the main mesh; the 205 cm wide aperture is clear.
The building uses complex-as-simple collision; door leaves have simple collision.
Use Source/Scripts/export_fbx.py for the building and parts FBXs. It exports temporary copies,
excludes leaves from the main FBX, and never saves or edits the source .blend.
No level placement, actor edits, Blueprints, or map saves were performed for this change.

Blender metres: body 26 x 18; full bounds 27.22 x 21.34923 x 14.24750.
Ground min Z = 0. Dormitory_ROOT = (0,0,0), centred on the body at ground level.
Rotation and Scale applied, object scales 1/1/1. Exterior surface normals corrected.
FBX export: -Y forward, Z up, FBX_SCALE_NONE, apply_unit_scale=True.
Units are baked for the importer; Blender source remains in metres.
Verified UE local bounds in centimetres:
min (-1361,-957.92297,0), max (1361,1177.00012,1424.75).

BO_Dormitory replaced in place in level_6_create_map:
location (5700,7400,24) cm; yaw 90 degrees; scale (1,1,1).
Ground aligns with the plot top at 24 cm; entry points towards -X.
UE import combines meshes into one Static Mesh, source blend remains separate.
Map and imported assets saved. No additional detail or interior added.
