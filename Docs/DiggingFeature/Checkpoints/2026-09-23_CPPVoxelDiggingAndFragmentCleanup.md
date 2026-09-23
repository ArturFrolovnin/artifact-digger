# C++ Voxel Digging and Fragment Cleanup — checkpoint 2026-09-23

Проект: Artifact Digger / ArcheoDig, Unreal Engine 5.8.

Проверенный HEAD: `a668940037394508a58dbf309606f65465d17876` — `add c++ voxel digging tests and floating fragment cleanup`.

Этот checkpoint продолжает [C++ Workflow and Digging Migration — 2026-09-22](2026-09-22_CPPWorkflowAndDiggingMigration.md). Старый checkpoint остаётся историческим snapshot до переноса ISM digging logic и до появления C++ voxel test library.

## Scope и достоверность

Проверены commit `a668940`, текущие `ArcheoDig.Build.cs`, `DiggingComponent`, `TriggerLightActor` и `VoxelDigTestLibrary`. Source является главным источником фактов о C++ implementation. Внутреннее состояние `.uasset`/`.umap` обычным Git diff не раскрывается, поэтому результаты Editor/PIE записаны как **OBSERVED**.

- **VERIFIED** — подтверждено source или Git.
- **OBSERVED** — вручную проверено пользователем в Editor/PIE/build workflow.
- **PLANNED** — ещё не реализовано или не завершено.

Это documentation-only изменение. C++, Blueprint/assets, project/build files, материалы, уровни и плагины не изменялись.

## VERIFIED — commit и C++ structure

Commit `a668940` изменяет Runtime module, ISM и voxel prototype assets и добавляет:

```text
Source/ArcheoDig/
├── Public/
│   ├── DiggingComponent.h
│   ├── testLightCube/TriggerLightActor.h
│   └── voxelTests/VoxelDigTestLibrary.h
└── Private/
    ├── DiggingComponent.cpp
    ├── testLightCube/TriggerLightActor.cpp
    └── voxelTests/VoxelDigTestLibrary.cpp
```

`ArcheoDig.Build.cs` теперь содержит public dependency `Voxel`. Runtime module напрямую компилирует экспериментальный код против Voxel Plugin Free Legacy API. Это dependency текущего prototype, а не решение считать VoxelFree production backend.

## VERIFIED — `DiggingComponent` migration

`UDiggingComponent::ProcessDigging()` больше не debug stub. В C++ перенесён рабочий loop раннего ISM / `BP_DiggableGround` prototype:

```text
GetWorld
→ PlayerController + PlayerPawn
→ Left Mouse Button held / just pressed
→ DigInterval / NextDigTime
→ PlayerCameraManager
→ Camera Location + Rotation + Forward Vector
→ Visibility Line Trace, ignore PlayerPawn
→ Owner + UInstancedStaticMeshComponent SoilBlocks
→ Hit Component validation
→ DigReach from Pawn to ImpactPoint
→ GetInstancesOverlappingSphere
→ one RemoveInstances call
→ debug line / point / message
```

Собственный component Tick остаётся выключенным. Scheduling пока ожидается снаружи через Blueprint `Event Tick → Process Digging`; фактическое копание ограничивается `DigInterval` внутри C++.

Проверенные defaults из `DiggingComponent.h`:

| Parameter | Default | Meaning |
| --- | ---: | --- |
| `DigRadius` | `65 cm` | Radius для поиска и удаления ISM instances |
| `DigInterval` | `0.25 s` | До четырёх разрешённых попыток копания в секунду |
| `DigReach` | `350 cm` | Максимальная дистанция от Pawn до hit |
| `TraceDistance` | `800 cm` | Длина camera trace |
| `bDrawDebug` | `true` | Debug line и impact point |
| `NextDigTime` | `0` | Private runtime state |

Hit должен принадлежать найденному `SoilBlocks`. Instances удаляются одним `RemoveInstances(InstanceIndices)`, чтобы избежать проблем со сдвигом индексов при последовательном удалении.

Это существенный прогресс Blueprint → C++ migration старого ISM prototype. Он не означает, что voxel backend, все digging implementations или вся система terrain уже сведены в единый production component.

## VERIFIED — `TriggerLightActor` learning experiment

`ATriggerLightActor : AActor` создаёт C++ component tree:

```text
Root
├── PlateMesh
├── TriggerBox
└── CubeMesh
    └── CubeLight
```

- Actor Tick выключен.
- `TriggerBox` имеет half extent `(100, 100, 30)`, работает как `QueryOnly`, игнорирует остальные channels и принимает Pawn overlap.
- `CubeMesh` расположен на `(300, 0, 50)` относительно Root.
- `CubeLight` расположен на `(0, 0, 100)` относительно Cube, имеет intensity `5000`, attenuation radius `500` и выключен при старте.
- `OnComponentBeginOverlap` и `OnComponentEndOverlap` подписаны в C++ через `AddDynamic`.
- Begin overlap с `APawn` включает свет; End overlap выключает.

Commit добавляет `/Game/New_world/BP_TriggerLightActor` — Blueprint child/prefab для Editor configuration. По наблюдению пользователя этот Actor работал в Editor. Это учебный пример модели **C++ implementation + Blueprint prefab/config**, а не важная production subsystem.

## VERIFIED — `VoxelDigTestLibrary`

`UVoxelDigTestLibrary : UBlueprintFunctionLibrary` находится в:

- `Source/ArcheoDig/Public/voxelTests/VoxelDigTestLibrary.h`;
- `Source/ArcheoDig/Private/voxelTests/VoxelDigTestLibrary.cpp`.

Один class публикует несколько независимых `BlueprintCallable` nodes в категории `ArcheoDig|Voxel Tests`. Отдельный C++ class для каждой node не требуется.

Текущие Blueprint display names:

- `Try Remove Sphere C++`;
- `Try Trim Sphere C++`;
- `Try Surface Dig C++`;
- `Try Surface Flatten C++`;
- `Try Surface Strength Curve C++`;
- `Try Surface Strength Mask C++`.

Это экспериментальная library для сравнения methods. Она напрямую вызывает VoxelFree Legacy API, но gameplay architecture по-прежнему должна обращаться к project-owned Dig/Terrain abstraction, а не размазывать plugin-specific calls по player/gameplay code.

### Общий trace helper

Повторяющаяся camera trace logic вынесена во внутренний `TraceVoxelWorld()` в anonymous namespace. Helper:

```text
WorldContextObject
→ UWorld
→ PlayerCameraManager
→ Camera Location + Rotation + Forward Vector
→ Visibility Line Trace
→ ignore PlayerPawn
→ FHitResult
→ Cast HitActor to AVoxelWorld
→ FVoxelDigTraceResult
```

`FVoxelDigTraceResult` хранит `World`, `VoxelWorld`, trace start/end, `ImpactPoint` и `ImpactNormal`. Это уменьшает duplication между test nodes; тип и helper не публикуются в Blueprint.

### Defaults и фактическое состояние methods

| Method | Defaults | VERIFIED implementation / current status |
| --- | --- | --- |
| Remove Sphere | trace `500`, radius `20`, debug `true` | `UVoxelSphereTools::RemoveSphere`; простой sphere carve |
| Trim Sphere | trace `500`, radius `20`, falloff `0.35`, additive `false`, debug `true` | `TrimSphere` использует `-ImpactNormal` |
| Surface Dig | trace `500`, radius `20`, falloff `0.55`, strength `10`, cleanup `true`, cleanup radius `100`, max fragment voxels `100`, debug `true` | Surface stack + optional cleanup; текущий preferred prototype candidate |
| Surface Flatten | trace `500`, radius `20`, falloff `0.55`, strength `10`, debug `true` | `ApplyFlatten` plane проходит через текущий `ImpactPoint` с `ImpactNormal` |
| Surface Strength Curve | trace `500`, radius `20`, strength `10`, debug `true` | Требует valid `UCurveFloat`; без curve показывает сообщение и возвращает `false` |
| Surface Strength Mask | нет параметров кроме world context | Показывает, что Voxel Plugin Free Legacy требует Pro, и возвращает `false` |

`TrySurfaceDig` выполняет:

```text
TraceVoxelWorld
→ MakeIntBoxFromGlobalPositionAndRadius
→ FindSurfaceVoxelsFromDistanceField
→ ApplyFalloff(Smooth)
→ ApplyConstantStrength
→ ApplyStack
→ EditVoxelValues
→ optional CleanupFloatingFragments
```

`EditVoxelValues` использует distance divisor `1`, multithreaded edit и update render. `TrySurfaceDig` остаётся текущим наиболее перспективным из проверенных test methods, но не объявляется финальным production digging algorithm или доказанным production backend.

## VERIFIED — первая floating-fragment cleanup

`CleanupFloatingFragments()` — внутренний C++ helper, вызываемый после успешного `TrySurfaceDig`, если `bCleanupFloatingFragments = true`.

Проверенная последовательность:

```text
ImpactPoint + CleanupRadius
→ MakeIntBoxFromGlobalPositionAndRadius
→ FVoxelData
→ one FVoxelWriteScopeLock for Bounds
→ Data.GetValues(Bounds)
→ find solid connected components in memory
→ 6-neighbor flood fill: ±X, ±Y, ±Z
→ preserve component touching local boundary
→ preserve component larger than MaxFragmentVoxels
→ Data.SetValue(position, FVoxelValue::Empty())
→ release lock
→ UpdateBounds when voxels were removed
```

`FVoxelValue::IsEmpty()` отделяет empty samples от solid. Локальные координаты преобразуются в одномерный index `X + Y*Size.X + Z*Size.X*Size.Y`. Для очереди flood fill используются `TArray<int32> Queue` и `QueueHead`, отдельно хранится `Component` и `Visited`.

Conservative rules первой версии:

- component, касающийся любой стороны локального Bounds, считается потенциально продолжающимся в основную землю и сохраняется;
- component удаляется только если он не касается boundary и `Component.Num() <= MaxFragmentVoxels`;
- по умолчанию локальный radius `100 cm`, threshold `100` voxel samples;
- после снятия write lock вызывается `UVoxelBlueprintLibrary::UpdateBounds`;
- debug при реальном удалении показывает `Cleanup: fragments N | voxels N`.

### Ограничения prototype cleanup

- Анализируется локальный Bounds, не весь terrain.
- Boundary-touching component сохраняется даже если фактически disconnected за пределами рассматриваемой области.
- Большие disconnected components выше threshold сохраняются.
- Используется 6-connectivity; диагональные связи могут классифицироваться иначе, чем при 18/26-connectivity.
- Thin bridge/spike, соединённый с основной массой хотя бы цепочкой samples, flood fill не удалит.
- Debris Actor, physics, падение и lifetime не реализованы.
- Параметры cleanup требуют настройки на разных forms/resolutions.
- Алгоритм выполняет синхронный локальный read/flood-fill/write; performance ещё не benchmarked.

Это работающий proof, а не финальный production cleanup.

## Implementation/build note: `VoxelData.inl`

Для прямого template-вызова `FVoxelData::SetValue` / `Set<FVoxelValue>` нужен:

```cpp
#include "VoxelData/VoxelData.inl"
```

Без `.inl` compilation доходила до linker stage, затем возникал `LNK2019` на `FVoxelData::Set<FVoxelValue>`. После include normal/full build прошёл. `FVoxelDataLock.h` используется для `FVoxelWriteScopeLock`, `VoxelValue.h` — для `FVoxelValue::Empty()`.

## OBSERVED — Editor/PIE results

Пользователь вручную подтвердил:

- `TriggerLightActor` работает в Editor;
- C++ voxel nodes появились в Blueprint;
- `Try Surface Dig C++` реально копает и заменяет большой `TryVoxelSurfaceDig2` graph одной node;
- Remove Sphere и Trim Sphere работают;
- первая cleanup удаляет часть маленьких отделённых fragments и выглядит «почти как нужно»;
- project/full builds после исправлений проходят.

Это functional prototype observations, не controlled benchmark claims.

Surface Flatten в текущем виде почти не даёт желаемого копания на обычной поверхности. Source подтверждает, что flatten plane проходит через `ImpactPoint`; вероятная причина наблюдения — plane почти совпадает с существующей surface.

Strength Curve implementation существует, но полноценный визуальный тест с назначенной `UCurveFloat` не завершён. Strength Mask недоступен в текущей Free Legacy version без Pro; это ограничение конкретного method и не блокирует собственный C++ floating-fragment cleanup.

## Build и Live Coding workflow

Подтверждённый безопасный workflow проекта:

- изменение только `.cpp` implementation → Editor можно оставить открытым, использовать Live Coding `Ctrl+Alt+F11`, затем при необходимости перезапустить PIE;
- изменение `.h`, `UCLASS`, `UFUNCTION`, `UPROPERTY` или Blueprint-visible signature → закрыть Editor, выполнить full build, снова открыть Editor.

Во время сессии изменение `UFUNCTION` signature с Live Coding привело к failed patch; normal build с закрытым Editor восстановил рабочее состояние. Это практическое правило проекта, а не утверждение, что Live Coding никогда не способен обработать header changes.

## PLANNED — ближайшие эксперименты

1. Настроить и проверить cleanup на разных fragments: варьировать `CleanupRadius` и `MaxFragmentVoxels`, отслеживать false-positive/false-negative cases и hitch.
2. Проверить глубокие/соседние edits, стены, тоннель/потолок, collision, ходьбу, boundary cases и 6-connectivity behavior.
3. Исследовать thin spikes/bridges отдельным локальным thickness/neighbour cleanup; не считать flood fill решением connected artifacts.
4. Для Surface Flatten протестировать **ещё не реализованный** plane offset `ImpactPoint - ImpactNormal * FlattenDepth`.
5. Создать и визуально проверить `UCurveFloat` для Strength Curve.
6. Сравнить working methods в одинаковых условиях. Strength Mask Pro не является обязательным кандидатом.
7. После refinement вынести test-method selection/cleanup за единый project-owned C++ interface; возможный `EDigMethod` остаётся design direction.
8. Только после method/cleanup validation переходить к controlled benchmark и выбору одного-двух кандидатов.

Material/lighting остаётся достаточным baseline. Dirt Roughness и дальнейший art polish не являются immediate priority.

## Сохраняемые архитектурные границы

```text
Gameplay / orchestration
→ project-owned Dig/Terrain abstraction
→ concrete terrain backend
```

- VoxelFree Legacy остаётся experimental backend.
- `VoxelDigTestLibrary` — test harness, а не окончательная public gameplay API.
- Dynamic Mesh сохраняется как frozen/reference implementation.
- Production fallback — custom bounded chunked density field.
- Surface Dig — preferred prototype candidate, не финальный победитель.

