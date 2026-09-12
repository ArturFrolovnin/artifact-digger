# ArcheoDig — исследование архитектуры системы копания

**Дата исследования:** 2026-09-12
**Целевая версия:** Unreal Engine 5.8
**Цель:** выбрать практически реализуемую архитектуру изменяемого грунта для пяти биомов, слоёв пород, прогрессии инструментов и археологических находок.

---

# 1. Executive Summary

## Главный вывод

Для ArcheoDig наиболее разумна архитектура:

**один общий volumetric/density terrain backend + разные data-driven Soil Types + отдельные behavior-модули для разных типов грунта.**

То есть не пять независимых систем копания.

Архитектурно:

```text
Conventional Unreal World
│
├── Landscape / Static Meshes / PCG environment
│
└── Bounded Dig Site
    │
    ├── Density Field
    ├── Material / Soil Field
    ├── Chunk Manager
    ├── Artifact Registry
    ├── Terrain Mesher
    ├── Collision Manager
    │
    └── Soil Behaviors
        ├── Cohesive Soil
        ├── Loose / Sand
        ├── Mud
        ├── Frozen
        └── Rock / Volcanic
```

Различия между лесом, болотом, пустыней, ледником и вулканом должны в основном происходить **не на уровне terrain backend**, а на уровне:

* материала конкретной ячейки/объёма;
* hardness;
* допустимых инструментов;
* силы инструмента;
* размера и формы edit;
* скорости разрушения;
* cohesion;
* collapse behavior;
* fragment behavior;
* VFX/SFX;
* специальных объектов вроде корней, валунов и льда.

Это соответствует варианту **B: общий density backend + специализированные behavior modules**.

---

# 2. Что делать прямо сейчас

**Не писать собственный voxel engine.**

Следующий эксперимент должен использовать уже установленный **Voxel Plugin Free Legacy** как инструмент проверки самой игровой архитектуры.

Причины:

* текущая официальная ветка Legacy уже содержит правки под UE 5.8;
* README прямо говорит, что код должен собираться под UE 5.6, 5.7 и 5.8, и существуют бинарники для 5.8;
* у Legacy уже есть runtime edits;
* Blueprint API;
* асинхронные terrain edits;
* modified values;
* edited bounds;
* collision;
* сохранение изменённого voxel world.

При этом **не считать VoxelFree окончательным production backend**, пока он не пройдёт наши тесты.

В проекте уже зафиксирован editor crash внутри `FVoxelDataAssetEditorToolkit`, а сам Legacy остаётся старой архитектурой, хотя в 2026 году её подправили для UE 5.8. Это совместимость, но не доказательство production-стабильности. Текущий ArcheoDig checkpoint именно поэтому правильно считает VoxelFree экспериментом, а Dynamic Mesh — reference.

---

# 3. Plan A / Plan B

## Plan A — VoxelFree Legacy

Использовать VoxelFree для ответа на игровые вопросы:

* нравится ли нам voxel/density копание;
* достаточно ли качества поверхности;
* можно ли делать слои;
* насколько удобно менять материал;
* можно ли считать объём выкопанного материала;
* работают ли разные инструменты;
* выдерживает ли система 100–1000 edits;
* нормально ли collision обновляется;
* устраивает ли сохранение;
* можно ли реализовать особенности пяти биомов.

Если всё это проходит — Legacy потенциально можно оставить production backend.

## Plan B — собственный bounded density backend

Если VoxelFree провалится по:

* стабильности;
* производительности;
* архитектурным ограничениям;
* материалам;
* persistence;
* контролю над gameplay;

тогда писать **не полноценный voxel world engine**, а очень ограниченную систему специально для Dig Sites:

```text
DigSite
→ dense/chunked scalar density
→ material ID
→ dirty chunks
→ Marching Cubes
→ runtime render mesh
→ runtime collision
```

Это существенно меньшая задача, чем собственный Astroneer или Deep Rock Galactic.

---

# 4. Почему не Voxel Plugin 2 прямо сейчас

Современный Voxel Plugin 2 очень интересен долгосрочно.

В версии `2.0p8` появились:

* sparse chunk generation;
* улучшенный collision cooking;
* Render Chunk Size;
* ограничение числа background tasks;
* улучшения Nanite;
* metadata;
* Surface Types.

Но **актуальная 2.0p8 официально рассчитана на UE 5.6 и 5.7**, а не UE 5.8. Сам продукт всё ещё обозначается как beta и активно меняется.

Runtime sculpting отдельно отмечен разработчиками как experimental/первая итерация. Async edits есть, save/load есть, но gameplay API пока не позволяет удобно получить количество реально удалённого грунта, а physics/floating terrain не реализованы.

Кроме того, Legacy и Plugin 2 — **не эволюция одного API**, а фактически разные системы. Legacy saves, graphs и Blueprint logic напрямую не мигрируют.

Поэтому:

**Voxel Plugin 2 = watchlist.**

Не строить ArcheoDig вокруг него сейчас.

---

# 5. Dynamic Mesh: что с ним делать

Текущий Geometry Script / Dynamic Mesh prototype был полезен.

Он уже доказал:

* camera trace;
* `ImpactPoint`;
* `ImpactNormal`;
* ellipsoid cutter;
* body-based first person;
* runtime terrain edit;
* collision update;
* хорошее визуальное ощущение локальной выемки;
* world-aligned материал.

Текущая рабочая цепочка:

```text
TryDigSmooth
→ Line Trace
→ ImpactPoint + ImpactNormal
→ DigAtPoint
→ local transform
→ ellipsoid cutter
→ Boolean Subtract
→ Remove Small Connected Islands
→ Update Collision
```

и сохранённые cutter defaults:

```text
CutterBaseRadiusCm = 25
CutterShapeScale = (1, 1, 0.35)
CutterPhiSegments = 16
CutterThetaSegments = 24
CutterInsetCm = 5
```

Это полностью соответствует текущей документации ArcheoDig.

Но повторные Boolean edits портят topology, а уже проверенные:

* global remesh ≈ 3 s/edit;
* local smoothing ≈ 0.5 s/edit;

оказались непригодны.

Geometry Script в UE 5.8 действительно предоставляет runtime Dynamic Mesh operations и Boolean operations, но Epic всё ещё маркирует Geometry Script как Beta.

Поэтому правильная роль Dynamic Mesh:

**reference implementation + визуальный benchmark + tool-interaction prototype.**

Не основной terrain backend.

---

# 6. Главная архитектура ArcheoDig

Рекомендую разделить систему на четыре независимых слоя.

```text
Gameplay
↓
Dig Request API
↓
Soil / Biome Rules
↓
Terrain Backend
```

Gameplay вообще не должен знать:

* VoxelFree это;
* Dynamic Mesh;
* custom density;
* Marching Cubes;
* другой plugin.

Например:

```text
Player
→ Trace
→ Build DigRequest
→ IDiggableTerrain.ApplyDig()
```

## FDigRequest

Пример минимальной модели:

```text
ImpactPoint
ImpactNormal

ToolTag
ToolPower

BrushShape
Radius
Depth
ShapeScale

Precision
```

Опционально позже:

```text
ToolDamageType
Duration
Rotation
Falloff
```

Не нужно сразу хранить десятки параметров.

---

# 7. Ответ terrain backend

Backend должен возвращать не просто `Success`.

Например:

```text
FDigResult
{
    bTerrainChanged

    EditedBounds
    RemovedVolumeApprox

    RemovedMaterials[]

    ArtifactHits[]

    SurfaceMaterial
}
```

Это позволит gameplay сказать:

> Я ударил железной лопатой.

Terrain отвечает:

> Здесь плотная глина hardness 55.
> Лопата нанесла только 20% нужной силы.
> Убрано 150 см³ грунта.

Gameplay уже решает:

* звук;
* stamina;
* animation;
* опыт;
* повреждение инструмента;
* UI.

---

# 8. Особенно интересный плюс VoxelFree Legacy

Legacy API уже имеет концепцию **Modified Values** и **Edited Bounds**.

Документация прямо приводит mining как пример использования Modified Values: они позволяют определить, какие voxel values были изменены и сколько материала было удалено.

Но запись Modified Values имеет стоимость, поэтому её можно отключать. Там же есть `SetValueSphere` / `SetValueSphereAsync`, multithreading и edited bounds.

Для ArcheoDig это практически идеальный prototype API.

Например:

```text
Dig Request
→ SetValueSphereAsync
→ ModifiedValues
→ calculate removed volume/material
→ Artifact exposure
→ reward/progression
```

То есть VoxelFree позволяет проверить не только яму, но и саму **игровую экономику копания**.

---

# 9. Tool Model

Не советую делать систему:

```text
if Forest:
    if Shovel2...
```

Инструменты должны быть data-driven.

Минимальный Tool Definition:

| Поле             | Нужно       |
| ---------------- | ----------- |
| ToolTag          | обязательно |
| Power            | обязательно |
| DigShape         | обязательно |
| Radius           | обязательно |
| Depth / Scale    | обязательно |
| Precision        | обязательно |
| Speed            | gameplay    |
| DamageToArtifact | полезно     |
| DurabilityCost   | позже       |
| StaminaCost      | позже       |

Использование Gameplay Tags здесь очень удобно.

Например:

```text
Tool.Shovel
Tool.Shovel.Heavy

Tool.Pickaxe
Tool.Drill
Tool.IceAxe
Tool.Trowel
Tool.Brush
```

Gameplay Tags в UE предназначены именно для иерархических gameplay-категорий и условий.

---

# 10. Soil Material Model

Не нужно сразу моделировать 15 физических свойств.

## Нужны с первого prototype

```text
SoilId
Hardness
DigMultiplier

AllowedToolTags
PreferredToolTags

MaterialId
SurfaceMaterial

CollapseMode
FragmentMode
```

## Скорее всего понадобятся

```text
Cohesion
ArtifactDamageMultiplier
ParticleFX
SoundSet
```

## Добавлять только когда появится gameplay

```text
Moisture
Temperature
FractureThreshold
Compaction
Elasticity
```

## Сейчас лишние

Настоящие:

* plasticity tensor;
* pressure simulation;
* fluid saturation simulation;
* granular particle interaction;
* realistic geological stress.

Они не дадут соответствующего прироста gameplay.

---

# 11. Hardness и инструменты

Я бы не делал бинарное:

```text
Power < Hardness → нельзя копать
```

Лучше использовать кривую.

Например:

```text
Efficiency = ToolPower / SoilHardness
```

с clamps.

Условно:

```text
>= 1.0
нормальный копок

0.7–1.0
копок меньше и медленнее

0.3–0.7
маленькая царапина

< 0.3
только FX + минимальное повреждение
```

Тогда твоя прогрессия получается естественно.

Например:

```text
Starter shovel Power = 30

Forest Layer 1
Hardness 20
→ отлично

Layer 2
Hardness 35
→ уже тяжело

Layer 3
Hardness 60
→ почти царапает

Layer 4
Hardness 100
→ практически бесполезна
```

И при этом не требуется отдельная логика каждого слоя.

Игры давно используют похожее разделение tool/material эффективности. В 7 Days to Die инструменты имеют отдельные multipliers против earth, stone, wood и других материалов, а подходящий инструмент существенно увеличивает эффективность.

В DRG terrain materials имеют hardness 1–3, непосредственно определяющую количество ударов киркой. При этом игра сознательно **не моделирует tensile/structural integrity** всей пещеры.

Для ArcheoDig это очень хороший ориентир:

**hardness моделировать; настоящий rock mechanics simulator — нет.**

---

# 12. Один backend для всех биомов

Ответ: **да.**

Но не один behavior.

```text
Density Backend
│
├── NormalCohesiveBehavior
├── LooseSoilBehavior
├── SandRelaxationBehavior
├── FrozenBehavior
└── RockBehavior
```

Это даёт одну систему:

* chunks;
* save/load;
* collision;
* meshing;
* tools;
* artifacts.

А особенности грунта добавляются сверху.

Это значительно проще поддержки пяти независимых terrain implementations.

---

# 13. Биом №1 — Лес

Предлагаемая первоначальная структура:

| Layer | Материал                 | Gameplay                     |
| ----- | ------------------------ | ---------------------------- |
| 1     | перегной / topsoil       | мягкий, рыхлый               |
| 2     | loam / плотная земля     | обычная лопата               |
| 3     | clay / gravel subsoil    | сильная лопата / малая кирка |
| 4     | weathered rock / bedrock | кирка / бур                  |

Реальные soil profiles обычно разделяются примерно на organic/topsoil/subsoil/parent material/bedrock horizons, поэтому такая структура достаточно правдоподобна, даже если мы её упрощаем для игры.

### Особенность леса — корни

Корни **не стоит хранить внутри density field**.

Лучше:

```text
Terrain
+
Root Actors / Spline Meshes
```

Корень:

* имеет собственный collision;
* собственный hardness;
* режется/ломается отдельным инструментом;
* может блокировать excavation.

Это даст гораздо больше gameplay за существенно меньшую сложность.

---

# 14. Биом №2 — Болото / джунгли

Первоначально:

| Layer | Материал              | Gameplay                          |
| ----- | --------------------- | --------------------------------- |
| 1     | organic muck / peat   | мягкий, липкий                    |
| 2     | saturated mud         | легко копается, медленно работать |
| 3     | clay + roots          | плотнее                           |
| 4     | gravel/weathered rock | кирка                             |

Для hydric/wetland soil характерна длительная насыщенность водой и анаэробные условия верхних горизонтов.

Но **не нужно моделировать воду внутри density field в первой версии**.

Это очень резко увеличивает сложность:

```text
terrain edit
→ fluid propagation
→ surface extraction
→ water/terrain interaction
→ save
```

Первый вариант должен имитировать влажность через:

* material;
* sound;
* Niagara;
* footsteps;
* slower dig multiplier;
* sticky particles;
* puddle/water plane;
* gameplay drag.

Настоящее заполнение ямы водой можно исследовать позже как отдельную механику.

---

# 15. Биом №3 — Пустыня / степь

Предлагаемые layers:

| Layer | Материал            | Gameplay                  |
| ----- | ------------------- | ------------------------- |
| 1     | loose sand / dust   | очень легко, осыпается    |
| 2     | compacted sand      | обычная/улучшенная лопата |
| 3     | dry clay / caliche  | твёрдый hardpan           |
| 4     | sandstone / bedrock | кирка / бур               |

Для аридных почв действительно характерны слабый organic layer и плотные carbonate/caliche horizons.

## Самая интересная особенность — collapse

Не использовать миллионы simulated sand particles.

Предлагается:

```text
Dig
→ mark local dirty area
→ normal density removal
→ SandRelaxation pass
```

Relaxation может анализировать только небольшой объём рядом с выкопанной поверхностью.

Например:

```text
если solid voxel/sample
имеет слишком мало поддержки снизу
→ уменьшить density
→ перенести/добавить density вниз
```

Проводить максимум несколько iterations.

Это даст иллюзию осыпания.

Визуально добавить Niagara dust/sand.

---

# 16. Биом №4 — Frozen / Glacier

Предлагаемые layers:

| Layer | Материал                     | Gameplay      |
| ----- | ---------------------------- | ------------- |
| 1     | снег / seasonal frozen layer | лопата        |
| 2     | плотный снег / frozen soil   | мощная лопата |
| 3     | ground ice / permafrost      | ледоруб       |
| 4     | frozen bedrock               | кирка / бур   |

Permafrost geology естественно даёт удобную игровую модель: над постоянной мерзлотой существует active layer, который сезонно оттаивает/замерзает.

## Лёд

Не надо делать весь лёд через Chaos fracture.

Bulk terrain:

**density field.**

Fracture feel:

* decals;
* cracks;
* Niagara;
* sounds;
* occasional detached ice chunks.

Крупные специально подготовленные ледяные препятствия могут быть Geometry Collections.

Chaos Geometry Collections именно рассчитаны на заранее fractured rigid geometry и позволяют управлять разрушением через strain/fields.

---

# 17. Биом №5 — Вулкан

Предлагаемые layers:

| Layer | Материал                    | Gameplay             |
| ----- | --------------------------- | -------------------- |
| 1     | ash / loose tephra          | лопата               |
| 2     | compacted ash / tuff        | мощная лопата / pick |
| 3     | scoria / fractured basalt   | кирка                |
| 4     | massive basalt / solid lava | тяжёлая кирка / бур  |

USGS классифицирует volcanic ash, lapilli и blocks/bombs по размеру pyroclastic fragments; scoria сама по себе является пористой вулканической породой.

Вулкан — хороший кандидат для hybrid presentation:

```text
bulk terrain
= density field

крупный basalt boulder
= Static Mesh / Geometry Collection

мелкий debris
= Niagara / spawned meshes
```

Не нужно делать fracture каждого cubic centimeter.

---

# 18. Главное правило разных материалов

Пять биомов могут ощущаться совершенно по-разному при одном backend.

Например:

```text
Forest soil
high cohesion
smooth shovel cuts

Swamp mud
medium cohesion
slow resistance
heavy particles

Sand
low cohesion
post-edit relaxation

Ice
high hardness
small edits + crack FX

Basalt
very high hardness
small angular edits + debris
```

Именно **response на инструмент** создаст ощущение разных грунтов.

Не сам voxel algorithm.

---

# 19. Артефакты

Я **не рекомендую хранить сам артефакт как voxel material**.

Артефакт лучше оставить нормальным Unreal Actor:

```text
ArtifactActor
├── Static/Skeletal Mesh
├── Collision
├── Health / Condition
├── ArtifactData
└── ExposureState
```

Dig Site содержит:

```text
ArtifactRegistry
[
    ArtifactActor references
]
```

---

# 20. Как определить, что артефакт откопан

Простой и надёжный вариант:

вокруг артефакта создать несколько sampling points.

Например:

```text
top
bottom
front
back
left
right
+ дополнительные samples
```

Terrain backend проверяет density вокруг них.

```text
Exposure =
empty samples / total samples
```

Например:

```text
0–20%
скрыт

20–60%
частично найден

60–90%
нужна точная расчистка

>90%
можно извлечь
```

Это значительно проще, чем пытаться voxelize точную форму каждой находки.

---

# 21. Повреждение артефактов

Dig Request уже знает инструмент.

При overlap edit bounds с ArtifactActor:

```text
ToolPower
× ToolArtifactDamage
× distance/falloff
→ Artifact damage
```

Например:

```text
brush
damage = 0

trowel
damage = 0.1

shovel
damage = 0.4

pickaxe
damage = 1

drill
damage = 2
```

Это создаёт очень естественную археологическую механику:

**чем ближе к ценному объекту — тем аккуратнее инструмент.**

---

# 22. Разрешение voxel/density grid

Здесь исследование изменило предыдущую гипотезу.

Ранее рассматривалось:

**15–25 см.**

Но текущий cutter имеет:

```text
radius = 25 cm
diameter = 50 cm
```

При grid:

```text
25 cm → 2 cells на диаметр
20 cm → 2.5 cells
15 cm → 3.3 cells
10 cm → 5 cells
```

2–3 samples на форму лопаты слишком мало для хорошего smooth excavation.

Поэтому:

### Первый серьёзный кандидат

**10 см.**

### Performance fallback

**15 см.**

### 20–25 см

Оставить для:

* очень крупных инструментов;
* дальнего LOD;
* coarse experiments.

Не использовать как основной high-quality shovel terrain без проверки.

---

# 23. Расчёт памяти

Предположение:

```text
density = float32
material = uint8
```

без:

* mesh;
* collision;
* normals;
* metadata;
* allocator overhead;
* save history.

| Dig Site |  Cell | Cells | Raw density + material |
| -------- | ----: | ----: | ---------------------: |
| 5×5×3 m  | 10 cm |   75k |              ~0.38 MiB |
| 5×5×3    | 15 cm |   23k |              ~0.12 MiB |
| 5×5×3    | 20 cm |  9.4k |              ~0.05 MiB |
| 5×5×3    | 25 cm |  4.8k |              ~0.03 MiB |
| 10×10×5  | 10 cm |  500k |              ~2.46 MiB |
| 10×10×5  | 15 cm |  153k |              ~0.76 MiB |
| 10×10×5  | 20 cm | 62.5k |              ~0.32 MiB |
| 20×20×10 | 10 cm |    4m |              ~19.4 MiB |
| 20×20×10 | 15 cm |  1.2m |               ~5.9 MiB |
| 20×20×10 | 20 cm |  500k |              ~2.46 MiB |

Вывод очень важный:

**для bounded Dig Sites плотность сама по себе относительно дешёвая.**

Проблема скорее:

* triangulation;
* mesh buffers;
* collision cooking;
* allocations;
* synchronization;
* material data;
* repeated edits.

Это ещё один аргумент против premature sparse-octree complexity.

---

# 24. Какой Dig Site делать первым

Не `20×20×10`.

Первый production-oriented test:

# **5 × 5 × 3 m, 10 cm resolution**

Почему:

* хватает для нормальной ямы;
* можно проверить тоннель;
* можно проверить четыре слоя;
* можно спрятать артефакт;
* достаточно объёма для 1000 edits;
* легко профилировать;
* дешёво rebuild'ить.

После успеха:

# **10 × 10 × 5 m**

И только потом думать о 20×20×10.

---

# 25. Chunk size

Для собственного backend первым кандидатом считаю:

# **16³ cells**

При 10 cm:

```text
chunk world size = 1.6 m
```

5×5×3 site даст примерно:

```text
4 × 4 × 2
= 32 chunks
```

Это хороший масштаб для prototype.

`8³` создаёт слишком много chunk-management overhead.

`32³` даёт chunk ~3.2 m, и один маленький копок потенциально заставит перестраивать слишком большой объём.

Интересно, что Voxel Plugin Legacy исторически использует базовые chunks `32³` и LOD увеличивает пространственный размер chunks степенями двойки.

Но для нашего собственного **маленького bounded backend** мы не обязаны копировать их решение.

---

# 26. Marching Cubes vs Surface Nets vs Dual Contouring

## Marching Cubes

**Мой выбор для первого собственного prototype.**

Плюсы:

* хорошо изучен;
* простой;
* smooth;
* отлично подходит для земли;
* много references;
* просто local rebuild;
* легко понять и отладить.

Минус:

* плохо сохраняет идеально sharp edges.

Но ArcheoDig в основном копает:

* землю;
* песок;
* грязь;
* снег.

Поэтому это приемлемо.

---

## Surface Nets

Потенциально:

* меньше vertices;
* ровная поверхность;
* простая dual-like geometry.

Но ecosystem/examples для UE существенно слабее.

Проверять только если Marching Cubes даст очевидные проблемы.

---

## Dual Contouring

Преимущество:

* лучше сохраняет sharp features SDF;
* интересен для льда и камня.

Но реализация значительно сложнее, особенно:

* Hermite data;
* QEF solving;
* chunk seams;
* topology corner cases.

Современные работы по Dual Contouring по-прежнему подчёркивают преимущество метода именно для sharp features sampled signed-distance fields.

Для solo prototype это неправильная стартовая точка.

---

# 27. Recommendation

```text
Prototype mesher:
Marching Cubes

Future:
Dual Contouring only if
ice/rock quality demonstrably requires it
```

Визуальный характер камня дешевле сначала получать через:

* normals;
* material;
* noise in density;
* debris;
* decals;

а не менять весь mesher.

---

# 28. LOD

Для `5×5×3` и даже `10×10×5` Dig Site я бы вообще **не начинал с LOD**.

Это лишняя архитектурная сложность:

* transition meshes;
* cracks;
* collision mismatch;
* multiple mesh resolutions.

Если впоследствии Dig Sites станут намного больше, тогда уже появляется смысл в Transvoxel-подобном подходе. Transvoxel как раз предназначен для transition cells между разными voxel LOD resolutions.

Пока:

```text
near Dig Site
full resolution

far Dig Site
disable / static representation
```

---

# 29. Collision

Collision — один из главных performance risks.

VoxelFree уже умеет ограничивать high-resolution collision зонами возле invoker и рекомендует complex collision для voxel terrain, потому что он точно соответствует сложной поверхности.

Для собственного backend:

```text
Density edit
→ rebuild render mesh async

не обязательно сразу:
→ rebuild collision
```

Можно делать:

```text
rapid shovel inputs
→ merge requests

terrain visual update
→ immediately/asynchronously

collision
→ debounce 30–100 ms
```

При условии, что ощущения остаются корректными.

---

# 30. Async архитектура

Production pipeline должен выглядеть примерно так:

```text
Game Thread
DigRequest
   ↓
mark affected chunks dirty
   ↓
Worker Thread
apply density edits
   ↓
Worker Thread
rebuild meshes
   ↓
Game Thread
upload mesh
   ↓
async collision cook
```

Важно:

каждый chunk имеет `GenerationId`.

Если:

```text
job A started
player digs again
job B started
job A finishes
```

A нельзя применять поверх нового состояния.

```text
if CompletedGenerationId != CurrentGenerationId
    discard old result
```

Это предотвращает race/stale meshes.

---

# 31. Нельзя делать после каждого копка

Запрещённая production-архитектура:

```text
dig
→ iterate entire Dig Site
→ remesh entire Dig Site
→ recook entire collision
```

Именно такой класс проблемы уже проявился в Dynamic Mesh remesh experiment.

Правильно:

```text
brush AABB
→ intersecting chunks
→ + neighbour border
→ rebuild only them
```

---

# 32. Persistence

Я бы не начинал со списка всех Dig Operations.

Проблема edit log:

```text
10,000 shovel hits
= 10,000 commands
```

replay становится дорогим.

Не нужен и полный uncompressed world snapshot при каждом save.

Оптимальный вариант:

# modified-chunk snapshots

```text
DigSiteSave
├── Version
├── Seed
└── ModifiedChunks[]
    ├── ChunkCoord
    ├── DensityData
    └── MaterialData
```

Можно добавить compression.

VoxelFree уже хранит save в специальных compressed/uncompressed structs и интегрируется с Unreal SaveGame.

Сам plugin также оптимизирует память тем, что хранит только edited data и умеет упрощать density далеко от поверхности.

Это хороший reference для собственного backend.

---

# 33. Artifact save

Артефакт сохраняется отдельно:

```text
ArtifactId
Transform
Damage
Exposure
Collected
```

Terrain save не должен отвечать за lifecycle игровых предметов.

---

# 34. Floating terrain

Не нужно одно глобальное правило.

Правильно:

```text
Material
→ FragmentBehavior
```

Например:

| Material    | Detached piece           |
| ----------- | ------------------------ |
| mud         | collapse/delete          |
| normal soil | crumble/delete           |
| sand        | relaxation               |
| snow        | collapse                 |
| ice         | occasional falling chunk |
| basalt      | rock debris              |

---

# 35. Connected component detection

Не запускать flood fill всего Dig Site после каждого удара.

Лучше проверять только в локальном region после edit.

Даже проще — сначала вообще не делать structural simulation.

A Game About Digging A Hole является хорошим реальным примером: разработчики в патче 2025 года прямо упоминали изменение Voxel Plugin logic, при котором маленькие floating fragments земли стали **удаляться**, чтобы не висеть и не цеплять игрока.

Это подтверждает, что иногда игровой результат лучше настоящей физики.

---

# 36. Sand collapse

Три уровня сложности:

### Level 1 — VFX fake

После копка:

* particles;
* dust;
* звук.

Terrain не меняется.

### Level 2 — recommended

Local density relaxation.

Небольшая область над/вокруг excavation постепенно пересчитывается.

### Level 3

Настоящая granular simulation.

**Не рекомендуется.**

Начинать с Level 2.

---

# 37. Ice fracture

Также:

### Bulk volume

density.

### Visual cracking

material/decals/Niagara.

### Значимые крупные куски

Geometry Collection.

Chaos лучше использовать как специализированный subsystem, а не как terrain backend.

---

# 38. Rock

То же самое.

Не превращать каждый basalt voxel в rigid body.

```text
bedrock volume
= density

special exposed boulder
= Static Mesh / GC

tiny fragments
= Niagara
```

---

# 39. PCG

PCG не является системой excavation.

Его роль:

```text
biome decoration
roots
rocks
plants
surface props
artifact site decoration
```

UE PCG поддерживает partition/runtime generation, в том числе генерацию вокруг runtime generation sources.

То есть:

```text
Dig Site backend
≠ PCG

Environment around Dig Site
= excellent PCG use case
```

---

# 40. Niagara

Использовать очень активно для маскировки технической простоты.

Например:

* земля;
* песок;
* пыль;
* грязь;
* снежная крошка;
* ледяные осколки;
* volcanic ash;
* sparks от кирки.

Niagara — визуальный слой.

Не источник terrain truth.

---

# 41. World-aligned materials / RVT / WPO

World-aligned material из текущего prototype стоит сохранить концептуально.

Новая topology постоянно появляется, поэтому UV-based authoring неудобен.

Для bulk soil:

```text
World Position
→ tri/world-aligned texture
```

очень хорошо подходит.

WPO/displacement:

**только визуальный микродеталь.**

Не использовать как реальное копание, потому что collision и volume data не меняются.

---

# 42. Blueprint vs C++

## Оставить в Blueprint

* Player Trace.
* Tool switching.
* DigRequest construction.
* Interaction.
* UI.
* Audio/VFX.
* Biome selection.
* Data Assets.
* Gameplay progression.
* Artifact logic.
* high-level test logic.

## Если пишем custom backend — C++

* density arrays;
* chunk storage;
* brush evaluation;
* Marching Cubes;
* worker jobs;
* collision mesh data;
* connectivity checks;
* compression.

Это хорошая граница.

Blueprint остаётся местом, где ты реально видишь **gameplay architecture**, а низкоуровневая математика не превращает Blueprint в тысячу nodes.

---

# 43. Data Assets

`UPrimaryDataAsset` хорошо подходит для:

```text
DA_SoilType
DA_ToolType
DA_Biome
DA_DigSiteProfile
```

Primary Data Assets интегрированы с Asset Manager и могут грузиться/выгружаться как primary assets.

Пример:

```text
DA_Biome_Forest
│
├── Layer01 = DA_Soil_Humus
├── Layer02 = DA_Soil_Loam
├── Layer03 = DA_Soil_Clay
└── Layer04 = DA_Soil_Rock
```

Изменить баланс можно без изменения terrain code.

---

# 44. Layer representation

Не создавать:

```text
Layer1 Mesh
Layer2 Mesh
Layer3 Mesh
Layer4 Mesh
```

Правильно:

```text
Density
+
Material ID
```

Например:

```text
sample density = -0.8
material = Clay
```

или для cell/voxel:

```text
MaterialIndex = 3
```

Layer generation просто первоначально заполняет Material Field в зависимости от depth/noise.

---

# 45. Не делать идеально горизонтальные слои

Чтобы Dig Sites выглядели естественно:

```text
LayerDepth
+
low-frequency noise
+
local pockets
```

Например:

```text
humus: 0–35 cm ± noise
loam: next 80 cm
clay: irregular pockets
rock: deeper irregular surface
```

Это даст визуально красивое сечение.

---

# 46. Другая важная идея — inclusions

Не всё должно быть terrain material.

Dig Site может содержать:

```text
bulk terrain
+
inclusions
```

Inclusions:

* корни;
* валуны;
* buried wood;
* bones;
* ice blocks;
* basalt slabs;
* archaeology structures.

Они могут быть обычными Actors.

Это резко расширяет gameplay без усложнения voxel backend.

---

# 47. Другие игры — полезные выводы

## Astroneer

Это один из наиболее важных архитектурных references.

Разработчики описывали мир как grid из 3D voxels, где voxel хранит density, а smooth surface строится поверх density data. Они прямо отмечали, что такая система сложнее и тяжелее block-based Minecraft terrain.

Для ArcheoDig:

**density field — правильная mental model.**

Но нам не нужен planet-scale system.

---

## Deep Rock Galactic

Главный урок не rendering.

Главный урок:

**не симулировать то, что игроку не нужно.**

Terrain имеет hardness, влияющий на число ударов киркой, но structural integrity всего terrain не считается. Даже огромный кусок может висеть на небольшой перемычке.

Для ArcheoDig:

hardness — gameplay.

Полная физика грунта — нет.

---

## Enshrouded

Разработчики описывают workflow:

```text
rough authored 3D form
→ voxel world
→ hand-placed voxel stamps
→ detail до предела voxel resolution
```

Это хороший пример гибридного подхода, где voxel system не отменяет авторский worldbuilding.

Для ArcheoDig:

обычный Unreal world + специальные voxel Dig Sites — абсолютно нормальная архитектура.

---

## Space Engineers

Игра использует volumetric voxel terrain с разными материалами; voxel edits можно добавлять, удалять и заменять. Но большое количество сохранённых voxel changes ухудшает производительность, и серверы даже имеют инструменты reset edits.

Для ArcheoDig:

ещё один аргумент **не voxelize весь мир**.

---

## 7 Days to Die

Мир voxel-based, но базовый block — порядка `1×1×1 m`.

Очень полезный reference для:

* tool/material multipliers;
* progression;
* harvesting.

Но слишком грубый reference для формы археологической лопаты.

---

## A Game About Digging A Hole

Особенно интересный reference именно для ArcheoDig.

Разработчики Solarpunk прямо рассказывали, что экспериментировали с voxel terraforming, но сочли масштаб слишком большим для небольшой команды. Технологию затем использовали как основу маленькой игры A Game About Digging A Hole.

Это практически прямое подтверждение нашей стратегии:

**сильно ограничить scope изменяемого terrain.**

Не весь мир.

Конкретная digging-зона.

---

# 48. Plugin Comparison

| Решение                 | UE5.8                   | Runtime edit  | BP            | Save    | Контроль              | Риск              |
| ----------------------- | ----------------------- | ------------- | ------------- | ------- | --------------------- | ----------------- |
| VoxelFree Legacy        | Да                      | Да            | Хороший       | Да      | Хороший               | legacy/stability  |
| Voxel Plugin 2          | официально нет          | Experimental  | Да            | Да      | Потенциально отличный | beta/API churn    |
| Custom density          | Да                      | Полный        | через wrapper | свой    | Максимальный          | development cost  |
| Dynamic Mesh            | Да                      | Да            | Отличный      | свой    | Хороший               | topology          |
| RealtimeMeshComponent   | проверить               | renderer only | есть API      | —       | высокий               | 5.8 compatibility |
| ProceduralMeshComponent | Да                      | renderer only | Да            | —       | низкий уровень        | experimental      |
| Chaos                   | Да                      | fracture only | Да            | —       | узкая задача          | не terrain        |
| UnrealSandboxTerrain    | не подтверждено для 5.8 | Да            | C++ oriented  | зависит | средний               | licensing/version |

---

# 49. VoxelFree Legacy — подробная оценка

### Плюсы

* уже стоит в ArcheoDig;
* UE5.8 compile/binaries подтверждены;
* voxel runtime edits;
* sphere tools;
* async edits;
* Blueprint;
* material data;
* collision;
* save/load;
* Modified Values;
* Edited Bounds;
* multithread tools.
* commercial Free tier существует.

### Минусы

* Legacy architecture;
* большой старый codebase;
* у ArcheoDig уже был plugin editor crash;
* много исторических open issues;
* upgrade path на VP2 не совместим напрямую.

### Вердикт

**Лучший следующий prototype.**

Не автоматический production winner.

---

# 50. Voxel Plugin 2

### Плюсы

* современная архитектура;
* sparse generation;
* metadata;
* surface types;
* улучшенный collision;
* Render Chunk Size;
* stamps;
* хорошие перспективы.

### Минусы сейчас

* официально 5.6/5.7;
* beta;
* runtime edits всё ещё experimental;
* gameplay effects от removed terrain ограничены;
* floating physics нет;
* Legacy migration несовместима.

### Вердикт

**Следить за развитием. Не переключаться сейчас.**

---

# 51. Важная заметка по лицензии Voxel Plugin

Текущая главная страница говорит:

* Free — commercial;
* Pro — $349 и бюджет `<$200k`.

Но отдельная licensing documentation всё ещё описывает порог `$100k`.

То есть перед реальным коммерческим использованием Pro нужно **обязательно уточнить актуальные лицензионные условия у разработчиков**.

Для текущего prototype это значения не имеет.

---

# 52. RealtimeMeshComponent

Это не terrain engine.

Это потенциальная замена:

```text
ProceduralMeshComponent
```

для собственного custom backend.

RMC ориентирован на runtime-generated geometry и имеет собственный collision API.

Но его поддержку именно UE 5.8 нужно проверять локальной сборкой.

Поэтому:

```text
custom density prototype
→ сначала можно DynamicMeshComponent

потом:
→ compare RMC
```

Не делать renderer dependency до доказательства необходимости.

---

# 53. ProceduralMeshComponent

Epic всё ещё маркирует `UProceduralMeshComponent` как Experimental.

Поэтому не строил бы production architecture вокруг него, если есть более подходящие варианты.

---

# 54. Scoring Matrix

Оценка `1–5`.

Это **архитектурная оценка**, а не benchmark.

| Backend              | Quality | Biomes | Perf ceiling |  BP | UE5.8 | Solo cost | Production |
| -------------------- | ------: | -----: | -----------: | --: | ----: | --------: | ---------: |
| VoxelFree Legacy     |     4.5 |    4.5 |            4 |   5 |     4 |         4 |          4 |
| Custom density + MC  |       5 |      5 |            5 |   2 |     5 |         2 |          5 |
| Voxel Plugin 2       |     4.5 |      5 |          4.5 | 4.5 |     2 |         3 |          3 |
| Dynamic Mesh Boolean |       4 |      3 |            2 |   5 |     5 |         4 |          2 |
| UnrealSandbox-like   |       4 |      4 |          3.5 | 1–2 |     ? |         2 |        2–3 |

Главный конфликт:

**VoxelFree быстрее позволяет сделать игру.**

**Custom backend даёт лучший long-term control, но может съесть месяцы разработки.**

Поэтому нельзя выбирать custom только потому, что он «правильнее инженерно».

---

# 55. Рейтинги

## Лучший вариант для следующего prototype

1. **VoxelFree Legacy**
2. Custom micro density prototype
3. Existing Dynamic Mesh reference

## Самый перспективный production architecture

1. **bounded density terrain abstraction**
2. VoxelFree Legacy implementation, если проходит tests
3. custom density + Marching Cubes
4. Voxel Plugin 2 после появления UE5.8 support/stability

Здесь пункты 2/3 могут поменяться местами после benchmark.

## Максимальный контроль

1. Custom density
2. VoxelFree
3. VP2
4. Dynamic Mesh

## Самый простой для solo development сейчас

1. VoxelFree
2. Dynamic Mesh
3. VP2
4. Custom

## Самый большой engineering risk

1. Custom density engine
2. ранняя интеграция VP2
3. сторонние экспериментальные voxel plugins

---

# 56. Почему custom backend пока Plan B

Технически он очень привлекательный.

Но придётся самостоятельно решить:

* scalar field;
* brushes;
* materials;
* mesher;
* normals;
* chunk seams;
* async;
* collision;
* save;
* compression;
* floating fragments;
* debugging;
* serialization;
* version migration.

То есть можно легко перейти от:

> делаю игру про археологию

к:

> два года делаю voxel engine.

Это главный риск.

---

# 57. Performance Strategy

Главные правила:

### 1. Только bounded Dig Sites

Не voxelize world.

### 2. Только active sites имеют runtime mesh/collision

Остальные:

```text
saved data
+
cheap/static representation
```

### 3. Dirty chunks only

Никакого global rebuild.

### 4. Async meshing

Game thread только ставит запрос.

### 5. Collision отдельно

Не обязательно обновлять его каждый input frame.

### 6. Coalesce edits

Если лопата создаёт 5 edits за 100 ms:

```text
можно объединить dirty regions
```

### 7. Pool mesh buffers

Не создавать тысячи массивов каждый удар.

### 8. Version async jobs

Отбрасывать устаревшие результаты.

---

# 58. Profiling

Использовать:

```text
Unreal Insights
stat Unit
stat Game
stat SceneRendering
stat Memory
```

Для VoxelFree:

```text
stat Voxel
stat VoxelMemory
stat VoxelCounters
stat VoxelProcMeshMemory
```

Legacy documentation отдельно предлагает `stat Voxel`, memory/counter profiling и описывает multithreaded task pipeline.

Unreal Insights должен быть главным инструментом измерения game/render/worker thread событий.

---

# 59. Initial performance targets

Пока нет конкретного target PC, поэтому это **prototype gates**, не финальные requirements.

### Single dig

Цель:

```text
Game Thread hitch:
< 16.7 ms ideal
< 33 ms acceptable prototype
> 50 ms bad
```

### Visual edit latency

```text
<100 ms desirable
```

### Collision latency

```text
<100–150 ms
```

может быть допустима, если игрок не замечает mismatch.

### 100 edits

Не должно быть заметного постоянного роста edit time.

Например:

```text
average last 20 edits
не >20–25% медленнее
чем первые 20
```

### 1000 edits

* нет memory runaway;
* нет topology degradation;
* нет постоянного роста hitch;
* save/load остаётся рабочим.

---

# 60. Prototype Roadmap

## Experiment 0 — Reference baseline

Ничего не менять.

На Dynamic Mesh:

* 1 edit;
* 10;
* 100;

записать:

* визуальную форму;
* ощущения;
* cutter size;
* collision;
* screenshot/video;
* hitch.

Это baseline.

---

# 61. Experiment 1 — VoxelFree Basic Dig

## Цель

Доказать основной loop.

Карта:

```text
/Game/DiggingPrototype/Voxel/L_VoxelDigTest
```

Добавить маленький Voxel World.

Переиспользовать:

```text
BP_DigPlayer_FirstPerson
Line Trace
ImpactPoint
ImpactNormal
DigReachCm
```

Terrain edit:

```text
SetValueSphere / Async
```

или соответствующий runtime Sphere Tool.

VoxelFree предоставляет Blueprint/C++ tools, включая sphere edits и async versions.

### PASS

* edit появляется;
* collision совпадает;
* можно зайти в яму;
* соседние edits соединяются;
* нет очевидных артефактов.

### FAIL

* постоянные crashes;
* > 50 ms GT hitch даже на маленьком edit;
* collision систематически ломается;
* поверхность хуже Dynamic Mesh настолько, что gameplay не подходит.

---

# 62. Experiment 2 — Resolution comparison

Протестировать:

```text
10 cm
15 cm
20 cm
```

с cutter примерно:

```text
radius 25 cm
```

Смотреть:

* округлость;
* ступени;
* collision;
* edit speed;
* triangle count.

Мой prediction:

**10 cm визуально выиграет.**

15 cm может оказаться лучшим compromise.

---

# 63. Experiment 3 — 10 / 100 / 1000 edits

Автоматизированный тест.

Один и тот же pattern.

Замерить:

```text
frame time
GT
memory
voxel memory
edit latency
collision latency
```

Отдельно:

```text
Record Modified Values ON
OFF
```

потому что документация прямо предупреждает о дополнительной стоимости этого режима.

---

# 64. Experiment 4 — Layered Soil

Сделать только четыре материала.

Например лес:

```text
Humus
Loam
Clay
Rock
```

Проверить:

* material transitions;
* excavation между слоями;
* world-aligned material;
* material ID retrieval.

### PASS

Terrain edit может сказать gameplay:

> сейчас ты копаешь Clay.

Это критично.

---

# 65. Experiment 5 — Tool hardness

Два инструмента:

```text
Shovel Power 30
Pickaxe Power 80
```

Два материала:

```text
Soil Hardness 20
Rock Hardness 80
```

Проверить:

```text
shovel → soil = normal
shovel → rock = tiny/no edit
pickaxe → rock = normal
```

Если это удобно реализуется — основа всех пяти биомов готова.

---

# 66. Experiment 6 — Artifact

Один ArtifactActor.

Закопать его в Layer 2/3.

Проверить:

* terrain рядом;
* artifact collision;
* exposure sampling;
* shovel damage;
* trowel/brush;
* extraction condition.

### PASS

Terrain backend не требует специального voxelized artifact format.

---

# 67. Experiment 7 — Sand

Тот же backend.

Добавить:

```text
CollapseMode = Relaxation
```

После excavation сделать локальный pass.

Сначала буквально несколько итераций.

Сравнить:

```text
0
1
3
5 iterations
```

Измерить cost.

---

# 68. Experiment 8 — Frozen / Rock Hybrid

Проверить:

```text
density ice
+
Niagara debris
+
one Geometry Collection boulder
```

Ответить:

достаточно ли этого, чтобы terrain ощущался твёрдым без отдельного backend.

---

# 69. Experiment 9 — Save/Load

Создать:

```text
100 edits
save
reload map
load
```

Проверить:

* точность;
* размер save;
* load time;
* artifact state.

VoxelFree имеет готовый compressed save path, поэтому это можно проверить довольно рано.

---

# 70. Experiment 10 — Scale

Только после всего выше.

Перейти:

```text
5×5×3
→ 10×10×5
```

Повторить 100/1000 edits.

Если именно здесь всё начинает ломаться — тогда принимать архитектурное решение.

---

# 71. Когда отказаться от VoxelFree

Я бы остановил интеграцию, если произойдёт хотя бы одно из следующего:

* reproducible editor/runtime crashes в обычном workflow;
* невозможно надёжно связать terrain material с gameplay;
* collision edits дают неприемлемые hitch;
* 100–1000 edits постепенно деградируют;
* save data/restore ненадёжен;
* plugin API слишком сильно мешает artifact/soil architecture;
* UE5.8 updates требуют постоянного patching plugin source;
* необходимая функциональность оказывается Pro/недоступной/неподдерживаемой.

Тогда Plan B становится оправдан.

---

# 72. Custom prototype после отказа VoxelFree

Не повторять сразу всё.

Первый custom prototype должен быть буквально:

```text
5×5×3 m
10 cm cells
16³ chunks
float density
uint8 material

Sphere subtract
Marching Cubes
1 material
DynamicMeshComponent
collision
```

Без:

* save;
* artifacts;
* sand;
* biome;
* LOD;
* fancy materials.

Если это уже не выдерживает performance budget — custom направление можно остановить очень рано.

---

# 73. Итоговая рекомендуемая Architecture v1

```text
ADigSite
│
├── UDigTerrainBackend
│   ├── ApplyDig(FDigRequest)
│   ├── QueryMaterial()
│   ├── QueryDensity()
│   ├── Save()
│   └── Load()
│
├── UDigChunkManager
│
├── UArtifactRegistry
│
├── UBiomeConfig
│
└── USoilBehaviorManager
    │
    ├── Cohesive
    ├── Loose
    ├── Sand
    ├── Frozen
    └── Rock
```

Backend implementation:

```text
today:
VoxelFreeBackend

possible future:
CustomDensityBackend
```

Gameplay не меняется при замене.

---

# 74. Самое важное архитектурное решение

Если начать VoxelFree experiment напрямую из:

```text
BP_DigPlayer
→ Voxel Plugin nodes
```

мы создадим vendor lock-in.

Лучше уже в prototype иметь концептуальную границу:

```text
Player
→ Diggable interface
→ Voxel terrain actor/backend
```

Даже если это пока Blueprint function/interface.

Тогда замена Legacy на custom backend будет намного дешевле.

---

# 75. Что делать с пятью биомами

Не создавать их сейчас.

Сначала доказать:

```text
Layer
+
Hardness
+
Tool
+
Artifact
```

на одном Forest site.

Потом сделать **один специальный behavior**:

Sand.

Если:

```text
Forest + Sand
```

удаётся реализовать одним backend, архитектурная гипотеза практически доказана.

Frozen и Volcanic после этого будут намного проще.

---

# 76. Финальные ответы

## 1. Какой terrain backend сейчас наиболее перспективен?

**Bounded density/voxel terrain.**

Реализация для следующего prototype:

**Voxel Plugin Free Legacy.**

Не потому, что он уже признан production backend, а потому что он позволяет быстрее всего проверить реальные требования игры.

---

## 2. Какой fallback?

**Собственный bounded chunked scalar density field + Marching Cubes.**

Начальный кандидат:

```text
10 cm
16³ chunks
5×5×3 m
```

---

## 3. Один backend для пяти биомов?

**Да.**

Общий backend + разные Soil Types + behavior modules.

Не пять terrain engines.

---

## 4. Как реализовать различия грунта?

Через:

```text
Hardness
ToolPower
DigMultiplier
Cohesion
CollapseMode
FragmentMode
Brush response
Material
VFX/SFX
```

а не через пять разных mesh algorithms.

---

## 5. Как хранить 3–4 слоя?

**Один Density Field + Material/Soil ID.**

Initial generation задаёт material ID по глубине + noise.

---

## 6. Как связать инструмент и hardness?

Data-driven Tool Power против Soil Hardness.

Не binary check, а efficiency curve.

---

## 7. Как хранить артефакты?

Обычные Unreal Actors + ArtifactRegistry.

Terrain только окружает их.

Exposure определяется sampling density возле artifact.

---

## 8. Что реально симулировать?

### Реально

* volumetric excavation;
* hardness;
* material layers;
* local sand relaxation;
* collision;
* artifact exposure.

### Имитировать

* mud fluid dynamics;
* full granular sand;
* global soil structural integrity;
* ice fracture всей поверхности;
* millions of rock fragments.

Использовать:

* Niagara;
* decals;
* sound;
* Geometry Collections для редких крупных объектов.

---

## 9. Какой первый production-oriented Dig Site?

# **5 × 5 × 3 m @ 10 cm**

Затем сравнить 15 cm.

Потом:

**10 × 10 × 5 m.**

---

## 10. Какие эксперименты следующие?

```text
1. VoxelFree single dig
2. 10/15/20 cm resolution
3. 10/100/1000 edit benchmark
4. Four soil layers
5. Tool hardness
6. Artifact exposure
7. Sand relaxation
8. Frozen/rock hybrid
9. Save/load
10. Scale to 10×10×5
```

Именно в этом порядке.

---

## 11. Когда окончательно выбрать backend?

Когда backend проходит:

```text
visual quality
+
correct collision
+
1000 repeated edits
+
stable performance
+
4 materials/layers
+
tool hardness
+
artifact interaction
+
save/load
+
one special biome behavior
```

И при этом:

```text
GT hitch target <16.7 ms
prototype acceptable <33 ms
hard concern >50 ms

no progressive slowdown
no memory runaway
no collision corruption
no reproducible crashes
```

на целевом железе.

---

# 77. Итоговое архитектурное решение исследования

**Dynamic Mesh был правильным первым experiment, но неправильным production backend.**

**VoxelFree Legacy — правильный следующий experiment, но пока не доказанный production backend.**

**Voxel Plugin 2 сейчас слишком рано привязывать к UE5.8 ArcheoDig.**

**Собственный density backend технически лучше всего соответствует игре, но его нужно писать только тогда, когда готовый backend доказуемо мешает сделать игру.**

И самое важное:

> ArcheoDig не нужна универсальная физическая симуляция почвы.

Ей нужна очень хорошая **иллюзия разных типов грунта вокруг настоящего volumetric excavation**.

Если bulk terrain остаётся одним density backend, а лес, песок, лёд, грязь и basalt отличаются hardness, behavior, tools, particles, collapse и fragments, игрок будет воспринимать их как пять совершенно разных способов копания — при этом разработчику не придётся поддерживать пять terrain engines.

Это наиболее реалистичный путь для ArcheoDig как solo/small-team проекта.

