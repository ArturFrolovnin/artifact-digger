# ArcheoDig

Прототип археологических раскопок и изменяемого грунта на Unreal Engine 5.8.

Текущий статус: VoxelFree-прототип и Dynamic Mesh reference сохранены; material hotfix выполнен. Проект получил первый Runtime C++ module `ArcheoDig`, учебный Blueprint → C++ bridge и заготовку `DiggingComponent`. Следующий шаг — минимальный вызов `ProcessDigging()` из `BP_DiggableGround`, затем постепенная migration небольшими блоками. Главный gameplay priority после bridge — cleanup floating terrain fragments.

Документация:

- [C++ workflow и план migration digging logic — checkpoint 2026-09-22](Docs/DiggingFeature/Checkpoints/2026-09-22_CPPWorkflowAndDiggingMigration.md)
- [Voxel Ground Material + Lighting Prototype — checkpoint 2026-09-14](Docs/DiggingFeature/Checkpoints/2026-09-14_VoxelGroundMaterialLighting.md)
- [Текущая архитектура копания и checkpoint](Docs/DiggingArchitecture.md)
- [Исследование terrain architecture, биомов, voxel/density backends и roadmap прототипов](Docs/Research/DiggingTerrainArchitecture.md)
- [Подробная история digging-прототипа](Docs/DiggingFeature/README.md)
- [Краткий контекст для AI-ассистентов](Docs/DiggingFeature/AI_CONTEXT.md)
