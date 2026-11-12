# Blender sources

Editable scenes, FBX exports, material manifests and existing model scripts live outside Unreal `Content` so the editor does not automatically import every Blender object as a separate asset.

`models.json` records the current source paths and shared Unreal asset roots. `Buildings/` and `Residential/` follow the existing Unreal categories. `Archive/` preserves the older Rudy blockout; the museum and Graham source variants are also retained.

Use the current `.blend` as the geometry source. Historical build and placement scripts describe earlier operations; do not run them during export or project cleanup. Import/reimport and placement remain separate operations. Buildings still use their existing scripts. Characters use the shared [character pipeline](../../Tools/BlenderToUE/characters/README.md), configured by NPC in `Tools/BlenderToUE/characters/characters.json`.

Write fresh diagnostics to `Saved/`. Preview images and old generated reports are excluded. The source scenes and FBX files were recovered byte for byte from Git during the 2026-11-07 cleanup.

TownHall currently retains its editable source and materials; its combined Unreal mesh is absent. The registry records an empty `unreal_meshes` list for it.
