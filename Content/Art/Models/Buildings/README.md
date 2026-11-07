# Shared building assets

Unreal buildings use `/Game/Art/Models/Buildings/<ModelId>/`. Meshes, materials and Material Instances stay together; levels reuse the same assets.

Current building folders: BusStop, CafeBar, CarDealership, ConspiracyHouse, Dormitory, GeneralStore, GrahamShop, Hospital, Library, Museum and RudyPawnshop. MiaHouse and TownHall use the existing `/Game/Art/Models/Residential/` category alongside the other houses. Do not reorganize categories without a separate task.

Editable `.blend` scenes, FBX exports, manifests and existing scripts live under `SourceAssets/Blender/<Category>/<ModelId>/`, outside Unreal Content. See `SourceAssets/Blender/models.json` for the current paths. Model source folders and preview images are not Unreal assets.

The old `Content/TestLevel/Level_6/Blender` folder has been removed. Asset moves and reference repairs must use Unreal Editor APIs. Do not move or rename `.uasset` or `.umap` files in the filesystem.
