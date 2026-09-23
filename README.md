# ArcheoDig

Прототип археологических раскопок и изменяемого грунта на Unreal Engine 5.8.

Текущий статус: C++ migration существенно продвинулась. `DiggingComponent` содержит рабочую ISM digging logic, `VoxelDigTestLibrary` предоставляет несколько VoxelFree test methods, а `Try Surface Dig C++` вызывает первую рабочую floating-fragment cleanup. Следующий этап — refinement/validation cleanup и сравнение digging methods в одинаковых условиях. VoxelFree остаётся experimental backend.

Документация:

- [C++ voxel digging и floating-fragment cleanup — checkpoint 2026-09-23](Docs/DiggingFeature/Checkpoints/2026-09-23_CPPVoxelDiggingAndFragmentCleanup.md)
- [C++ workflow и план migration digging logic — checkpoint 2026-09-22](Docs/DiggingFeature/Checkpoints/2026-09-22_CPPWorkflowAndDiggingMigration.md)
- [Voxel Ground Material + Lighting Prototype — checkpoint 2026-09-14](Docs/DiggingFeature/Checkpoints/2026-09-14_VoxelGroundMaterialLighting.md)
- [Текущая архитектура копания и checkpoint](Docs/DiggingArchitecture.md)
- [Исследование terrain architecture, биомов, voxel/density backends и roadmap прототипов](Docs/Research/DiggingTerrainArchitecture.md)
- [Подробная история digging-прототипа](Docs/DiggingFeature/README.md)
- [Краткий контекст для AI-ассистентов](Docs/DiggingFeature/AI_CONTEXT.md)
