# Dormitory — scripts

Current delivery includes the first-floor interior (2026-11-08). Use `export_fbx.py`
with the existing saved `.blend`: it exports temporary copies, fixed architecture
to the current main asset and separate parts to their FBXs. `EXPORT_TARGETS` can
limit export to asset basenames. It never saves or changes the editable source.
Meshes marked `export_preserve_normals` retain their source winding. This applies
to the repaired foundation, front ground-floor backing and thickened roof meshes.
Their validated faces must retain their direction, including downward-facing
roof undersides.
`add_first_floor_interior.py` is the completed one-time authoring operation, not
an export dependency; do not rerun it. See ../../README.md for current assets.

## Historical campus restyle notes

Current Blender collection: BLD_Dormitory. Parent: Dormitory_ROOT at (0,0,0), ground centre.
Four storeys; existing wall and window objects were retained in place.
Warm geometric brick, limestone trim/quoins, dark pitched slate roof, modest porch.
All ACs, large downpipes, antenna and flat-roof equipment removed, no archived model copy.
59 separate meshes, 36,781 triangles. Body footprint 26 x 18 m.
Complete measured envelope: 27.22 x 21.34923 x 14.24750 m.
No interior, merge, blend save, or UE export performed.

Game-design source of truth is now available in Docs/GameDesign/Buildings/StyleGuide.md, Dormitory.md and BlenderWorkflow.md.
The current restyle was originally derived from the user's university reference / screenshot and Level6_University_Detail.md; future iterations should also read the Buildings docs.

restyle_campus.py modifies the original assembly in place once; campus_finish.py
adds the small gable windows. These are operation scripts, not archived scene versions.
Do not rerun the original build/finalize scripts against the current restyled scene.
Current measurements and screenshots are in Saved/BlenderDormitory/.

Current delivery: editable blend and FBX saved under SourceAssets/Blender/Buildings/Dormitory/Source; imported as one UE Static Mesh and BO_Dormitory replaced. See SourceAssets/Blender/Buildings/Dormitory/README.md for validated units and placement. Earlier no-save/no-export notes describe the prior preview stage.
