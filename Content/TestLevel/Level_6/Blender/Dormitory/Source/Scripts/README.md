# Dormitory — current campus restyle

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

Current delivery: editable blend and FBX saved under Content/TestLevel/Level_6/Blender/Dormitory/Source; imported as one UE Static Mesh and BO_Dormitory replaced. See Content/TestLevel/Level_6/Blender/Dormitory/README.md for validated units and placement. Earlier no-save/no-export notes describe the prior preview stage.
