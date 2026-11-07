# Car dealership + workshop

Historical model/import notes. The current level layout may differ. Preview images and old diagnostic reports were removed during cleanup; use the existing scripts for fresh checks. See `SourceAssets/Blender/README.md` for current source locations.

Status: current Blender model transferred to UE5 and placed on Level_6, awaiting user review. Design unchanged during transfer.

- FBX: `Source/SM_CarDealership_Blockout.fbx`.
- Static Mesh: `/Game/Art/Models/Buildings/CarDealership/SM_CarDealership_Blockout`.
- Eleven dedicated materials under `Materials/`, prefixed `CAR_`; showroom glass is translucent.
- Replaced only `BO_CarDealer` in `level_6_create_map`; its plot is `BO_Plot_CarDealer`.
- Location: `(-3085.50, -7410.25, 24.00)` cm; yaw `0`; scale `(1,1,1)`.
- Measured UE dimensions: `1835.00 x 2600.50 x 730.00` cm; import scale `1`.
- Front faces world `+Y` toward the main street; garage doors face the open space at `+X`.
- Ground min Z equals plot top: `24` cm. Entire bounds fit on plot; no overlap with neighboring actors. Sky sphere excluded from bounds-overlap testing.
- Bounds center uses the original blockout center with a `17.50` cm shift toward `+X` to keep the existing west entry marker clear. All other actor transforms, mesh assignments and materials were verified unchanged.
- Export uses metres, `-Y` forward / `Z` up, `FBX_SCALE_NONE`, unit conversion enabled. Only temporary evaluated copies are cleaned and exported; 216 degenerate faces were removed, zero remain. Source architecture stays editable; no backup blend files were created.

- Editable source: `Source/CarDealership_Blockout.blend`.
- Body footprint: **18 x 24 m**, one tall showroom storey; maximum height **7.30 m**.
- Envelope including coping, handles and canopies: approximately **18.35 x 26.01 m**.
- Front: **-Y**. Showroom occupies the front 11 m; workshop occupies the rear 13 m.
- Two service openings face **+X**, each approximately **4.2 x 3.9 m**.
- `BLD_CarDealership` contains `CarDealership_ROOT` at `(0,0,0)` with nine named groups. All architecture is parented below the root; scales are 1 and ground minimum Z is 0.
- `Presentation_NOT_EXPORT` contains the preview ground, camera and lights, outside the building hierarchy.
- Separate editable panels, glass, doors, signs, flat roofs, one HVAC unit, a small technical room and two intentionally simple vehicle placeholders. No production UV, collision or LOD work.
- `Source/validation.txt` records measured bounds and hierarchy checks.
