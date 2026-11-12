# Blender → Unreal Engine 5.8: agent asset workflow

**Scope:** Blender 5.2.2 LTS → UE 5.8 for reusable assets across all levels. Read this file only for Blender/UE asset tasks. **Default: import assets, never place actors or save maps.**

## 1. Pick the correct operation

- **Model:** edit the existing `.blend` only. Do not export/import without a request.
- **Import / Reimport:** update an existing UE asset **at its exact path**, or create a requested new asset. No level placement.
- **Place / level work:** separate, explicit user task. Historical `Place` scripts do not authorize placement.
- **Character / NPC:** use the dedicated Skeletal Mesh pipeline in `Tools/BlenderToUE/characters/README.md`, configured in `characters.json`. Do **not** use building Static Mesh scripts for NPCs.

**Current tool status:** `Tools/BlenderToUE/characters/` exists. A generic **building** launcher such as `Tools/BlenderToUE/run_pipeline.ps1` is **not installed**. Do not invent or run that command. Buildings currently use their existing verified, model-specific export/import scripts. Building a shared launcher is a separate task.

## 2. Locate the asset; preserve its identity

1. Check `SourceAssets/Blender/models.json`, the current `.blend`, FBX and real UE Asset Registry / Content Browser entry. Verify actual state: a registry path alone does not prove an asset exists.
2. Check Git and unsaved Blender/UE work. Do not overwrite unrelated or unsaved changes.
3. Reuse one shared UE asset across levels; never copy it into each level folder.
4. Preserve existing UE locations, including `/Game/Art/Models/Residential/`. For **new buildings** use `/Game/Art/Models/Buildings/<ModelId>/`; the main Static Mesh lives at its root, existing materials remain in `Materials/`.
5. New **independent** building components (movable doors, separate stairs, independent interior pieces) belong in the model's `Parts/` beside `Materials/`. Create `Parts/` if needed. Do not duplicate those parts inside the main mesh. Existing models use their **actual** folder, not a forced migration.
6. Editable sources, exported FBXs and scripts belong under `SourceAssets/Blender/<Category>/<ModelId>/` (follow existing layout). Source `.blend` is authoritative; do not regenerate it with historical `build_*.py`. Source moves require import-data updates, not new duplicate assets.
7. Never rename/move `.uasset` or `.umap` in the file system. Any requested migration must use UE Asset Tools in a separate task.

## 3. Efficient building export

- Select only the model root/tree (`BLD_*`, `*_ROOT` or configured root); exclude cameras, lights, background, helpers and animation.
- Keep source units in **meters**. Existing working FBX settings: `-Y Forward`, `Z Up`, `global_scale=1`, `apply_unit_scale=True`, `FBX_SCALE_NONE`. Expect **1 Blender meter = 100 UE centimeters**; do not add another ×100 conversion.
- Validate root transforms, expected dimensions/origin (usually bottom at local `Z=0` unless specified), mesh normals, nondegenerate geometry and required UVs. Keep material slot names stable.
- Evaluate modifiers and convert fonts/curves **only on temporary export copies**. Never destructively apply them to the editable source merely to export.
- If Blender is open with unsaved edits, use the active scene through the existing Blender MCP. Do not call `open_mainfile` in that session or silently save over the source. A background export may use the saved `.blend` only after verifying it is current.
- Use the smallest verified existing script. Skip unchanged export/reimport stages when source, FBX and target are already verified current.

## 4. UE import / reimport

- Prefer the **already open** Unreal Editor and its established Python/MCP execution route; do not start a second editor on the same project. If the editor is closed, a verified `-ExecutePythonScript` workflow may be used; check scripting plugins once.
- For reimport, update the existing main Static Mesh at its **exact** current asset path. Do not create `_1`, `_2`, `Copy` or `New` variants.
- Create genuinely new standalone Static Mesh parts only in `Parts/`. Keep the main asset at the building root and reuse `Materials/`.
- Preserve UE material assignments, slot order/names, custom materials (glass/two-sided), collisions, import settings and other user-defined Static Mesh settings. If reimport would change them unexpectedly, stop and report the risk.
- Save **only** the relevant asset packages. Do not create, replace or reposition actors; do not modify or save maps (`.umap`), and do not assemble a Blueprint unless separately requested.
- Reimporting shared geometry may change the appearance of already placed instances; it never authorizes changing those instances.

## 5. Character-specific rules

Read `Tools/BlenderToUE/characters/README.md` and only the selected NPC configuration in `Tools/BlenderToUE/characters/characters.json`. The current pipeline exports a **Skeletal Mesh** on the existing **Quinn Skeleton**, not a building Static Mesh. Its temporary export copies switch meter-based source geometry to centimeters while keeping root-bone scale 1. Preserve the Skeleton/Reference Pose, material slots and other NPC assets. The character pipeline does not place actors, bake artistic procedural textures or fix the character's appearance.

## 6. Verify and report

Use **Validate → Export → Import/Reimport → Validate** when the operation requires it; skip verified unchanged stages. Confirm:

- Target asset exists at its original path; new independent parts are in `Parts/`; no duplicates or unexpected asset edits.
- UE bounds match Blender dimensions; expected material slots/assignments and settings remain intact.
- No map saves, actor placement or transform changes occurred.
- No fatal log errors; inspect only affected assets, not the whole city.

On failure, **stop**, retain diagnostics in `Saved/BlenderToUE/`, and name the exact problem. Do not retry indefinitely with renamed assets or claim a rollback you did not verify.

```text
MODEL: <ModelId>
MODE: Model | Import | Reimport
STATUS: SUCCESS | SKIPPED | FAILED
ASSET: /Game/... (or none)
CHECKS: geometry/materials/levels
ERROR: none | concise reason
LOG: Saved/... (if any)
```

## 7. Keep context and tool calls small

- Read `AGENTS.md`, this document and **only the relevant model's** manifest/script. Do not load unrelated city lore or digging systems for an import.
- Use existing MCP connections from `.codex/config.toml`; do not recreate connections or invent pipeline commands.
- Read short command summaries; inspect detailed logs only when needed. No unsolicited screenshots, renders, preview folders, duplicate import scripts, backups or intermediate commits.
- For exceptional pipeline repair, consult `SourceAssets/Blender/README.md`, `Docs/GameDesign/Buildings/BlenderWorkflow.md` and the **specific** known scripts under `SourceAssets/Blender/`. Do not inspect all historical generators during routine imports.

**If instructions conflict:** explicit current user task → actual editor/tool state → verified model registry → this document → historical guidance. Never guess an unsafe path or destructive operation.
