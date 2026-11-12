# Agent instructions — artifact-digger

Applies to this entire Unreal Engine 5.8 repository. **Work only within the user's requested scope**; do not rebuild existing systems or change unrelated game content.

## Find the relevant instructions

- **Building/interior Blender ↔ UE asset work:** read `Docs/Technical/BlenderToUE_ImportRules.md`. Use `SourceAssets/Blender/models.json` for model paths; verify actual assets in Unreal.
- **NPC/character import:** additionally read `Tools/BlenderToUE/characters/README.md` and the NPC entry in `Tools/BlenderToUE/characters/characters.json`. Characters use a Skeletal Mesh pipeline; do not apply building Static Mesh import steps to them.
- **Production game architecture:** read `Docs/Technical/GameCoreArchitecture.md` before introducing new gameplay systems, game maps or persistent player state. Keep production systems separate from `Content/TestLevel/`.
- **Design/gameplay changes:** consult only the relevant files under `Docs/GameDesign/` or `Docs/DiggingArchitecture.md`. Do not load the entire lore for an asset import.

## Non-negotiable defaults

1. **Model** means edit the existing Blender source. **Import/reimport** means update the existing UE asset in place. Do not import merely because modeling was requested.
2. **No automatic placement:** do not add/move actors, assemble Blueprints, change transforms, edit or save `.umap` files unless the user explicitly asks for level work. Existing placed instances may update visually after reimporting their shared asset.
3. Keep the editable `.blend` intact during export; use temporary export copies. Never run old `build_*.py` generators just to reimport a model.
4. Reimport to the **exact existing UE asset path**. Preserve names, materials, links and user settings. Import new independent building parts only into that building's `Parts/` next to `Materials/`. Never move/rename `.uasset` or `.umap` using the file system.
5. Use existing, verified scripts and MCP connections. The shared pipeline currently exists **for characters only**; do not assume a generic building CLI exists. Never claim a tool ran or succeeded without verification.
6. Avoid unsolicited screenshots, renders, GUI/computer-control sessions, backup copies, extra folders, commits and long logs. Keep full diagnostics in `Saved/`; report a short outcome and actual errors.

Before making changes, check working state and preserve unrelated edits. If an unsafe operation is ambiguous, stop and explain rather than inventing paths or parameters.
