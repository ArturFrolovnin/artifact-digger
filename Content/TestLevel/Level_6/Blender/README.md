# Building assets

Keep each building in its own named folder. Do not put building materials or meshes in this root.

- `RudyPawnshop/`: Uncle Rudy's pawnshop; `SM_RudyPawnshop`, `Materials/`, editable Blender and FBX under `Source/`.
- `Dormitory/`: campus dormitory; `SM_Dormitory_Blockout`, `Materials/`, editable Blender and FBX under `Source/`.

Building-specific generation scripts are under each building's `Source/Scripts/`.
Move Unreal assets through the editor so references remain valid.
Diagnostic reports use `.txt` to avoid Unreal treating JSON reports as DataTables.
