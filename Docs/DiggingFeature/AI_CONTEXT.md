# AI Context — Digging Feature

PURPOSE:  
This file is a persistent project-context checkpoint for AI coding assistants.  
Read this file before modifying the digging system.

## Snapshot

- Project: ArcheoDig / artifact-digger, Unreal Engine `5.8`.
- Git HEAD at this checkpoint: `6fa2aea0a1ff09dedb6e2cb6e60ad02d90087b88` (`add readme`).
- Test feature root: `/Game/DiggingPrototype/DiggingFeature`.
- Current preferred path: `BP_DiggableGround_Smooth` using Dynamic Mesh + Geometry Script + Boolean Subtract.
- Current player direction: `BP_DigPlayer_FirstPerson`, intentional full-body first person.
- Current visual-material experiment: Quixel Megascans Soil Ground `MI_xdhhdhl` on `DigMesh`.
- Status: working small-area prototype; not production- or large-world-proven.

Important asset-name collision:

- `/Game/DiggingPrototype/BP_DiggableGround` is a separate older voxel prototype used with `L_DiggingTest`.
- `/Game/DiggingPrototype/DiggingFeature/Blueprints/BP_DiggableGround` is the voxel reference inside the feature described here.
- Always use full asset paths when inspecting, reporting, or editing.

## Current goal

Довести один `BP_DiggableGround_Smooth` до визуально приятного и удобного для first-person digging состояния: плавно изменяемая геометрия, надёжная collision, читаемый soil material и управляемая форма cutter.

Не строить сейчас весь мир. Material, cutter feel и benchmark одного участка идут раньше chunk manager.

## Current preferred implementation

Основная ветка:

```text
BP_DigPlayer_FirstPerson.TryDigSmooth
→ camera-based Line Trace
→ ImpactPoint + ImpactNormal (World Space)
→ Cast To BP_DiggableGround_Smooth
→ BP_DiggableGround_Smooth.DigAtPoint(ImpactPoint, ImpactNormal)
→ World-to-local position and direction conversion
→ rebuild and orient scaled-sphere DigCutter
→ DigMesh minus DigCutter
→ Update Collision
```

`BP_DiggableGround_Smooth` является текущим направлением. Старый `BP_DiggableGround` voxel implementation сохранять как reference/prototype, пока smooth implementation не станет доказанно стабильной. Не удалять и не рефакторить voxel-эталон без явного запроса.

## Relevant assets

- `/Game/DiggingPrototype/DiggingFeature/L_DiggingFeature`
- `/Game/DiggingPrototype/DiggingFeature/newLevel_Digging`
- `/Game/DiggingPrototype/DiggingFeature/Blueprints/BP_DigPlayer`
- `/Game/DiggingPrototype/DiggingFeature/Blueprints/BP_DigPlayer_FirstPerson`
- `/Game/DiggingPrototype/DiggingFeature/Blueprints/BP_DiggableGround`
- `/Game/DiggingPrototype/DiggingFeature/Blueprints/BP_DiggableGround_Smooth`
- `/Game/DiggingPrototype/DiggingFeature/Blueprints/BP_DigGameMode`
- `/Game/DiggingPrototype/DiggingFeature/Blueprints/BP_DigGameMode2`
- `/Game/DiggingPrototype/DiggingFeature/Blueprints/WBP_DigCrosshair`
- `/Game/Characters/Mannequins/Meshes/SK_Mannequin` (Skeleton containing `FP_Camera`)
- `/Game/Characters/Mannequins/Meshes/SKM_Manny_Simple` (full-body mesh using that Skeleton)
- `/Game/Fab/Megascans/Surfaces/Soil_Ground_xdhhdhl/Medium/xdhhdhl_tier_2/Materials/MI_xdhhdhl`

Do not confuse these with `/Game/DiggingPrototype/L_DiggingTest` and `/Game/DiggingPrototype/BP_DiggableGround`.

## Current player architecture

### `BP_DigPlayer_FirstPerson`

- Current player direction; created separately so `BP_DigPlayer` third-person/reference is preserved.
- Full-body first person: body intentionally remains visible when looking down.
- Do not replace with floating FPS arms without explicit design decision.
- `BP_DigGameMode2.DefaultPawnClass = BP_DigPlayer_FirstPerson`.
- Retains `Move`, `Aim`, `TryDig`, `TryDigSmooth`, digging trace, movement/look/jump input.
- Current left mouse execution calls `TryDigSmooth`; `TryDig` node exists as voxel reference but is not connected to the click chain.
- Uses `FollowCamera` location and forward vector.
- Current trace distance in the graph is `550` cm; independent `DigReach` is not finalized.
- Reads `Hit Actor`, `ImpactPoint`, and `ImpactNormal` from `Break Hit Result`.
- Uses `Cast To BP_DiggableGround_Smooth`.
- Calls `DigAtPoint(ImpactPoint, ImpactNormal)` on the correctly typed smooth-ground reference.
- Player determines the point of interaction; it does not edit the ground mesh.
- Prototype debug remains in `TryDigSmooth`: trace drawing `ForDuration`, `HIT`/`MISS` `Print String`, and `Draw Debug Sphere`.

Camera / body setup:

- `FollowCamera` parent = `Mesh` (confirmed component hierarchy).
- Parent socket = `FP_Camera` (confirmed in asset data).
- `FP_Camera` belongs to Skeleton `/Game/Characters/Mannequins/Meshes/SK_Mannequin`.
- `FP_Camera` parent bone = `neck_02`.
- Socket local Location ≈ `(14.4002, 12.8814, 0.2201)`, Rotation `(0,0,0)`, Scale `(1,1,1)`.
- Camera relative Location/Rotation = `(0,0,0)`; relative Scale = `(1,1,1)`.
- `FollowCamera.Use Pawn Control Rotation = true`.
- `Use Controller Rotation Pitch = false`.
- `Use Controller Rotation Yaw = true`.
- `Use Controller Rotation Roll = false`.
- `CharacterMovement.Orient Rotation to Movement = false`.
- Horizontal controller yaw rotates the whole Character; vertical pitch remains camera-only.
- `CameraBoom` still exists as a leftover component attached to the capsule, but it is not the parent of `FollowCamera`.

Head experiment:

- `Hide Bone By Name(head)` fixed head intrusion into local camera but removed the head from the character shadow.
- Experiment was reverted: the node remains in `EventGraph` but has no execution connection and does not run.
- Head currently remains part of the visible mesh; socket positioning prevents obstruction.
- Do not enable head hiding as final solution without preserving full-body shadow.

Crosshair:

- `WBP_DigCrosshair` is spawned on `BeginPlay` and added to viewport.
- Widget tree: `CanvasPanel` → `TextBlock` containing `○`.
- Center anchors `(0.5,0.5)`, alignment `(0.5,0.5)`, slot `24×24`, font size `20`.
- It is an interaction ring prototype, not a weapon crosshair.

## Current ground architecture

### `BP_DiggableGround_Smooth`

Components:

- `DigMesh`: visible mutable ground geometry, collision enabled.
- `DigCutter`: temporary/invisible cutter geometry, `NoCollision`.

Construction:

```text
DigMesh
→ Get Dynamic Mesh
→ Append Box
→ Enable Complex as Simple Collision
→ Set Override Render Material(MI_xdhhdhl)
```

Current box values:

- Size: `500 × 500 × 300` cm.
- Origin: `Center`.
- Transform Location: `(0, 0, -150)`.
- Result: top surface near local `Z = 0`.
- Collision: `Enable Complex as Simple Collision`.

`DigAtPoint(ImpactPoint: Vector, ImpactNormal: Vector)`:

```text
ImpactPoint (World Space)
+ DigMesh.GetWorldTransform
→ Inverse Transform Location
→ LocalImpactPoint

ImpactNormal (World Space)
+ DigMesh.GetWorldTransform
→ Inverse Transform Direction
→ Make Rot from Z
→ cutter local Rotation

DigCutter.GetDynamicMesh
→ Reset
→ Append Sphere Lat Long
   Radius = DigRadius (default 25)
   Steps Phi = DigCutterPhi (default 16)
   Steps Theta = DigCutterTheta (default 24)
   Origin = Center
   Transform Location = LocalImpactPoint
   Rotation = Make Rot from Z(local ImpactNormal)
   Scale = DigCutterScale (default 1,1,0.35)

DigMesh.GetDynamicMesh
→ Apply Mesh Boolean
   Target Mesh = DigMesh
   Tool Mesh = DigCutter
   Operation = Subtract
→ Update Collision (DigMesh)
```

Editable cutter variables:

- `DigRadius: Float = 25`
- `DigCutterScale: Vector = (1,1,0.35)`
- `DigCutterPhi: Integer = 16`
- `DigCutterTheta: Integer = 24`
- Category for all: `Digging|Cutter`
- All are intended as `Instance Editable` for Details-panel iteration.

Exact-name warning from current asset inspection: internal member names `DigCutterScale `, `DigCutterPhi `, `DigCutterTheta ` and function input `ImpactNormal ` contain a trailing space. Human-facing docs omit it. Match the actual pin/member when automating inspection; do not silently create duplicates.

The exact wiring in the current Unreal Editor asset is authoritative. Binary `.uasset` files do not provide a useful textual Git diff.

## Current material state

- Fab UE Plugin is installed in local UE `5.8` at `Engine/Plugins/Fab`; inspected version `0.0.15`, enabled by default.
- Preferred import workflow: Fab website → save exact asset to My Library → Unreal Editor Fab panel → Add to Project.
- Imported asset: Quixel Megascans **Soil Ground**.
- Confirmed Fab import id in `AssetImportData`: `1e20f0ed-b2ce-46db-8aaa-54d10f56e975`.
- Current Material Instance: `/Game/Fab/Megascans/Surfaces/Soil_Ground_xdhhdhl/Medium/xdhhdhl_tier_2/Materials/MI_xdhhdhl`.
- Textures: `T_xdhhdhl_2K_B`, `T_xdhhdhl_2K_N`, `T_xdhhdhl_2K_ORM`.
- Parent: `/Game/Fab/Materials/Standard/M_MS_Srf`.
- Applied in `BP_DiggableGround_Smooth.UserConstructionScript` with `Set Override Render Material`, `Target = DigMesh`.
- `MI_xdhhdhl` renders on the Dynamic Mesh, but is not production-ready for deforming geometry.

Known issue:

- Standard UV mapping visibly stretches/distorts on Boolean-created surfaces.
- Cavities show radial/star-like patterns and bad texture projection on inner walls.
- Do not assume the imported Material Instance solves diggable-ground rendering.

Likely next direction:

- custom `M_DiggableSoil`;
- imported Soil Ground textures as source data;
- `WorldAlignedTexture` / triplanar projection for Base Color and scalar maps;
- `WorldAlignedNormal` for Normal;
- parameterized world-space texture scale.

`M_DiggableSoil` does not exist yet. Do not delete Fab/Megascans shared Materials, Material Functions, Material Parameter Collections, or textures: the current instance references its master material and textures, and dependency cleanup must wait until a verified independent replacement exists.

## Voxel reference architecture

Feature-local `BP_DiggableGround` used one `Instanced Static Mesh` containing many cube instances.

Construction:

```text
Clear Instances
→ nested For Loop X/Y/Z
→ calculate voxel transform
→ Add Instance
```

Dig flow:

```text
BP_DigPlayer.TryDig
→ camera Line Trace
→ ImpactPoint
→ BP_DiggableGround.DigAtPoint
→ Get Instances Overlapping Sphere
→ Remove Instances
```

Voxel sizes around `50`, `25`, and `20` cm were explored. Smaller voxels reduce step size but increase instance count sharply and do not create a truly continuous surface.

## Important design decisions

Treat these as project rules unless the user explicitly changes them:

1. Player determines **WHERE** to dig.
2. Ground determines **HOW** digging modifies itself.
3. Keep mesh editing, cutter construction, Boolean, and collision update inside `BP_DiggableGround_Smooth`.
4. Do not delete the working voxel reference implementation without explicit request.
5. `BP_DigPlayer_FirstPerson` is the current player direction; old `BP_DigPlayer` remains reference.
6. Full-body first person is intentional because future inventory may physically exist on the body.
7. Do not switch to floating FPS arms without explicit request.
8. Do not hide the head bone as a final solution unless full-body shadow remains correct.
9. Keep cutter parameters exposed for fast visual iteration.
10. Do not build a chunk manager yet; first make one ground visually good, robust, and benchmarked.
11. Do not assume standard UV materials work on Boolean Dynamic Mesh; investigate World Aligned / Triplanar soil.
12. Do not delete Fab/Megascans shared dependencies until a replacement is verified independent.
13. Do not return to tiny visible cube voxels as the main rendering solution unless measurements show Dynamic Mesh is unsuitable.
14. Keep interaction range (`DigReach`) conceptually separate from trace length.
15. Prefer small, understandable Blueprint changes; explain each new node and data flow before large graphs.
16. Do not perform large automatic refactors without explicit request.
17. Verify full asset paths because duplicate short names exist.
18. Suggest a Git checkpoint after meaningful verified milestones.

## Known tested behavior

The current project checkpoint records these PIE results:

- voxel prototype works;
- multiple Blueprint instances had independent state;
- Dynamic Mesh box renders correctly;
- character collision required `Enable Complex as Simple Collision`;
- character can stand on the test Dynamic Mesh surface after enabling it;
- smooth Boolean subtraction works in PIE;
- repeated sphere cuts produce neighboring/connected rounded cavities;
- collision around many overlapping Boolean cavities was validated;
- player can physically enter cavities, stand on inner surfaces, and move among overlapping cuts;
- voxel-style visual stepping and cube flicker are absent in the smooth result;
- `Update Collision` is present in `DigAtPoint`;
- current smooth result appears stable on the small prototype;
- full-body first-person camera works;
- body follows controller yaw and stays visible when looking down;
- centered `WBP_DigCrosshair` interaction ring appears in PIE and matches camera trace direction;
- Quixel Soil Ground renders on `DigMesh`;
- Boolean-created surfaces expose the known UV stretching problem.

Do not generalize these results to measured `100`/`500+` Boolean stress tests, long sessions, large terrain, multiplayer, or production performance.

## Known abandoned or deferred work

- `BP_DigChunk` experiment was temporary and is removed/deferred.
- `BP_DigWorld` / chunk manager is deferred.
- Large-world implementation is not designed.
- Streaming/loading and unloading are not implemented.
- Persistence of excavated geometry is not implemented.
- Voxel approach is retained as reference, not as the preferred visual solution.
- Current Boolean implementation is not assumed production-performance ready.
- Custom `M_DiggableSoil` with World Aligned / Triplanar projection is planned but not created.
- Dedicated shadow-safe local head-hiding representation is deferred and is not the next priority.

## Next exact tasks

Collision validation around overlapping cavities is complete. Next session order:

1. Build custom `M_DiggableSoil` from imported Soil Ground textures using World Aligned / Triplanar projection.
2. Verify texture density, Base Color, Normal, Roughness/AO on flat top, vertical side, and several Boolean cavities.
3. Once surfaces are readable, tune `DigRadius` and `DigCutterScale` using exposed Details parameters.
4. Add independent `DigDepth` / cutter offset into ground along `ImpactNormal`.
5. Design a less spherical, shovel-like cutter shape.
6. Evaluate several neighboring cuts for natural-looking excavation.
7. Replace prototype Text `○` ring later if needed.
8. Add held digging and `DigInterval`.
9. Finalize `DigReach` separately from trace length.
10. Benchmark `10`, `100`, and `500+` Boolean operations; record operation time and FPS.
11. Measure triangle growth and `Update Collision` cost.
12. Investigate remesh/simplification only if measurements justify it.
13. Only after one smooth ground is robust and benchmarked, return to chunks / `DigWorld` manager.

## Current limitations

- Cutter is still a scaled sphere / ellipsoid (`25`, scale `1,1,0.35`).
- Excavation still looks like rounded bites.
- No shovel-specific cut shape.
- No independent `DigDepth` / normal offset.
- Standard UV Megascans material distorts on Boolean-generated surfaces.
- World Aligned / Triplanar `M_DiggableSoil` is not implemented.
- `WBP_DigCrosshair` is still prototype Text `○`.
- Full-body FPS remains a prototype.
- No held-LMB loop / `DigInterval` in the smooth path.
- No finalized independent `DigReach`.
- No high-count Boolean benchmark.
- No triangle-growth measurements.
- No measured `Update Collision` cost.
- No remesh/simplification strategy.
- No chunk manager.
- No save/load for changed geometry.
- No Dirt/Clay/Stone layers or hardness.
- No resources/ore rewards.
- No complete tool system.
- No dirt particles, decals, or sound.
- Imported soil material is a test, not final diggable-ground shading.
- No proven replication/multiplayer behavior.

## Pitfalls already encountered

- ISM cubes produced coarse, stepped digging.
- Smaller voxels increased total count dramatically in 3D.
- Adjacent cube rendering produced visible flicker/artifacts.
- Dynamic Mesh initially had no usable character collision until `Enable Complex as Simple Collision` was enabled.
- `ImpactPoint` from Line Trace is World Space; cutter construction uses ground-local coordinates. Convert via `DigMesh.GetWorldTransform` + `Inverse Transform Location`.
- `ImpactNormal` is also World Space. Convert with `Inverse Transform Direction`, then use `Make Rot from Z` for cutter orientation.
- `Apply Mesh Boolean` must use ground as `Target Mesh`, cutter as `Tool Mesh`, and `Subtract` as operation.
- `DigCutter` must be `Reset` before appending the next sphere.
- Collision must be updated after modifying `DigMesh`.
- Blueprint node target types matter. A `DigAtPoint` call created for `BP_DiggableGround` cannot accept `BP_DiggableGround_Smooth` as Target. Recreate the call from a correctly typed smooth-ground reference.
- Duplicate short asset names can lead inspection or edits to the wrong Blueprint.
- A full-body camera without controller yaw allowed the camera to look back into the Character's neck. Current fix: `Use Controller Rotation Yaw=true`, `Orient Rotation to Movement=false`.
- `Hide Bone By Name(head)` removed local head obstruction but also removed the head shadow; it was disconnected/reverted.
- Direct standard-UV Megascans material is insufficient for Boolean-generated surfaces.
- `MI_xdhhdhl` depends on `M_MS_Srf` and imported textures; do not delete Fab dependencies blindly.
- Internal names `DigCutterScale `, `DigCutterPhi `, `DigCutterTheta `, `ImpactNormal ` currently include trailing whitespace.
- `CameraBoom` remains in `BP_DigPlayer_FirstPerson`, but `FollowCamera` is parented directly to `Mesh`.
- Do not infer Blueprint graph changes from LFS pointer diffs.

## Git checkpoints

Implementation milestones:

- `dc5abe3fc8010f443ea89281b4cb91556de78f63` — `add manual voxel digging prototype`. First manually assembled voxel implementation in feature-local Blueprints.
- `48ae26f23da91e08a8de7ccffa577cbf118abd5d` — `add smooth dynamic mesh excavation`. Added `BP_DiggableGround_Smooth` and Dynamic Mesh Boolean excavation.

Documentation milestone:

- `6fa2aea0a1ff09dedb6e2cb6e60ad02d90087b88` — `add readme`. Previous documentation checkpoint and Git `HEAD` when this update was prepared.

Full-body FPS, surface-aware cutter, crosshair, collision validation, and Fab/Soil Ground work are newer than the implementation milestone above. Inspect current Git history and assets before assigning a new implementation SHA.

## How future AI should work

Before changing the digging feature:

1. Read this file and `Docs/DiggingFeature/README.md`.
2. Inspect `git status`; preserve unrelated user changes.
3. Inspect the latest relevant commits and do not assume this checkpoint is newest.
4. If Unreal MCP is available, use it to inspect the exact Blueprint graphs and level state.
5. Treat the actual Unreal assets/current Editor state as authoritative when they disagree with this file.
6. State the intended small change before editing.
7. Prefer one focused feature or experiment at a time.
8. Preserve working checkpoints, especially the voxel reference.
9. Explain new nodes and coordinate spaces clearly.
10. Compile and validate the affected Blueprint in Unreal.
11. Test in PIE in proportion to the change, including collision when geometry changes.
12. Record parameter values and measured results; do not label behavior “tested” without evidence.
13. Suggest a Git commit after a meaningful verified milestone.

Unreal `.uasset` and `.umap` files are binary and tracked through Git LFS. Normal Git diff commonly exposes only pointer/hash changes, not Blueprint node wiring. Prefer Unreal MCP or direct inspection in the current Unreal Editor for exact graph structure.
