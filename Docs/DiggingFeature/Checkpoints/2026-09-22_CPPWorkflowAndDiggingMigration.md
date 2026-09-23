# C++ Workflow and Digging Migration — checkpoint 2026-09-22

> **Historical snapshot:** продолжение текущего состояния находится в [C++ Voxel Digging and Fragment Cleanup — 2026-09-23](2026-09-23_CPPVoxelDiggingAndFragmentCleanup.md). После этого checkpoint `DiggingComponent` получил реальную ISM digging logic, появилась `VoxelDigTestLibrary`, а первая floating-fragment cleanup была реализована и проверена. Остальной текст ниже сохраняет состояние на 2026-09-22.

Проект: Artifact Digger / ArcheoDig, Unreal Engine 5.8.

Текущий HEAD при создании документа: `a1bc1a120af1e997ab9e9a3bacaae41de4c02c0e` — `I added training scripts in C++.`

Этот checkpoint фиксирует material hotfix, первый Runtime C++ module проекта, учебный Blueprint-to-C++ bridge и направление постепенного переноса digging logic. Архитектурные решения остаются authoritative в [`../../DiggingArchitecture.md`](../../DiggingArchitecture.md), а подробная история ранних прототипов — в [`../README.md`](../README.md).

## Scope и источники проверки

Проверены commits:

- `c00dd306c5c43aa40360a07c31ee7517c8e07674` — `hot fix`, 2026-09-22;
- `a1bc1a120af1e997ab9e9a3bacaae41de4c02c0e` — `I added training scripts in C++.`, 2026-09-22.

Проверены текущие C++ source, module/target files и существующие digging documents. `.uasset` и `.umap` используют Git LFS: commit/file scope проверяется по Git, но внутренний Blueprint/material graph не раскрывается обычным diff. Поэтому ниже явно разделены:

- **VERIFIED** — подтверждено repository/source;
- **OBSERVED** — результат сегодняшней работы, подтверждённый ручной проверкой пользователя;
- **PLANNED** — направление, ещё не реализованное полностью.

Это documentation-only изменение. C++, Blueprint/assets, материалы, project/build/solution files не изменялись.

## VERIFIED — commits и текущая реализация

### Material hotfix commit

Commit `c00dd306c5c43aa40360a07c31ee7517c8e07674` изменяет только:

- `/Game/DiggingPrototype/Voxel/Voxel_2/L_VoxelDig2`;
- `/Game/DiggingPrototype/Voxel/Voxel_2/Materials/M_VoxelGround_Prototype`.

Предыдущий [material/lighting checkpoint от 2026-09-14](2026-09-14_VoxelGroundMaterialLighting.md) зафиксировал проблемное состояние: normal `Lerp` не использовал ту же Grass/Dirt mask, что Base Color, а mask строилась с участием `PixelNormalWS`. Этот старый документ остаётся историческим snapshot до hotfix.

### Первый Runtime C++ module

Commit `a1bc1a120af1e997ab9e9a3bacaae41de4c02c0e` впервые добавил C++ module проекта:

```text
Source/
├── ArcheoDig.Target.cs
├── ArcheoDigEditor.Target.cs
└── ArcheoDig/
    ├── ArcheoDig.Build.cs
    ├── ArcheoDig.h
    ├── ArcheoDig.cpp
    ├── Public/
    │   ├── MyActorComponent.h
    │   └── DiggingComponent.h
    └── Private/
        ├── MyActorComponent.cpp
        └── DiggingComponent.cpp
```

`ArcheoDig.cpp` регистрирует primary game module через `IMPLEMENT_PRIMARY_GAME_MODULE`. `ArcheoDig.Build.cs` подключает `Core`, `CoreUObject`, `Engine` и `InputCore`. Созданы Game target `ArcheoDigTarget` и Editor target `ArcheoDigEditorTarget` с `BuildSettingsVersion.V7`.

Тот же commit включает project/solution setup (`ArcheoDig.uproject`, `.vsconfig`, `.slnx`) и несколько изменённых Unreal assets. Их наличие подтверждено составом commit; этот documentation checkpoint не интерпретирует внутренние binary changes как доказательство завершённой C++ migration.

### `MyActorComponent` — учебный эксперимент

Текущие файлы:

- `Source/ArcheoDig/Public/MyActorComponent.h`;
- `Source/ArcheoDig/Private/MyActorComponent.cpp`.

Проверенное по source состояние:

- `UMyActorComponent : UActorComponent`;
- `UCLASS(ClassGroup=(Custom), meta=(BlueprintSpawnableComponent))`;
- `ShowHelloWorld()` объявлена как `UFUNCTION(BlueprintCallable, Category="C++ Test")`;
- собственный component Tick отключён;
- `ShowHelloWorld()` выводит экранное сообщение через `GEngine->AddOnScreenDebugMessage` и сообщение в Output Log через `UE_LOG`.

Это learning/prototype code, а не production gameplay system. Через него изучены `.h`/`.cpp`, `UCLASS`, `GENERATED_BODY`, `UFUNCTION(BlueprintCallable)`, `BlueprintSpawnableComponent` и вызов C++ функции из Blueprint. Функция компонента вызывается у конкретного instance, поэтому компонент сначала должен быть добавлен в Actor/Blueprint и служить Target ноды.

### `DiggingComponent` — будущая production-oriented boundary

Текущие файлы:

- `Source/ArcheoDig/Public/DiggingComponent.h`;
- `Source/ArcheoDig/Private/DiggingComponent.cpp`.

Проверенное по source состояние:

- `UDiggingComponent : UActorComponent`;
- компонент доступен через `BlueprintSpawnableComponent`;
- `ProcessDigging()` объявлена как `UFUNCTION(BlueprintCallable, Category="Digging")`;
- собственный Tick компонента отключён;
- `ProcessDigging()` пока только обновляет тестовое жёлтое экранное сообщение `ProcessDigging работает из C++` с ID `1001`.

Реальная camera trace, range validation, timing и terrain edit logic в C++ ещё не перенесены. Нельзя считать `BP_DiggableGround` полностью переведённым на C++.

## OBSERVED — результаты сессии

Следующие результаты были проверены пользователем во время работы, но не доказываются одним текстовым Git diff:

- проект успешно собирался как Development Editor через Unreal Build Tool / Visual Studio;
- `ShowHelloWorld` появилась в Blueprint как C++ node;
- Blueprint вызвал функцию реального instance `MyActorComponent`; экранное сообщение и `UE_LOG` подтвердили bridge;
- material после hotfix успешно компилировался;
- Grass/Dirt transition визуально стал естественнее, с меньшим толстым зелёным слоем на стенках ямы.

Концептуальный material hotfix:

```text
VertexNormalWS.Z
→ Saturate
→ Power
→ height mask × orientation mask
→ одна итоговая Grass/Dirt mask
   ├── Base Color Lerp Alpha
   └── Normal Lerp Alpha

Dirt: WorldAlignedNormal
Grass: VertexNormalWS
→ Lerp
→ Normalize
→ Material Normal
```

`PixelNormalWS` после исправления больше не нужен в этом graph. Замена на `VertexNormalWS` убирает проблемную зависимость, при которой mask, участвующая в вычислении Material Normal, сама зависела от pixel normal и могла образовать circular shader dependency. Точная wiring-схема относится к наблюдению Editor-сессии: binary material asset не читается как текстовый graph в Git.

## Принятое направление: C++ + Blueprint

C++-first применяется к тяжёлой gameplay/terrain логике:

- voxel/density processing и terrain edits;
- digging algorithms;
- cleanup floating fragments;
- flood fill / connected components;
- большие циклы и массивы;
- performance-sensitive gameplay;
- потенциальные save/load algorithms.

Blueprint сохраняет orchestration и content-facing работу:

- events и input routing;
- вызов крупных C++ operations;
- VFX, SFX и animation;
- assets, визуальную настройку, конфигурацию и простые условия.

Главное performance правило — не делать частые Blueprint ↔ C++ переходы внутри тяжёлого цикла.

Хорошая граница:

```text
Blueprint Event / scheduler
→ один крупный ProcessDigging() call
→ trace, validation, loops и terrain processing внутри C++
```

Плохая граница:

```text
Blueprint → C++ GetCamera → Blueprint → C++ Trace
→ Blueprint → C++ FindVoxel → Blueprint → C++ RemoveVoxel → ...
```

Один Blueprint-to-C++ вызов на frame сам по себе не считается главной performance-проблемой. Стоимость и сложность появляются при постоянном дроблении тяжёлой операции через language boundary.

Архитектурная terrain boundary сохраняется:

```text
Gameplay / Blueprint orchestration
→ project-owned Dig/Terrain C++ abstraction
→ concrete terrain backend
```

## Краткая модель Unreal C++ для этого проекта

- `.h` объявляет interface/структуру класса; `.cpp` содержит implementation.
- Один Unreal class обычно представлен парой `.h`/`.cpp`.
- `Public/Private` folders модуля управляют видимостью headers между modules и не равны C++ access modifiers `public`/`private` внутри класса.
- `UCLASS`, `UFUNCTION` и `UPROPERTY` обрабатываются Unreal Header Tool.
- `*.generated.h` создаётся Unreal и обычно подключается последним include в header.
- `GENERATED_BODY()` добавляет сгенерированную object/reflection infrastructure.
- `UFUNCTION(BlueprintCallable)` публикует C++ функцию как Blueprint node.
- Нестатическая функция `ActorComponent` требует instance/Target компонента.
- Blueprint Function Library обсуждалась для stateless/global utility functions без component state; gameplay state/system логичнее держать в `ActorComponent` или другом владеющем объекте.

Это проектный контекст, а не полный C++ tutorial.

## Build, Live Coding и IDE workflow

Для изменения только implementation внутри `.cpp`:

1. Unreal Editor можно оставить открытым.
2. Запустить Live Coding через `Ctrl+Alt+F11`.
3. При необходимости остановить и снова запустить PIE, чтобы увидеть новое поведение.

Для reflection/header changes — новый `UCLASS`, `UFUNCTION`, `UPROPERTY`, новый C++ class или существенная правка `.h` — текущий безопасный workflow обучения:

1. закрыть Unreal Editor;
2. выполнить full build;
3. снова открыть Editor.

Это осторожное правило проекта из-за Unreal Header Tool, generated code, reflection и Blueprint metadata. Оно не утверждает, что Live Coding технически никогда не способен обработать header changes.

Текущий IDE workflow:

- Visual Studio 2026 Community/Insiders — Unreal C++, build, IntelliSense и debugger;
- Unreal Editor работает отдельно;
- Visual Studio можно attach к уже открытому `UnrealEditor.exe`, чтобы не запускать второй Editor;
- VS Code с Codex/Astra остаётся рабочим инструментом для документации, repository work и agent-assisted edits.

## Память и lifecycle guidance

- Указатель не означает обязательный ручной `delete`.
- `UObject` и `Actor` живут по Unreal lifecycle/GC patterns.
- Не использовать raw `new/delete` без явной необходимости и понятной ownership model.
- Actors создавать и удалять Unreal-way.
- Unreal containers/types использовать там, где они упрощают интеграцию с Engine.
- Тяжёлые циклы и algorithms держать в C++.

Это guidance и архитектурное направление; отдельная memory subsystem не реализована.

## Главный gameplay priority: terrain fragment cleanup

Проблема: после копания остаются маленькие floating pieces/islands, на которых игрок застревает и по которым приходится отдельно попадать мышью. Целевой ориентир — A Game About Digging A Hole: маленький disconnected fragment отделяется, падает или исчезает и не блокирует движение.

План:

1. Проверить VoxelFree Legacy API для voxel physics/disconnected pieces, если такая возможность доступна.
2. Не связывать архитектуру с потенциально платной или нестабильной функцией.
3. Production-friendly fallback после terrain edit:
   - взять локальные Edited Bounds и небольшой margin;
   - найти disconnected/floating connected components;
   - удалить маленькие components из terrain;
   - опционально создать visual debris actor;
   - debris не блокирует Pawn, падает и исчезает после небольшого lifetime.
4. Учитывать connected thin spikes/bridges: flood fill удалит disconnected islands, но не кусок, соединённый одним voxel. При подтверждении проблемы исследовать локальный neighbour/thickness cleanup или очень ограниченный smoothing/erosion pass.
5. `Max Step Height` использовать только как safety net.

Cleanup проектируется общим слоем для разных digging methods.

## План сравнения digging methods

После C++ bridge и базового cleanup проверить в одинаковых условиях:

- `RemoveSphere`;
- `TrimSphere`;
- текущий Surface Edit;
- Surface + Flatten;
- Surface + Strength Curve;
- Surface + Strength Mask;
- box/level-like methods оставить резервом.

Желательное будущее представление — `EDigMethod` и единый C++ interface, чтобы переключать method без нескольких больших Blueprint graphs.

Для каждого method проверить: один и соседние edits, глубокое копание, вертикальные стенки, тоннель/потолок, floating fragments, thin spikes, ходьбу, collision и деградацию performance после серии edits. Затем выбрать один-два кандидата для controlled benchmark.

## Material/lighting baseline

Material и lighting достаточно стабильны для gameplay/backend tests. Они больше не являются главным непосредственным приоритетом.

Рабочая база из предыдущей сессии:

- world-aligned Grass/Dirt material;
- `DirtTint = #C2A189`;
- `DirtTextureSize ≈ 180`;
- Dirt normal подключён;
- lighting/exposure настроены;
- глубокие шахты не должны искусственно оставаться светлыми; позже там нужен player light/flashlight.

Dirt Roughness/ORM, normal strength, Grass Normal/Roughness, parameter cleanup и Material Instance workflow отложены до более важных gameplay/backend задач.

## PLANNED — roadmap после текущего HEAD

### 0. Current state

- material hotfix выполнен;
- C++ Runtime module создан;
- Blueprint → C++ bridge проверен на `MyActorComponent`;
- `DiggingComponent` создан, но настоящая digging logic туда не перенесена.

### 1. Первый `DiggingComponent` proof

Добавить или проверить `DiggingComponent` в `/Game/DiggingPrototype/BP_DiggableGround`, затем собрать минимальную схему:

```text
Event Tick
→ Process Digging [C++]
```

Убедиться, что C++ node вызывается. Наличие изменённого binary Blueprint в commit само по себе не считается подтверждением этого подключения.

### 2. Первый маленький перенос в `ProcessDigging`

Переносить по одному проверяемому блоку:

- Player Camera Manager;
- Camera Location;
- Camera Rotation;
- Forward Vector;
- Line Trace By Channel.

Не переносить весь graph одним giant change.

### 3. Следующие блоки migration

- `DigReach` / range check;
- hit validation;
- `DigInterval` behavior;
- поиск/удаление soil instances или соответствующий backend operation.

### 4. Scheduling

Сначала изучить `Blueprint Event Tick → ProcessDigging`. После рабочего переноса сравнить это с C++-owned scheduling. Вероятное направление — timer/event-driven processing, поскольку старый `BP_DiggableGround` уже использует `DigInterval` / `NextDigTime`.

`BeginPlay` выполняется один раз; `Tick` — каждый frame. Возможная поздняя схема: `BeginPlay` запускает Timer, Timer вызывает `ProcessDigging` с нужным interval.

### 5–8. Gameplay/backend priorities

5. Реализовать общий terrain fragment cleanup — главный gameplay priority после базовой C++ migration.
6. Реализовать и сравнить оставшиеся digging methods через общую C++ abstraction.
7. Выполнить controlled benchmark: performance, collision, quality, cleanup, experimental `5 cm` против production-oriented `10 cm` target.
8. Вернуться к material polish: Dirt Roughness/ORM, normal strength, Grass Normal/Roughness, parameters и Material Instance workflow.
