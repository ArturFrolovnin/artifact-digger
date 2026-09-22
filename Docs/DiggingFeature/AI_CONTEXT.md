# AI Context — ArcheoDig digging feature

Purpose: compact, persistent context for assistants continuing the digging work. Read [`../DiggingArchitecture.md`](../DiggingArchitecture.md) for the authoritative current decisions. The completed terrain architecture research is in [`../Research/DiggingTerrainArchitecture.md`](../Research/DiggingTerrainArchitecture.md).

## Snapshot

- Architecture research completed: `2026-09-12`.
- Current verified HEAD: `a1bc1a1` (`I added training scripts in C++.`), 2026-09-22.
- Project: ArcheoDig / artifact-digger, Unreal Engine `5.8`.
- Current direction: one bounded volumetric/density Dig Site architecture for all five biomes, varied through Soil Types, material data and behavior modules.
- Dynamic Mesh is a frozen interaction/visual reference, not the production terrain direction.
- Current prototype: **Voxel Surface Dig** in `/Game/DiggingPrototype/Voxel/Voxel_2/L_VoxelDig2`.
- Installed experiment dependency: Voxel Plugin Free Legacy in `Plugins/VoxelFree`.
- VoxelFree is a prototype backend only until benchmarks pass; do not treat it as the production dependency.
- Latest project checkpoint: [`Checkpoints/2026-09-22_CPPWorkflowAndDiggingMigration.md`](Checkpoints/2026-09-22_CPPWorkflowAndDiggingMigration.md). Earlier material/lighting state: [`Checkpoints/2026-09-14_VoxelGroundMaterialLighting.md`](Checkpoints/2026-09-14_VoxelGroundMaterialLighting.md); brush state: [`Checkpoints/2026-09-12_VoxelSurfacePrototype.md`](Checkpoints/2026-09-12_VoxelSurfacePrototype.md).
- On 2026-09-14 the material was saved, but the loaded level was dirty. Current Editor world settings: voxel size `5 cm`, world size `256`; these are experimental values, not revised production or benchmark targets.
- The original `/Game/DiggingPrototype/Voxel/L_VoxelDigTest` and `BP_VoxelDigPlayer` are preserved as the earlier VoxelFree baseline.
- In the current `Voxel_2` branch, LMB calls `TryVoxelSurfaceDig2`; `RemoveSphere` and `TrimSphere` remain reference experiments.
- Runtime C++ module `ArcheoDig` now exists. `MyActorComponent` is learning-only; `DiggingComponent.ProcessDigging()` is Blueprint-callable but currently only displays a test message. Real digging logic has not been migrated.
- Commit `c00dd30` contains the material hotfix. Session-observed result: orientation uses `VertexNormalWS`, Base Color and Normal use the same Grass/Dirt mask, material compiles and wall transition is cleaner. The older 2026-09-14 wiring remains historical.

## Do not confuse these assets

- `/Game/DiggingPrototype/BP_DiggableGround` — older standalone voxel/ISM prototype.
- `/Game/DiggingPrototype/DiggingFeature/Blueprints/BP_DiggableGround` — feature-local ISM reference.
- `/Game/DiggingPrototype/DiggingFeature/Blueprints/BP_DiggableGround_Smooth` — Geometry Script / Dynamic Mesh checkpoint.

Always use full asset paths.

## Verified Dynamic Mesh flow

```text
BP_DigPlayer_FirstPerson.TryDigSmooth
→ camera Line Trace, end = camera position + forward * DigReachCm
→ ImpactPoint + ImpactNormal
→ BP_DiggableGround_Smooth.DigAtPoint
→ world-to-local point and direction
→ oriented scaled-sphere cutter
→ Apply Mesh Boolean (Subtract)
→ Remove Small Connected Islands
→ Update Collision
```

Ground construction:

- Dynamic Mesh box: `500 × 500 × 300 cm`, local center `Z = -150`;
- complex-as-simple collision enabled;
- render material: `/Game/DiggingPrototype/DiggingFeature/Materials/M_DiggableSoil`.

Verified cutter defaults:

- `CutterBaseRadiusCm = 25`
- `CutterShapeScale = (1, 1, 0.35)`
- `CutterPhiSegments = 16`
- `CutterThetaSegments = 24`
- `CutterInsetCm = 5`

Verified cleanup defaults:

- `Min Volume = 0`
- `Min Area = 0`
- `Min Triangle Count = 20`

Verified player value:

- `DigReachCm = 500` as the persisted class default, category `Digging|Interaction`.
- Approximately `180 cm` was a transient prototype test value, not the current saved default.

Prototype debug remains in `TryDigSmooth`: drawn trace, `HIT` / `MISS` print strings and impact debug sphere.

## Material checkpoint

`M_DiggableSoil` uses world-aligned projection:

- `T_xdhhdhl_2K_B` → Base Color;
- `T_xdhhdhl_2K_N` → Normal;
- green channel of `T_xdhhdhl_2K_ORM` → Roughness;
- red channel of `T_xdhhdhl_2K_ORM` → Ambient Occlusion;
- Metallic disconnected;
- hard-coded world texture size `(200, 200, 200)`.

Do not revert to the heavy Fab material instance merely to fix UVs. Parameterize the world-aligned material later if it remains relevant.

## First-person layer to preserve

- `BP_DigPlayer_FirstPerson` is intentional full-body first person.
- Camera attaches to skeleton socket `FP_Camera`, parent bone `neck_02`.
- Body follows controller yaw; camera handles vertical pitch.
- Body remains visible when looking down.
- Do not hide the head without accounting for the broken/missing shadow observed in the previous experiment.
- `WBP_DigCrosshair` provides the center interaction ring.
- Player owns trace/range/UI; terrain backend owns edit and collision.

This layer should feed either Dynamic Mesh or voxel terrain through impact data.

## Known Dynamic Mesh limitations

Repeated sequential Booleans create spikes, thin connected flaps, obstructive micro-surfaces, hanging pieces and degraded topology. `Remove Small Connected Islands` cannot remove defects that are still connected to the main mesh.

Rejected and removed from the active graph:

1. Global Uniform Remesh after each dig: target edge `4 cm`, reproject on, smoothing `0`, flips/splits/collapses on, normal/tiny-triangle prevention on, `5` iterations. Observed hitch approximately `3 s` per edit.
2. Local iterative smoothing in an approximately `35 cm` sphere: `2` iterations, alpha `0.15`. Observed hitch approximately `0.5 s`, with stretched triangles and needles. It moves vertices but does not fix topology.

Do not restore either chain without a new, explicit experiment and performance budget.

## Current architecture decision

```text
Gameplay
→ Dig/Terrain abstraction
→ concrete terrain backend
```

**Do not connect player/gameplay code directly to VoxelFree-specific APIs when an abstraction can contain the dependency.** Build a project-owned request/result or terrain interface boundary first. A concrete backend may be VoxelFree now and custom density later without rewriting gameplay.

Terrain model:

```text
Conventional Unreal world
└── bounded Dig Site
    ├── density + chunks
    ├── Soil Types / material data
    ├── behavior modules
    ├── Artifact Registry + separate Artifact Actors
    └── local render/collision/persistence
```

Plan A: Voxel Plugin Free Legacy experiment.

Production fallback: custom bounded chunked density field, initially meshed with Marching Cubes.

Research recommendations / prototype targets, not final production constants:

- benchmark Dig Site: `5 × 5 × 3 m` at `10 cm` resolution;
- compare `15 cm` as a performance alternative;
- do not use `20–25 cm` as the primary quality target without a separate test;
- first custom-backend chunk candidate: `16³` cells.

Use one bulk terrain architecture for all five biomes. Implement sand/frozen/rock differences through behavior modules. After cohesive soil, test sand relaxation first. Store artifacts as separate Unreal Actors / Registry, not in the voxel material field.

## C++ migration and immediate next stage

Strategy: heavy terrain/gameplay logic in C++; Blueprint for orchestration, events/input, VFX/SFX/animation, assets/config and coarse calls. Avoid repeated Blueprint ↔ C++ crossings inside heavy loops. One Blueprint call to a substantial `ProcessDigging()` operation per frame is not the primary performance concern.

Immediate proof:

```text
/Game/DiggingPrototype/BP_DiggableGround
Event Tick
→ Process Digging [C++]
```

Add/verify the `DiggingComponent` instance and confirm the test node call. Then migrate only the first camera/trace block: Player Camera Manager, location, rotation, forward vector, Line Trace By Channel. Do not move the entire graph at once.

Later migrate range/hit validation, interval and terrain operation; compare Blueprint Tick with C++ scheduling. Prefer timer/event-driven processing once behavior is understood. After the bridge, the main gameplay priority is shared terrain-fragment cleanup. Then compare additional digging methods behind a common C++ abstraction before selecting benchmark candidates.

Material/lighting is now a sufficient gameplay/backend test baseline. Keep `DirtTint #C2A189`, `DirtTextureSize ≈ 180`, world-aligned Grass/Dirt, Dirt Normal and current lighting as working prototype state. Dirt Roughness and further art polish are deferred.

## Unreal teaching workflow — project standard

The user learns Unreal Engine and C++ through this project. Previous experience: C#/Unity; current primary experience: JS/Vue; little prior C++. Apply these rules during hands-on work; autonomous documentation/read-only checks do not require staged confirmation.

1. Work in small iterations: usually **2–4 concrete actions**, with no more than about 3 new Blueprint nodes. Do not deliver a huge graph or hundreds of lines at once.
2. Use real Unreal node names. Do not invent names such as “Dirt WorldAlignedTexture”. Identify repeated nodes by position, connected texture or neighbours: “верхняя нода WorldAlignedTexture, в которую подключён коричневый Texture Object”.
3. Describe connections literally: “Найди ноду WorldAlignedTexture, в которую подключён коричневый Texture Object. Возьми выходной пин XYZ Texture. Подключи его во входной пин A ноды Multiply.” Avoid ambiguous shorthand in teaching instructions.
4. Before an action, explain what the Actor/node/parameter is, what it controls and why it is needed now. For Directional Light, explain sunlight, Pitch/height/shadow length and Yaw/direction before giving values.
5. Explain the direction of change: smaller TextureSize repeats more often; larger TextureSize enlarges the pattern; higher Exposure Compensation brightens the camera; higher SkyLight Intensity lifts shadows but can flatten the scene.
6. Always provide starting numerical values before artistic adjustment. Do not only say “turn it until it looks good”. Use a verified preset or clearly label a proposed starting value.
7. Use simple ASCII diagrams when spatial or mathematical relationships need explanation.
8. After each small hands-on stage, stop and ask for a screenshot, result or confirmation; continue after checking it. This prevents version/UI differences from invalidating a long instruction chain.
9. If actual node pins or Details parameters are unknown, ask for a screenshot of that node/panel; never invent available controls.
10. Preserve future corrections to this teaching style in project documentation. When the user says the format is ideal, treat it as the continuing project standard.
11. For a small C++ class, prefer a complete short `.h`/`.cpp` example over disconnected fragments. Explain new C++ constructs as they appear. Russian comments are welcome in learning code for orientation.
12. The user prefers text code to very large Blueprint graphs. Default heavy logic to C++; use Blueprint for orchestration/content/config.

## VoxelFree risks and Git hygiene

- A saved crash records `Cast of nullptr to VoxelDataAsset failed` in `FVoxelDataAssetEditorToolkit::InitVoxelEditor()` at `VoxelDataAssetEditorToolkit.cpp:123`.
- Treat this as an editor stability risk, not proof that runtime edits fail.
- Main Git stores `Plugins/VoxelFree` as gitlink `7e64a89ce827b44a75c83a939e2c2e2e42bee61d`.
- `.gitmodules` is absent, so a fresh clone cannot currently restore it as a normal submodule.
- Nested remote: `https://github.com/VoxelPlugin/VoxelPluginFreeLegacy.git`.
- Do not automatically convert, delete or vendor the plugin.
- Later choose one explicit policy: proper submodule, ignored external dependency with setup instructions, or vendored files subject to license.
- Keep `Plugins/Marketplace/VoxelPluginInstaller` until the experiment is finished.

## Guardrails

- Preserve the Dynamic Mesh prototype and early voxel references unless explicitly asked to remove them.
- Keep failed-experiment results in documentation even though their nodes were removed.
- Distinguish verified asset state from prototype observations and research hypotheses.
- Do not infer the live Voxel prototype state from the research document; inspect current Unreal assets and the latest checkpoint first.
- Never bypass `Gameplay → Dig/Terrain abstraction → concrete terrain backend` by coupling player/gameplay code directly to VoxelFree when the dependency can be isolated.
- After any Unreal edit, compile/save the touched asset and report exact paths and remaining warnings.
- Do not describe `BP_DiggableGround` as migrated to C++; verify each bridge and transferred block first.
- Terrain fragment cleanup is the main gameplay priority after the basic C++ bridge. Material polish is deferred.
