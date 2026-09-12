# ArcheoDig — checkpoint архитектуры копания

Дата checkpoint: **2026-09-12**

Проверенный HEAD до checkpoint этой сессии: `4f999557bb0db4e1cac10f7948865fbe3b60801c` (`add research and test level voxel`)

Проект: Unreal Engine **5.8**

Architecture research update: **2026-09-12**

Это основной актуальный документ по архитектуре копания. В нём факты, проверенные по репозиторию и Unreal assets, отделены от наблюдений прототипирования и проектных гипотез, которые ещё нужно проверить.

## Краткий статус

В проекте сохранены четыре полезных этапа разработки:

1. ранний ручной voxel / Instanced Static Mesh эталон;
2. рабочий Geometry Script / Dynamic Mesh Boolean прототип;
3. первый Voxel Plugin Free Legacy baseline в `L_VoxelDigTest`;
4. отдельный `Voxel_2` prototype с работающими `TrimSphere` и surface-edit brushes.

Dynamic Mesh версия подтверждает работу interaction loop, full-body first person, проекции материала и обновления collision во время игры. Однако повторные Boolean Subtract постепенно ухудшают topology. Global remesh и local smoothing были проверены и отклонены для realtime.

Текущее решение: **Dynamic Mesh ветка заморожена как рабочий checkpoint; bounded volumetric/density Dig Sites развиваются через собственную abstraction boundary**. VoxelFree prototype подтвердил runtime terrain edits. `TryVoxelSurfaceDig2` сейчас является предпочтительным из проверенных brush-кандидатов, но VoxelFree по-прежнему не выбран production backend. Production fallback — собственный bounded chunked density field.

Полный checkpoint текущих assets, точных параметров и наблюдений: [Voxel Surface Prototype — 2026-09-12](DiggingFeature/Checkpoints/2026-09-12_VoxelSurfacePrototype.md).

Полное обоснование, сравнение backends, модель пяти биомов, расчёты resolution/chunks и roadmap экспериментов находятся в [исследовании terrain architecture](Research/DiggingTerrainArchitecture.md). Здесь сохранены только принятые после него рабочие решения.

Последовательность последних содержательных commits подтверждает этот переход:

- `358ab06` — `add first person setup and configurable cutter`;
- `d260dc4` — `dynamic mesh digging prototype`, включая `M_DiggableSoil`;
- `46371c4` — `add voxel`, включая `L_VoxelDigTest`, installer и gitlink `Plugins/VoxelFree`.

## Проверенная структура проекта

```text
Content/DiggingPrototype/
├── BP_DiggableGround.uasset              # ранний отдельный voxel-эталон
├── L_DiggingTest.umap
├── DiggingFeature/
│   ├── Blueprints/
│   │   ├── BP_DigPlayer.uasset
│   │   ├── BP_DigPlayer_FirstPerson.uasset
│   │   ├── BP_DiggableGround.uasset      # ISM-эталон внутри feature
│   │   ├── BP_DiggableGround_Smooth.uasset
│   │   ├── BP_DigGameMode.uasset
│   │   ├── BP_DigGameMode2.uasset
│   │   └── WBP_DigCrosshair.uasset
│   ├── Materials/M_DiggableSoil.uasset
│   ├── L_DiggingFeature.umap
│   └── newLevel_Digging.umap
└── Voxel/
    ├── BP_VoxelDigPlayer.uasset
    ├── L_VoxelDigTest.umap
    └── Voxel_2/
        ├── Blueprints/BP_VoxelDigGameMode2.uasset
        ├── Blueprints/BP_VoxelDigPlayer2.uasset
        ├── Materials/M_VoxelGround_Prototype.uasset
        └── L_VoxelDig2.umap

Plugins/
├── Marketplace/VoxelPluginInstaller/
└── VoxelFree/
```

В проекте есть два разных asset с именем `BP_DiggableGround`. При проверке и изменениях всегда использовать полный Content Browser path.

## Dynamic Mesh prototype

### Runtime flow

```text
BP_DigPlayer_FirstPerson.TryDigSmooth
→ camera Line Trace с DigReachCm
→ ImpactPoint + ImpactNormal
→ BP_DiggableGround_Smooth.DigAtPoint
→ перевод точки и нормали в local space земли
→ создание и ориентация scaled sphere cutter
→ Apply Mesh Boolean: Subtract
→ Remove Small Connected Islands
→ Update Collision
```

В Construction Script земля создаётся как Dynamic Mesh box размером `500 × 500 × 300 cm` с локальным центром `Z = -150`. Включён complex-as-simple collision.

Проверенные editable параметры cutter и текущие class defaults:

| Переменная | Default | Назначение |
|---|---:|---|
| `CutterBaseRadiusCm` | `25` | Базовый радиус копка |
| `CutterShapeScale` | `(1, 1, 0.35)` | Сплющивание сферического cutter |
| `CutterPhiSegments` | `16` | Tessellation cutter |
| `CutterThetaSegments` | `24` | Tessellation cutter |
| `CutterInsetCm` | `5` | Смещение cutter внутрь поверхности |

Все пять переменных сейчас находятся в категории `Cutter`.

`BP_DigPlayer_FirstPerson.DigReachCm` находится в `Digging|Interaction`. Его **сохранённый class default равен `500 cm`**. Значение около `180 cm` использовалось при ручном прототипировании, но не является текущим сохранённым default в проверенном asset.

В `TryDigSmooth` остаётся prototype debug: рисование trace `ForDuration`, `HIT` / `MISS` через Print String и маленькая debug sphere в точке попадания.

### Cleanup связанных компонентов

Активная цепочка после Boolean:

```text
Apply Mesh Boolean
→ Remove Small Connected Islands
→ Update Collision
```

Проверенные пороги:

- `Min Volume = 0`
- `Min Area = 0`
- `Min Triangle Count = 20`

Операция удаляет только действительно отделённые connected components. Тонкий лепесток или игла, всё ещё соединённые с основной землёй несколькими треугольниками, остаются частью главного компонента.

### Материал земли

На сгенерированный Dynamic Mesh напрямую назначен `/Game/DiggingPrototype/DiggingFeature/Materials/M_DiggableSoil`.

Материал использует Megascans/Fab soil textures через world-aligned projection, чтобы новые Boolean-поверхности не зависели от стабильных authored UV:

- Base Color: `T_xdhhdhl_2K_B` через `WorldAlignedTexture`;
- Normal: `T_xdhhdhl_2K_N` через `WorldAlignedNormal`;
- Roughness: зелёный канал `T_xdhhdhl_2K_ORM`;
- Ambient Occlusion: красный канал `T_xdhhdhl_2K_ORM`;
- Metallic не подключён.

World-aligned texture size сейчас жёстко задан как `(200, 200, 200)`, а не вынесен в parameter. Для checkpoint это приемлемо; если материал переживёт следующий prototype, размер стоит параметризовать.

### First-person interaction, который нужно сохранить

`BP_DigPlayer_FirstPerson` — full-body first person, а не отдельные парящие руки:

- камера прикреплена к socket `FP_Camera` на `neck_02`;
- controller yaw вращает тело, вертикальный pitch остаётся на камере;
- при взгляде вниз игрок видит тело;
- голову не скрывали, потому что этот эксперимент ломал тень персонажа;
- `WBP_DigCrosshair` показывает центральное interaction ring;
- player отвечает за trace/range/UI и передаёт земле только hit data.

Этот interaction layer можно использовать повторно при смене editable-terrain backend.

## Почему Dynamic Mesh не выбран production-направлением

После большого числа пересекающихся Boolean Subtract появляются:

- острые треугольные иглы и тонкие лепестки земли;
- мелкие поверхности, мешающие дальнейшему Line Trace;
- висящие или почти отсоединённые куски;
- грязная и неравномерная topology;
- соседние сферические копки не всегда объединяются в органичную полость.

Это не только проблема shading. Последовательные Boolean постоянно меняют surface topology, тогда как желаемый результат лучше представлять изменениями объёмных данных с последующей локальной реконструкцией поверхности.

Dynamic Mesh сохраняется как:

- рабочий эталон и визуальный benchmark;
- fallback для малых или сценарных вырезов;
- проверенный источник camera trace, impact data, `DigReachCm`, настройки cutter и UI behavior.

Не усложнять realtime topology repair этого прототипа без нового теста с явным performance budget и exit criteria.

## Отклонённые эксперименты

Эти nodes больше не присутствуют в активном graph. Результаты ниже — наблюдения текущего прототипирования, а не гарантии автоматизированного benchmark.

### Global Uniform Remesh

Проверенная цепочка:

```text
Apply Mesh Boolean
→ Apply Uniform Remesh
→ Remove Small Connected Islands
→ Update Collision
```

Настройки:

- Target Type: Target Edge Length;
- Target Edge Length: `4 cm`;
- Reproject To Input Mesh: true;
- Smoothing Rate: `0`;
- Allow Flips, Splits и Collapses: true;
- Prevent Normal Flips: true;
- Prevent Tiny Triangles: true;
- Remesh Iterations: `5`.

Наблюдаемый результат: примерно **3 секунды hitch на один копок**. Отклонено для realtime, потому что после каждого edit перестраивался весь Dynamic Mesh.

### Local iterative smoothing

Проверенная цепочка:

```text
Apply Mesh Boolean
→ Select Mesh Elements in Sphere
→ Apply Iterative Smoothing to Mesh
→ Remove Small Connected Islands
→ Update Collision
```

Настройки:

- центр selection: Impact Point в local space;
- radius: примерно `35 cm`;
- Num Iterations: `2`;
- Alpha: `0.15`.

Наблюдаемый результат: hitch уменьшился примерно до **0.5 секунды**, но появились растянутые треугольники и иглы. Smoothing двигает существующие вершины, но не исправляет повреждённую topology и не создаёт качественную новую. Отклонено как финальное решение.

## Заметки исследования архитектур других игр

Сравнения ниже — **рабочие выводы текущего исследования и визуального анализа**. Это ориентиры и гипотезы, а не source-level подтверждение закрытой реализации игр.

Расширенная версия сравнений и технических выводов: [Digging Terrain Architecture Research](Research/DiggingTerrainArchitecture.md).

| Reference | Полезный вывод для ArcheoDig | Что не копировать вслепую |
|---|---|---|
| A Game About Digging A Hole | Округлые edits, слияние соседних копков, объёмный terrain, обработка floating fragments; главный reference по ощущению | Один выбор плагина не гарантирует такой же feel |
| Hydroneer | Изменяемую землю логично ограничить отдельными Dig Sites/parcels | Не распространять стоимость voxel/persistence на всю карту |
| Astroneer | Density-field edits показывают плавную локальную реконструкцию объёма | Ощущение «пылесоса земли» не соответствует работе лопатой |
| 7 Days to Die | Regular voxel grid + density/smoothing — предсказуемый Plan B | Грубая сетка неприемлема; нужны меньшие ячейки и ограниченные зоны |
| Deep Rock Galactic | Поверхность лучше локально строить из volumetric state, а не длинной цепочки Boolean; полезна идея удаления отсоединённого terrain | Не пытаться воспроизвести полный bespoke terrain backend на этапе prototype |
| Enshrouded | Нужно ограничивать editable area и объём сохранённых данных | Не считать persistence большого изменяемого мира дешёвым |
| Space Engineers | Chunking, collision rebuild и LOD boundaries — первичные ограничения | Не превращать каждый edit в глобальную операцию над mesh |

## Предлагаемая архитектура мира

```text
Обычный Unreal-мир
├── Landscape / static meshes
├── здания, дороги и окружение
└── Dig Site — ограниченный изменяемый объём
    ├── chunked density data
    ├── soil/material layers
    ├── Artifact Registry + отдельные Artifact Actors
    ├── persisted local edits
    └── локально перестраиваемые render mesh + collision
```

Предлагаемый edit pipeline:

```text
camera trace
→ impact position и surface normal
→ shovel/brush меняет малый density volume
→ пересечённые chunks помечаются dirty
→ перестраиваются только затронутые chunks, желательно async
→ обновляется local collision
→ по явным правилам проверяются/удаляются unsupported floating components
```

Граница Dig Site — главный механизм контроля scope: окружающий Unreal-мир остаётся обычным, а цену volumetric storage, meshing, collision и persistence платят только участки раскопок.

## Эксперимент Voxel Plugin Free Legacy

### Проверенное состояние на 2026-09-12

- `Plugins/VoxelFree` присутствует; Unreal показывает `VoxelFree` включённым и mounted по пути `/Voxel/`.
- Плагин идентифицируется как **Voxel Plugin Free Legacy** и содержит runtime/editor modules и example content.
- `Plugins/Marketplace/VoxelPluginInstaller` тоже присутствует и включён. Сохранить его до завершения эксперимента.
- `/Game/DiggingPrototype/Voxel/L_VoxelDigTest` и `BP_VoxelDigPlayer` сохранены как первый VoxelFree baseline.
- Текущий изолированный prototype находится в `/Game/DiggingPrototype/Voxel/Voxel_2/L_VoxelDig2`.
- В `L_VoxelDig2` есть автоматически создаваемый `VoxelWorld` с `Voxel Size = 10 cm`, `World Size In Voxel = 64`, `VoxelFlatGenerator`, `RGB` material config и `Marching Cubes` render type.
- `BP_VoxelDigPlayer2` содержит работающие TrimSphere и Surface Edit варианты. LMB сейчас вызывает `TryVoxelSurfaceDig2`.
- Из проверенных вариантов Surface Edit субъективно лучше соединяет соседние edits и меньше похож на последовательность сферических stamps. Это предпочтительный prototype candidate, а не production-решение.
- Полные graph parameters, разделение verified state/observations и unresolved issues записаны в [checkpoint 2026-09-12](DiggingFeature/Checkpoints/2026-09-12_VoxelSurfacePrototype.md).
- `M_VoxelGround_Prototype` назначен Voxel World, но сохранённый material graph пуст: expression nodes отсутствуют, `Base Color` не подключён. Height-based grass/dirt blend ещё не реализован и не подтверждён.
- Project logs подтверждают compile/load модулей Voxel под UE 5.8.

Legacy и актуальное поколения Voxel Plugin архитектурно различаются. Официальная legacy-документация описывает `AVoxelWorld` как контейнер voxel data и render mesh; migration guide объясняет другой manager/stamp подход Voxel Plugin 2. Первый эксперимент должен явно использовать установленный Legacy API: [Legacy Voxel World](https://docs.voxelplugin.com/1.2/core-systems/voxelworld/) и [migration notes](https://docs.voxelplugin.com/getting-started/migrating-from-legacy).

### Известный crash

В `Saved/Crashes` найден crash, прямо относящийся к editor path плагина:

```text
Cast of nullptr to VoxelDataAsset failed
FVoxelDataAssetEditorToolkit::InitVoxelEditor()
Plugins/VoxelFree/Source/VoxelEditor/Private/DataAssetEditor/
VoxelDataAssetEditorToolkit.cpp:123
```

Это не доказывает поломку runtime terrain editing, но является конкретным риском стабильности редактора.

### Historical checklist перед первым VoxelFree edit

> Этот список сохранён как план до реализации `Voxel_2`. Он больше не является текущим TODO: первые runtime edits, trace и сравнение brush variants уже выполнены. Актуальный следующий шаг приведён в конце [checkpoint 2026-09-12](DiggingFeature/Checkpoints/2026-09-12_VoxelSurfacePrototype.md).

- [ ] Добавить маленький Voxel World в `L_VoxelDigTest`.
- [ ] Проверить один runtime spherical/ellipsoidal dig edit.
- [ ] Переиспользовать существующие camera trace, `ImpactPoint`, `ImpactNormal` и range control.
- [ ] Сравнить форму одного копка с Dynamic Mesh checkpoint.
- [ ] Проверить чистое слияние нескольких соседних edits.
- [ ] Выполнить 10 последовательных edits и записать результат.
- [ ] Выполнить 100 последовательных edits и измерить hitch/frame impact.
- [ ] Проверить collision после edits.
- [ ] Проверить тоннель и копок в стене, а не только сверху вниз.
- [ ] Проверить маленькие и floating terrain fragments.
- [ ] Сравнить feel с A Game About Digging A Hole.
- [ ] Проверить save/load ограниченного Dig Site.
- [ ] Решить, является ли VoxelFree production-направлением или только prototype dependency.
- [ ] При отказе собрать custom bounded density-field prototype: сначала benchmark `5 × 5 × 3 m` при `10 cm`, затем сравнить с `15 cm`.
- [ ] Только после архитектурного решения привести Content/Docs/Plugins в окончательный порядок.

Exit criteria: форма edit, корректность collision, стабильность на 10/100 edits, максимальный hitch, тоннели, политика floating fragments, bounded persistence и поддерживаемость на целевой версии Unreal.

## Git и dependency hygiene

Главный repository хранит `Plugins/VoxelFree` как gitlink (`mode 160000`) на commit `7e64a89ce827b44a75c83a939e2c2e2e42bee61d`, но файл `.gitmodules` **отсутствует**. Вложенный repository чист; remote — `https://github.com/VoxelPlugin/VoxelPluginFreeLegacy.git`.

Следствие: свежий clone ArcheoDig не сможет восстановить dependency обычной командой submodule. Во время prototype ничего не менять разрушительно. После решения по voxel выбрать и документировать одну политику:

- оформить правильный git submodule;
- считать плагин исключённой внешней dependency с явной инструкцией установки;
- vendor нужные файлы плагина в главный repository с учётом лицензии.

Не удалять `VoxelPluginInstaller` до завершения эксперимента и решения по dependency policy.

## Decision record после architecture research

Принятые рабочие решения:

- основное направление — bounded volumetric/density Dig Sites внутри обычного Unreal world;
- для всех пяти биомов предпочтительна одна базовая terrain architecture;
- различия грунта задаются data-driven Soil Types, material data и специализированными behavior modules, а не отдельными terrain backends;
- bulk terrain остаётся единым; sand, frozen и rock behavior добавляются отдельными modules;
- первым biome-specific behavior после обычного cohesive soil проверяется sand relaxation;
- текущий prototype — **Voxel Surface Dig** в `/Game/DiggingPrototype/Voxel/Voxel_2/L_VoxelDig2`; следующий непосредственный шаг — завершить и проверить минимальный ground material, затем провести controlled benchmark Surface Edit;
- Voxel Plugin Free Legacy пока является только prototype backend, а не production dependency;
- gameplay не должен напрямую зависеть от VoxelFree API;
- обязательная граница слоёв: `Gameplay → Dig/Terrain abstraction → concrete terrain backend`;
- production fallback — собственный bounded chunked density field;
- первый кандидат mesher для custom prototype — Marching Cubes;
- artifacts хранятся отдельными Unreal Actors / Registry, а не внутри voxel material field;
- окончательную упаковку VoxelFree и repository cleanup отложить до решения по backend.

Research recommendations / prototype targets, **не утверждённые production constants**:

- первый production-oriented benchmark: Dig Site `5 × 5 × 3 m` при resolution `10 cm`;
- `15 cm` проверить как performance alternative;
- `20–25 cm` не считать основным quality target без отдельного визуального и gameplay-теста;
- первый кандидат chunk size для custom backend — `16³` cells.

Не решено:

- production terrain backend;
- окончательные voxel resolution и chunk size;
- async meshing/collision strategy;
- правила floating fragments;
- save-game format для изменённых Dig Sites;
- финальная VoxelFree dependency policy.
