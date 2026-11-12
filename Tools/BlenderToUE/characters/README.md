# Character import pipeline — Blender → Unreal Engine 5.8

Shared, **character-only** pipeline for Blender 5.2.2 and UE 5.8. It imports/reimports Skeletal Meshes; **it never places actors or saves levels**. Building Static Mesh imports remain a separate workflow (`Docs/Technical/BlenderToUE_ImportRules.md`).

## Run in the existing Unreal Editor

In the **Cmd** mode of the open project's UE console, with Blender open on the NPC's live scene and the existing Blender MCP add-on running:

```text
py "D:/UEProject/ArcheoDig/Tools/BlenderToUE/characters/run.py" --npc EllieRowan --mode all
```

The absolute path above is an example; use the **verified** local project path. Do not open another editor or launch a second MCP server. Existing connection settings: `.codex/config.toml`. Alternatively, after adding this directory to `sys.path`, run `run.run('EllieRowan', 'all')` in Unreal Python.

Modes:
- `validate` — check active Blender scene and the source UE skeleton; no import.
- `export` — validate and export FBX, then read it back; no UE asset changes.
- `all` — validate → export → import/reimport → validate. Skip export/import if geometry, config, FBX, source Skeleton and saved target are verified unchanged.
- `reimport` — force the full pipeline; the target Skeletal Mesh **must already exist**.

`characters.json` is the only NPC registry for this pipeline: select an existing Quinn profile, source `.blend`, armature, included/excluded collections, exact Skeletal Mesh path and materials path. Add an NPC there; **do not copy the scripts**. The Quinn Skeleton is discovered from the `SKM_Quinn_Simple` mesh and its Skeleton reference via Asset Registry; never guess a Skeleton path.

## Blender export safety

- Use the **live scene**, including unsaved edits; never save or replace the source `.blend` just to export. Export only configured collections; exclude the hidden Quinn weight reference, cameras, Empty and helpers. An object's viewport `hide_set` alone is not a reliable export exclusion.
- Use a neutral pose. Evaluate modifiers on temporary duplicates only; keep the source editable. Source units stay in **meters**; temporary exports convert to centimeters for a root-bone scale of **1**.
- FBX uses `-Y Forward / Z Up`, with **no animation or leaf bones**. Only the temporary exported armature's serialized name is adjusted to match the root bone; do not rename the source armature.
- Before UE import, round-trip the FBX and verify rest pose, bone names, parents and scale against Quinn (tolerances: **0.002 cm**, **0.02°**). Blender has 88 internal bones; FBX/UE add the `root` (89 total). Do not copy/modify extra corrective bones on the shared Skeleton.

## Unreal import safety

- Use the existing tested `FbxFactory` flow with FBX Interchange temporarily disabled and `save=False`; validate before explicitly saving **only affected asset packages**.
- Never update the Quinn Skeleton reference pose, `T0` pose, animations or create a new PhysicsAsset. Compare full Skeleton reference pose hash, tracked Skeleton/Quinn files, dirty/new packages, dirty maps and imported mesh geometry before/after.
- Reimport **to the same Skeletal Mesh path**; no duplicate assets. If material slot order or composition changes, stop. Preserve existing material assignments, including external custom materials.
- On first import, basic Blender PBR values can create simple materials (face uses vertex colors). **Procedural nodes/textures, artistic hair detail and facial expressions are not baked.** Temporary box UVs are technical only. Do not overwrite existing materials on reimport.
- FBX is stored alongside the NPC source `.blend`. Logs go to `Saved/BlenderToUE/Characters/<NPC>/{reference,export,import,result}.json` and `error.txt`.
- If a pre-import check fails, no UE assets change. If post-import validation fails, changed assets may remain **unsaved** in the editor: report this; do not claim an automatic rollback.

Checks without editors:

```sh
python -m unittest discover -s Tools/BlenderToUE/characters -p test_safety.py
```

Report only NPC, mode, status, target asset and errors. Open full logs only for failures. No screenshots, new MCP connections, level saves or unrelated asset changes.
