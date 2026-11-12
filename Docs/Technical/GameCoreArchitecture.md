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
    ├── Maps/
    │   ├── Menu/                    # L_MainMenu (future .umap)
    │   ├── Town/                    # L_Town (future .umap)
    │   └── DigSites/                # L_DigSite_01, future Dig Sites
    ├── Core/                        # game modes, player/controller BP
    ├── Features/
    │   ├── Interaction/             # interaction BP and prompts
    │   ├── Travel/                  # stop/exit destination configuration
    │   ├── Items/                   # DA_Item_* definitions, pickups
    │   ├── Inventory/               # inventory widgets and configuration
    │   ├── Economy/                 # pawnshop UI and currency presentation
    │   └── Digging/                 # production digging BP/VFX (not tests)
    └── UI/
        ├── Menu/                    # WBP_MainMenu
        └── HUD/                     # shared in-game HUD
```

**Current maps are not renamed by this structure change.** The actual town map is currently under `Content/TestLevel/Level_6/`; check whether `NewMap` or `level_6_create_map` is the intended source in Unreal before producing `L_Town`. Create/copy/migrate Unreal map assets **inside Unreal Editor** (and verify dependencies/redirectors), never via a raw Git/file-system rename. Do not duplicate all city models. `L_MainMenu`, `L_Town` and `L_DigSite_01` are **future asset names**, not files created by this documentation-only change.

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

1. Build `L_MainMenu` with `WBP_MainMenu`: **Start** and **Exit** only. Start opens the production town map; Exit quits.
2. Create `L_Town` (using the approved city assets/layout without moving existing test maps). Place player and one interactive bus stop.
3. Create `L_DigSite_01`, add return travel, then validate town → site → town in editor **and** a Windows packaged Development build.
4. Add one repeatable digging action, one collectible, minimal session inventory and pawnshop transaction. Verify item and money survive travel.
5. Package again and play the complete loop twice.

**Build/config:** `Config/DefaultEngine.ini` currently points at the experimental Level_1. Change Game Default Map to `L_MainMenu` and add only intended production maps to packaging settings **after these map assets exist**. Do not change startup settings as part of empty-folder creation.

## Definition of done and change policy

- A feature should work in more than one map/actor without copying its C++ business logic.
- Keep `.h` and `.cpp` organized under matching `Public/Game/<Feature>/` and `Private/Game/<Feature>/` directories; Blueprints and Data Assets go under the corresponding `Content/Game/Features/<Feature>/`.
- Use small, incremental, verified changes. No speculative features or empty C++ classes just to fill directories.
- Existing assets and source maps are not relocated/renamed as part of this layout task.
- For UE assets, create/move through **Content Browser / Unreal Asset Tools**, not Git or file system; empty placeholder folders may not appear in Content Browser until they contain an Unreal asset.
