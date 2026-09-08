# AI Context — Digging Feature

PURPOSE:  
This file is a persistent project-context checkpoint for AI coding assistants.  
Read this file before modifying the digging system.

## Snapshot

- Project: ArcheoDig / artifact-digger, Unreal Engine `5.8`.
- Documented HEAD: `48ae26f23da91e08a8de7ccffa577cbf118abd5d` (`add smooth dynamic mesh excavation`).
- Test feature root: `/Game/DiggingPrototype/DiggingFeature`.
- Current preferred path: `BP_DiggableGround_Smooth` using Dynamic Mesh + Geometry Script + Boolean Subtract.
- Status: working small-area prototype; not production- or large-world-proven.

Important asset-name collision:

- `/Game/DiggingPrototype/BP_DiggableGround` is a separate older voxel prototype used with `L_DiggingTest`.
- `/Game/DiggingPrototype/DiggingFeature/Blueprints/BP_DiggableGround` is the voxel reference inside the feature described here.
- Always use full asset paths when inspecting, reporting, or editing.

## Current goal

Создать качественную digging mechanic, визуально близкую к **A Game About Digging A Hole** / **Hydroneer**: плавно изменяемая геометрия грунта и соответствующая физическая collision.

Не строить сейчас весь мир. Текущий приоритет — один качественный, устойчивый и измеренный diggable ground.

## Current preferred implementation

Основная ветка:

```text
BP_DigPlayer.TryDigSmooth
→ camera-based Line Trace
→ ImpactPoint (World Space)
→ Cast To BP_DiggableGround_Smooth
→ BP_DiggableGround_Smooth.DigAtPoint
→ World-to-local conversion
→ rebuild sphere DigCutter
→ DigMesh minus DigCutter
→ Update Collision
```

`BP_DiggableGround_Smooth` является текущим направлением. Старый `BP_DiggableGround` voxel implementation сохранять как reference/prototype, пока smooth implementation не станет доказанно стабильной. Не удалять и не рефакторить voxel-эталон без явного запроса.

## Relevant assets

- `/Game/DiggingPrototype/DiggingFeature/L_DiggingFeature`
- `/Game/DiggingPrototype/DiggingFeature/newLevel_Digging`
- `/Game/DiggingPrototype/DiggingFeature/Blueprints/BP_DigPlayer`
- `/Game/DiggingPrototype/DiggingFeature/Blueprints/BP_DiggableGround`
- `/Game/DiggingPrototype/DiggingFeature/Blueprints/BP_DiggableGround_Smooth`
- `/Game/DiggingPrototype/DiggingFeature/Blueprints/BP_DigGameMode`
- `/Game/DiggingPrototype/DiggingFeature/Blueprints/BP_DigGameMode2`

Do not confuse these with `/Game/DiggingPrototype/L_DiggingTest` and `/Game/DiggingPrototype/BP_DiggableGround`.

## Current known Blueprint architecture

### `BP_DigPlayer`

- `TryDig` = voxel implementation/reference.
- `TryDigSmooth` = Dynamic Mesh implementation.
- Uses `FollowCamera` location and forward vector.
- Computes trace end and calls `Line Trace By Channel`.
- Reads `Hit Actor` and `ImpactPoint` from `Break Hit Result`.
- Uses `Cast To BP_DiggableGround_Smooth`.
- Calls `DigAtPoint(ImpactPoint)` on the correctly typed smooth-ground reference.
- Player determines the point of interaction; it does not edit the ground mesh.

### `BP_DiggableGround_Smooth`

Components:

- `DigMesh`: visible mutable ground geometry, collision enabled.
- `DigCutter`: temporary/invisible cutter geometry, `NoCollision`.

Construction:

```text
DigMesh
→ Get Dynamic Mesh
→ Append Box
```

Current box values:

- Size: `500 × 500 × 300` cm.
- Origin: `Center`.
- Transform Location: `(0, 0, -150)`.
- Result: top surface near local `Z = 0`.
- Collision: `Enable Complex as Simple Collision`.

`DigAtPoint(ImpactPoint: Vector)`:

```text
ImpactPoint (World Space)
+ DigMesh.GetWorldTransform
→ Inverse Transform Location
→ LocalImpactPoint

DigCutter.GetDynamicMesh
→ Reset
→ Append Sphere Lat Long
   Radius = 50
   Steps Phi = 16
   Steps Theta = 24
   Origin = Center
   Transform Location = LocalImpactPoint
   Rotation = 0
   Scale = 1

DigMesh.GetDynamicMesh
→ Apply Mesh Boolean
   Target Mesh = DigMesh
   Tool Mesh = DigCutter
   Operation = Subtract
→ Update Collision (DigMesh)
```

The exact wiring in the current Unreal Editor asset is authoritative. Binary `.uasset` files do not provide a useful textual Git diff.

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
3. Do not move mesh-editing, cutter, Boolean, or collision-update logic into `BP_DigPlayer`.
4. Do not delete the working voxel reference implementation without explicit request.
5. Do not build a chunk manager yet.
6. First make one smooth ground robust and benchmark it.
7. Do not return to tiny visible cube voxels as the main rendering solution unless measurements show Dynamic Mesh is unsuitable.
8. Prefer small, understandable Blueprint changes; the developer is learning UE Blueprint architecture during implementation.
9. Explain each new Blueprint node and its data flow before introducing a large graph.
10. Do not perform large automatic refactors without explicit request.
11. Keep interaction range (`DigReach`) conceptually separate from trace length.
12. Verify asset paths because duplicate short names exist.

## Known tested behavior

The current project checkpoint records these PIE results:

- voxel prototype works;
- multiple Blueprint instances had independent state;
- Dynamic Mesh box renders correctly;
- character collision required `Enable Complex as Simple Collision`;
- character can stand on the test Dynamic Mesh surface after enabling it;
- smooth Boolean subtraction works in PIE;
- repeated sphere cuts produce neighboring/connected rounded cavities;
- voxel-style visual stepping and cube flicker are absent in the smooth result;
- `Update Collision` is present in `DigAtPoint`;
- current smooth result appears stable on the small prototype.

Do not generalize these results to deep cavities, long sessions, large terrain, multiplayer, or production performance.

## Known abandoned or deferred work

- `BP_DigChunk` experiment was temporary and is removed/deferred.
- `BP_DigWorld` / chunk manager is deferred.
- Large-world implementation is not designed.
- Streaming/loading and unloading are not implemented.
- Persistence of excavated geometry is not implemented.
- Voxel approach is retained as reference, not as the preferred visual solution.
- Current Boolean implementation is not assumed production-performance ready.

## Next exact tasks

First task for the next implementation session:

> Validate physical collision inside and around several overlapping smooth Boolean cavities.

Then, in order:

1. Tune cutter radius, resolution, and shape.
2. Replace the ideal sphere with a shovel-like excavation imprint.
3. Add held input.
4. Add/configure `DigInterval`.
5. Add a separate `DigReach` independent of Line Trace length.
6. Benchmark `10`, `100`, and `500+` Boolean operations; record operation time and FPS.
7. Measure triangle-count growth across repeated Boolean operations.
8. If measurements require it, investigate remesh/simplification and bounded mesh complexity.
9. Only after this, design chunks.
10. After chunks, consider `DigWorld`, streaming, soil layers, and persistence.

## Current limitations

- Ideal spherical cutter only.
- Test cutter radius is `50` cm.
- No shovel-specific cut shape.
- No held-LMB loop / `DigInterval` in the smooth path.
- No finalized independent `DigReach`.
- No high-count Boolean benchmark.
- No triangle-growth measurements.
- No remesh/simplification strategy.
- Deep/complex cavity collision needs testing.
- No chunk manager.
- No save/load for changed geometry.
- No Dirt/Clay/Stone layers or hardness.
- No resources/ore rewards.
- No complete tool system.
- No dirt particles, decals, or sound.
- Test material only.
- No proven replication/multiplayer behavior.

## Pitfalls already encountered

- ISM cubes produced coarse, stepped digging.
- Smaller voxels increased total count dramatically in 3D.
- Adjacent cube rendering produced visible flicker/artifacts.
- Dynamic Mesh initially had no usable character collision until `Enable Complex as Simple Collision` was enabled.
- `ImpactPoint` from Line Trace is World Space; cutter construction uses ground-local coordinates. Convert via `DigMesh.GetWorldTransform` + `Inverse Transform Location`.
- `Apply Mesh Boolean` must use ground as `Target Mesh`, cutter as `Tool Mesh`, and `Subtract` as operation.
- `DigCutter` must be `Reset` before appending the next sphere.
- Collision must be updated after modifying `DigMesh`.
- Blueprint node target types matter. A `DigAtPoint` call created for `BP_DiggableGround` cannot accept `BP_DiggableGround_Smooth` as Target. Recreate the call from a correctly typed smooth-ground reference.
- Duplicate short asset names can lead inspection or edits to the wrong Blueprint.
- Do not infer Blueprint graph changes from LFS pointer diffs.

## Git checkpoints

- `dc5abe3fc8010f443ea89281b4cb91556de78f63` — `add manual voxel digging prototype`. First manually assembled voxel implementation in the feature-local Blueprints.
- `48ae26f23da91e08a8de7ccffa577cbf118abd5d` — `add smooth dynamic mesh excavation`. Added `BP_DiggableGround_Smooth` and updated player/level assets for Dynamic Mesh Boolean excavation.

At the time of this checkpoint, `48ae26f` is `HEAD` and there are no newer relevant commits.

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
