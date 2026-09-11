# AI Context — ArcheoDig digging feature

Purpose: compact, persistent context for assistants continuing the digging work. Read [`../DiggingArchitecture.md`](../DiggingArchitecture.md) before modifying any digging asset; it is the authoritative checkpoint.

## Snapshot

- Checkpoint date: `2026-09-11`.
- Verified pre-documentation HEAD: `46371c4` (`add voxel`).
- Project: ArcheoDig / artifact-digger, Unreal Engine `5.8`.
- Current decision: freeze the working Dynamic Mesh implementation as a reference and evaluate bounded voxel Dig Sites.
- Next test map: `/Game/DiggingPrototype/Voxel/L_VoxelDigTest`.
- Installed experiment dependency: Voxel Plugin Free Legacy in `Plugins/VoxelFree`.
- Status: the Voxel plugin loads, but the test map has no Voxel World or `/Voxel/` asset dependency yet.

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
Conventional Unreal world
└── bounded Dig Site
    ├── chunks + density
    ├── soil/material layers
    ├── artifacts
    ├── persisted local edits
    └── local render/collision rebuild
```

Preferred edit flow:

```text
camera trace → local density brush → dirty intersecting chunks
→ local/async rebuild → collision refresh → fragment policy
```

Plan A: Voxel Plugin Free Legacy experiment.

Plan B: custom chunked density grid, approximately `15–25 cm` per cell, only inside small Dig Sites.

## Immediate next tasks

1. Add a small Voxel World to `/Game/DiggingPrototype/Voxel/L_VoxelDigTest`.
2. Reuse camera trace, impact point/normal and range from the first-person Blueprint.
3. Implement one runtime sphere/ellipsoid edit using the installed Legacy API.
4. Test one cut, neighboring cuts, 10 edits and 100 edits.
5. Measure hitch and verify collision.
6. Test a tunnel/wall-side cut and floating fragments.
7. Check bounded save/load.
8. Decide VoxelFree versus the custom density-grid Plan B.

Do not start large-world voxelization, inventory, shovel upgrades, soil layering or final persistence before this backend decision unless explicitly requested.

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
- Do not claim the current Voxel test is implemented: only the plugin installation and empty test level are verified.
- After any Unreal edit, compile/save the touched asset and report exact paths and remaining warnings.
