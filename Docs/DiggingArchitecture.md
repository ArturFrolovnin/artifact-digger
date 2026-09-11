# ArcheoDig — checkpoint архитектуры копания

Дата checkpoint: **2026-09-11**

Проверенный HEAD до правок документации: `46371c4` (`add voxel`)

Проект: Unreal Engine **5.8**

Это основной актуальный документ по архитектуре копания. В нём факты, проверенные по репозиторию и Unreal assets, отделены от наблюдений прототипирования и проектных гипотез, которые ещё нужно проверить.

## Краткий статус

В проекте сохранены три полезных этапа разработки:

1. ранний ручной voxel / Instanced Static Mesh эталон;
2. рабочий Geometry Script / Dynamic Mesh Boolean прототип;
3. установленный Voxel Plugin Free Legacy и пустой тестовый уровень для следующего эксперимента.

Dynamic Mesh версия подтверждает работу interaction loop, full-body first person, проекции материала и обновления collision во время игры. Однако повторные Boolean Subtract постепенно ухудшают topology. Global remesh и local smoothing были проверены и отклонены для realtime.

Текущее решение: **заморозить Dynamic Mesh ветку как рабочий checkpoint и проверить ограниченные voxel volumes для Dig Sites**. Если Voxel Plugin Free Legacy не пройдёт требования по качеству, производительности или поддерживаемости, Plan B — собственная небольшая chunked density grid с ячейкой примерно `15–25 cm`, только внутри Dig Sites.

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
    └── L_VoxelDigTest.umap

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
    ├── buried artifacts
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

### Проверенное состояние

- `Plugins/VoxelFree` присутствует; Unreal показывает `VoxelFree` включённым и mounted по пути `/Voxel/`.
- Плагин идентифицируется как **Voxel Plugin Free Legacy** и содержит runtime/editor modules и example content.
- `Plugins/Marketplace/VoxelPluginInstaller` тоже присутствует и включён. Сохранить его до завершения эксперимента.
- `/Game/DiggingPrototype/Voxel/L_VoxelDigTest` существует.
- Проверенный уровень пока не зависит от content `/Voxel/`. Voxel World и digging logic **ещё не добавлены**.
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

### Checklist следующего эксперимента

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
- [ ] При отказе собрать prototype custom chunked density-grid Plan B с `15–25 cm` ячейкой в одном Dig Site.
- [ ] Только после архитектурного решения привести Content/Docs/Plugins в окончательный порядок.

Exit criteria: форма edit, корректность collision, стабильность на 10/100 edits, максимальный hitch, тоннели, политика floating fragments, bounded persistence и поддерживаемость на целевой версии Unreal.

## Git и dependency hygiene

Главный repository хранит `Plugins/VoxelFree` как gitlink (`mode 160000`) на commit `7e64a89ce827b44a75c83a939e2c2e2e42bee61d`, но файл `.gitmodules` **отсутствует**. Вложенный repository чист; remote — `https://github.com/VoxelPlugin/VoxelPluginFreeLegacy.git`.

Следствие: свежий clone ArcheoDig не сможет восстановить dependency обычной командой submodule. Во время prototype ничего не менять разрушительно. После решения по voxel выбрать и документировать одну политику:

- оформить правильный git submodule;
- считать плагин исключённой внешней dependency с явной инструкцией установки;
- vendor нужные файлы плагина в главный repository с учётом лицензии.

Не удалять `VoxelPluginInstaller` до завершения эксперимента и решения по dependency policy.

## Decision record

Принято:

- сохранить Dynamic Mesh prototype в простой рабочей конфигурации Boolean + island removal;
- не возвращать отклонённые global remesh и local smoothing chains;
- сохранить full-body camera/trace/UI interaction layer;
- ограничить изменяемую землю отдельными Dig Sites;
- следующим проверить Voxel Plugin Free Legacy в `L_VoxelDigTest`;
- держать custom chunked density field как Plan B;
- отложить окончательную упаковку плагина и repository cleanup до результата архитектурного эксперимента.

Не решено:

- production terrain backend;
- voxel resolution и chunk size;
- async meshing/collision strategy;
- правила floating fragments;
- представление soil layers и artifacts;
- save-game format для изменённых Dig Sites;
- финальная VoxelFree dependency policy.
