# AI Context — ArcheoDig digging feature

Purpose: compact, persistent context for assistants continuing the digging work. Read [`../DiggingArchitecture.md`](../DiggingArchitecture.md) for the authoritative current decisions. The completed terrain architecture research is in [`../Research/DiggingTerrainArchitecture.md`](../Research/DiggingTerrainArchitecture.md).

## Snapshot

- Architecture research completed: `2026-09-12`.
- Previous asset checkpoint: `2026-09-11`, HEAD `46371c4` (`add voxel`).
- Project: ArcheoDig / artifact-digger, Unreal Engine `5.8`.
- Current direction: one bounded volumetric/density Dig Site architecture for all five biomes, varied through Soil Types, material data and behavior modules.
- Dynamic Mesh is a frozen interaction/visual reference, not the production terrain direction.
- Next stage: **VoxelFree Basic Dig** in `/Game/DiggingPrototype/Voxel/L_VoxelDigTest`.
- Installed experiment dependency: Voxel Plugin Free Legacy in `Plugins/VoxelFree`.
- VoxelFree is a prototype backend only until benchmarks pass; do not treat it as the production dependency.
- At the 2026-09-11 asset checkpoint the plugin loaded, but the test map did not yet contain verified Voxel digging logic.

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

## Immediate next stage: VoxelFree Basic Dig

Work in `/Game/DiggingPrototype/Voxel/L_VoxelDigTest` through the project-owned Dig/Terrain abstraction. Establish a small bounded world, perform a runtime dig, verify edit shape/collision and then run the `5 × 5 × 3 m @ 10 cm` production-oriented benchmark. Follow the experiment sequence and PASS/FAIL criteria in the full [research report](../Research/DiggingTerrainArchitecture.md); do not duplicate that roadmap here.

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
- Do not infer the live Voxel prototype state from this research document; inspect current Unreal assets first. The last verified asset checkpoint on 2026-09-11 contained only the plugin and test level.
- Never bypass `Gameplay → Dig/Terrain abstraction → concrete terrain backend` by coupling player/gameplay code directly to VoxelFree when the dependency can be isolated.
- After any Unreal edit, compile/save the touched asset and report exact paths and remaining warnings.
