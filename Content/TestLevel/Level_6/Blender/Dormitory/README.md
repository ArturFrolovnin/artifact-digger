# Dormitory — UE5 test import

Editable source: Source/Dormitory_Blockout.blend (59 separate mesh assemblies).
Export: Source/SM_Dormitory_Blockout.fbx (building meshes only, no camera/light/root).
UE asset: /Game/TestLevel/Level_6/Blender/Dormitory/SM_Dormitory_Blockout.

Blender metres: body 26 x 18; full bounds 27.22 x 21.34923 x 14.24750.
Ground min Z = 0. Dormitory_ROOT = (0,0,0), centred on the body at ground level.
Rotation and Scale applied, object scales 1/1/1. Exterior surface normals corrected.
FBX export: -Y forward, Z up, FBX_SCALE_NONE, apply_unit_scale=True.
Units are baked for the importer; Blender source remains in metres.
Verified UE local bounds in centimetres:
min (-1361,-957.92297,0), max (1361,1177.00012,1424.75).

BO_Dormitory replaced in place in level_6_create_map:
location (5700,7400,24) cm; yaw 90 degrees; scale (1,1,1).
Ground aligns with the plot top at 24 cm; entry points towards -X.
UE import combines meshes into one Static Mesh, source blend remains separate.
Map and imported assets saved. No additional detail or interior added.
