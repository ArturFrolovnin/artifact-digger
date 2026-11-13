# Production game structure — The Lost Velunith

Scope: **production gameplay** for the single-player Unreal Engine 5.8 project (C++ module: `ArcheoDig`). This document defines folder ownership and the first playable loop. **Do not create all the proposed classes upfront.** Implement each system when the player-facing feature needs it.

## Key separation

- **Maps contain locations and placed actors.** They must not own persistent inventory, currency, item catalogs, travel rules or global interaction code.
- **Game features contain reusable logic and assets.** Adding a new Dig Site, pawnshop or collectible should mainly mean configuring assets and maps, not duplicating C++ logic.
- **`Content/TestLevel/` stays a laboratory.** Do not relocate experiments into production or delete their maps. Re-implement a clean production feature using knowledge from the experiments.
- **Shared imported art stays in its verified existing folders**, such as `Content/Art/Models/`. Do not duplicate shared models inside map folders.

## Content layout (Unreal assets)

```text
Content/
├── TestLevel/                       # existing experiments, unchanged
│   ├── Level_1 ... Level_5/
│   ├── Level_6/                     # current town blockout/reference maps
│   └── Level_7/
├── Art/Models/                      # existing reusable imported meshes
└── Game/                            # production assets
    ├── Gameplay/
    │   ├── BP_PlayerCharacter
    │   ├── BP_GameplayPlayerController
    │   └── BP_GameplayGameMode
    ├── MainMenu/
    │   ├── BP_MenuGameMode
    │   ├── BP_MenuPlayerController
    │   └── WBP_MainMenu
    ├── Characters/
    │   └── NPC/
    ├── Features/
    │   ├── Interaction/             # interaction BP and prompts
    │   ├── Travel/                  # stop/exit destination configuration
    │   ├── Items/                   # DA_Item_* definitions, pickups
    │   ├── Inventory/               # inventory widgets and configuration
    │   ├── Economy/                 # pawnshop UI and currency presentation
    │   └── Digging/                 # production digging BP/VFX (not tests)
    ├── Levels/
    │   ├── MainMenu/                # L_MainMenu.umap
    │   └── Town/                    # L_Town.umap
    └── UI/
        └── HUD/                     # shared in-game HUD
```

This is the current production Content layout. Unreal mounts `Content/` as `/Game/`, so `Content/Game/Gameplay/` is `/Game/Game/Gameplay/` in asset references. `Features/`, `Characters/NPC/` and `UI/HUD/` reserve ownership for future content; their presence does not imply that those systems are implemented.

**Production maps keep their existing paths:** `/Game/Game/Levels/MainMenu/L_MainMenu` and `/Game/Game/Levels/Town/L_Town`. Experimental town blockouts under `Content/TestLevel/Level_6/` remain separate reference maps. `L_DigSite_01` is still planned. Create or move Unreal assets **inside Unreal Editor / Asset Tools**, update and save their referencers, then run **Fix Up Redirectors in Folder** (called **Update Redirector References** in UE 5.8). Verify old paths have no remaining referencers before removing unused redirectors or empty folders. Never move `.uasset` or `.umap` files through Git or the file system.

### Existing gameplay and menu wiring

- `L_MainMenu` overrides its GameMode with `/Game/Game/MainMenu/BP_MenuGameMode`. That mode uses `BP_MenuPlayerController`, which creates `WBP_MainMenu` and sets UI input mode. The widget has **Start** and **Exit** buttons. Start sets game input mode and opens `L_Town`; Exit calls `QuitGame`.
- `L_Town` overrides its GameMode with `/Game/Game/Gameplay/BP_GameplayGameMode`. Its default controller is `BP_GameplayPlayerController`, and its default pawn is `BP_PlayerCharacter`, both in the same `Gameplay/` folder.
- Gameplay uses Enhanced Input with the existing `/Game/Input/IMC_Default` and `/Game/Input/IMC_MouseLook`. The character binds the corresponding actions under `/Game/Input/Actions/` for WASD movement, mouse look and jumping. Keep these exact context references; the Voxel Plugin contains unrelated contexts with matching short names.
- `BP_PlayerCharacter` retains the existing first-person movement and camera logic. Experimental digging is not part of this production character. The test character and its test maps stay under `Content/TestLevel/`.

## C++ layout (one existing ArcheoDig module)

```text
Source/ArcheoDig/
├── ArcheoDig.Build.cs
├── Public/Game/
│   ├── Core/                     # game framework and shared state types
│   ├── Interaction/              # interfaces and interaction component
│   ├── Travel/                   # map travel and arrival identifiers
│   ├── Items/                    # item definitions and item IDs
│   ├── Inventory/                # inventory storage/operations
│   ├── Economy/                  # wallet and item-sale logic
│   └── Digging/                  # production terrain-facing API
└── Private/Game/
    └── (same feature directories, for .cpp implementations)
```

The existing `DiggingComponent`, `voxelTests` and learning experiments remain unchanged where they are. New production code goes in `Game/`; do not move historical C++ files just for symmetry.

## Gameplay framework and ownership

| Lifetime | Owner | Responsibilities |
|---|---|---|
| Whole app / between `OpenLevel` transitions | `UGameInstanceSubsystem` | Session inventory, currency and travel state. Do not store direct references to level actors. |
| Each loaded map | `AGameModeBase` / map | Rules for that map (menu vs gameplay), player spawning and world setup. Recreated on normal `OpenLevel`. |
| Player while in a map | Pawn/Character and components | Input, camera, traces, character animation, immediate interaction. Recreated on map load. |
| Placed world object | Actor + reusable interface | Collectible, bus stop, pawnshop counter, exit; holds configuration, not global state. |
| Restarting game later | `USaveGame` (future) | Disk persistence only when explicitly implemented; `GameInstance` alone does **not** save to disk. |

For our **single-player** first slice, a small `UInventorySubsystem : UGameInstanceSubsystem` and `UWalletSubsystem : UGameInstanceSubsystem` can hold authoritative session data across maps. The player should not maintain conflicting duplicate copies. Add a `UTravelSubsystem` only once travel behavior needs more than direct map open. Avoid premature managers for hypothetical features.

### Feature contracts when implemented

- **Interaction:** a single player `UInteractionComponent` performs a trace on `E`. Target actors implement one `Interactable` interface (prompt + interact action). No special interaction code per level.
- **Travel:** bus stops and exits supply destination map and optional arrival identifier. A travel service validates it and opens the level. Arrival marker is resolved in the loaded world. Never store an Actor pointer from a previous map.
- **Items:** a reusable item definition (for example `UPrimaryDataAsset` / `DA_Item_*`) contains stable item ID, name, value and presentation data. Pickups reference a definition, not custom one-off inventory logic.
- **Inventory:** entries store stable item ID + quantity, not pickup Actor pointers. Pickup adds an item and removes the world pickup only after successful addition. Session data survives map changes.
- **Economy:** pawnshop removes an eligible item from inventory, then credits currency only on successful transaction. The pawnshop does not own the global wallet.
- **Digging:** separate the player interaction and loot discovery from the terrain implementation. The VoxelFree Legacy code under tests is a reference, not the public API of the production game.

## First playable sequence

1. Keep the existing `L_MainMenu` → `L_Town` foundation working: **Start**, **Exit**, first-person movement, mouse look and jump.
2. Extend the existing production `L_Town` with approved city content and one interactive bus stop when that work is requested. Do not move or modify the experimental town maps as part of production folder maintenance.
3. Create `L_DigSite_01`, add return travel, then validate town → site → town in editor **and** a Windows packaged Development build.
4. Add one repeatable digging action, one collectible, minimal session inventory and pawnshop transaction. Verify item and money survive travel.
5. Package again and play the complete loop twice.

**Build/config:** `Config/DefaultEngine.ini` still uses the experimental Level_1 as Editor Startup Map and Game Default Map, with the ThirdPerson global GameMode. The production maps use their own GameMode overrides. Startup and packaging settings were not changed by this folder migration; change them only when production startup/packaging work is explicitly requested.

## Definition of done and change policy

- A feature should work in more than one map/actor without copying its C++ business logic.
- Keep `.h` and `.cpp` organized under matching `Public/Game/<Feature>/` and `Private/Game/<Feature>/` directories; Blueprints and Data Assets go under the corresponding `Content/Game/Features/<Feature>/`.
- Use small, incremental, verified changes. No speculative features or empty C++ classes just to fill directories.
- Framework Blueprints belong in `Content/Game/Gameplay/`; menu Blueprints and the menu widget belong together in `Content/Game/MainMenu/`. Production maps stay under `Content/Game/Levels/`. This Blueprint organization does not rename the C++ `Public/Game/Core/` and `Private/Game/Core/` ownership paths.
- For UE assets, create/move through **Content Browser / Unreal Asset Tools**, not Git or file system; empty placeholder folders may not appear in Content Browser until they contain an Unreal asset.
