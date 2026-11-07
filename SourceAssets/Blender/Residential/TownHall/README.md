# Town Hall — Blender to UE transfer

Historical model/import notes. The current level layout may differ. Preview images and old diagnostic reports were removed during cleanup; use the existing scripts for fresh checks. See `SourceAssets/Blender/README.md` for current source locations.

Independent compact two-storey administration building, created from scratch from the supplied multi-view reference. No geometry from Museum, Hospital, University or other buildings is used.

- Editable source: `Source/TownHall_Blockout.blend`.
- Reproducible build: `Source/Scripts/create_town_hall.py` (run in a fresh/background Blender process).
- Dimension/hierarchy report: `Source/validation.txt`.

Body: **16 m across the facade × 12 m deep**, two floors, **9.5 m roof ridge**. The 12 × 16 m working footprint is oriented with its longer edge along the street to match the reference. Porch, steps, eaves and entrance decoration extend beyond the body. Dimensions are provisional, not locked for town layout.

`BLD_TownHall` contains `TownHall_ROOT` at (0, 0, 0), scale (1, 1, 1), and separate Walls, Roof, Windows, Entrance, Columns_Trim, Signage, Flag and Props collections. All building parts are parented to the root. Front faces -Y. Lighting, cameras and the neutral ground are in `Presentation_NOT_EXPORT`.

Warm plaster and limestone, a dark hipped roof, a small two-column entrance porch, central heraldic gable, TOWN HALL lettering, narrow recessed windows, window boxes and civic flag establish the first-pass design. Side and back elevations are modeled, including a simple rear service entrance. The gate-and-river shield is a provisional town emblem.

## UE transfer — 2026-10-06

The existing design was saved and exported without rebuilding or joining the editable source. Source remains 865 meshes and one editable text object under `TownHall_ROOT`. No `.blend1` or archive copies were created. Cameras, lights and presentation ground are excluded from the FBX.

- FBX: `Source/SM_TownHall_Blockout.fbx`.
- Static Mesh: `/Game/Art/Models/Residential/TownHall/SM_TownHall_Blockout`.
- All 24 original `TH_*` materials are under this building's `Materials/`, with source base color, roughness and metallic values.
- Blender metres → UE centimetres, `-Y Forward`, `Z Up`, import scale 1; normals recalculated and two zero-area faces removed only from temporary export meshes. No animation.
- Full mesh dimensions including decorations: **17.28 × 15.70 × 9.615 m**; 181,308 triangles.
- Replaced the mesh in `BO_Administration` in `/Game/TestLevel/Level_6/level_6_create_map`.
- Location: **(5695, -7100, 24) cm**, yaw **90°**, scale **(1,1,1)**. Front faces west (-X), toward the street and original entry marker.
- World dimensions after rotation: **15.70 × 17.28 × 9.615 m**. XY bounds centered on the old blockout; ground min Z equals plot top at 24 cm.
- Every other actor's transform, mesh and material assignments were verified unchanged. The thin existing `BO_Entry_Administration` marker partly extends under the entrance steps; it was preserved. No neighboring building overlaps; the entire building, including flag, fits inside its plot.
