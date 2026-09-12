# Digging Feature

> **Checkpoint 2026-09-12:** этот файл сохраняет подробную историю ранних ISM и Dynamic Mesh прототипов. Актуальное состояние VoxelFree-прототипа зафиксировано в [`Checkpoints/2026-09-12_VoxelSurfacePrototype.md`](Checkpoints/2026-09-12_VoxelSurfacePrototype.md), а authoritative архитектурные решения — в [`../DiggingArchitecture.md`](../DiggingArchitecture.md). При расхождениях актуальным считается architecture checkpoint.

Полный terrain architecture research от 2026-09-12 вынесен в [`../Research/DiggingTerrainArchitecture.md`](../Research/DiggingTerrainArchitecture.md); актуальные принятые решения остаются в `DiggingArchitecture.md`.

Текущее состояние: Dynamic Mesh сохранён как frozen/reference checkpoint; активный VoxelFree-эксперимент находится в `/Game/DiggingPrototype/Voxel/Voxel_2/L_VoxelDig2`. Из проверенных voxel brushes предпочтительным кандидатом сейчас является `TryVoxelSurfaceDig2`, но это результат прототипа, а не production-решение.

Основная часть документа ниже — **historical snapshot этапа DiggingFeature / Dynamic Mesh**, сложившегося около документационного milestone `6fa2aea0a1ff09dedb6e2cb6e60ad02d90087b88` (`add readme`) и последующего first-person/cutter этапа. Формулировки «текущий» внутри historical sections относятся к тому этапу, а не к актуальному production-направлению проекта. Тестовый контур этого этапа находится в `/Game/DiggingPrototype/DiggingFeature`.

> В проекте есть два разных ассета с именем `BP_DiggableGround`: `/Game/DiggingPrototype/BP_DiggableGround` относится к более раннему отдельному voxel-тесту `L_DiggingTest`, а `/Game/DiggingPrototype/DiggingFeature/Blueprints/BP_DiggableGround` — к описанной здесь ветке `DiggingFeature`. При проверке и изменениях всегда сверяйте полный Content Browser path.

## Цель механики

Цель — получить копание грунта, похожее по ощущению на **A Game About Digging A Hole** и **Hydroneer**: игрок должен постепенно вынимать объём земли, а поверхность и физическая коллизия должны принимать форму получившейся ямы.

Главный ориентир — не разрушение заранее подготовленных кубов, а визуально плавное изменение цельной геометрии. На описанном историческом этапе сознательно решалась задача одного качественного копаемого участка; большой мир, загрузка чанков и сохранение изменений ещё не проектировались.

## Historical snapshot: статус Dynamic Mesh этапа

В репозитории сохранены два последовательных прототипа:

1. `BP_DiggableGround` на основе `Instanced Static Mesh` — рабочий и понятный voxel-эталон.
2. `BP_DiggableGround_Smooth` на основе `Dynamic Mesh`, Geometry Script и Boolean Subtract — основное экспериментальное направление **на момент этого snapshot**. Сейчас оно заморожено как working/reference checkpoint, а не выбрано production backend.

Историческая эволюция этой ветки выглядела так:

```text
Voxel / ISM
→ Smooth Dynamic Mesh + Boolean Subtract
→ проверка collision в пересекающихся cavities
→ ориентация cutter по ImpactNormal
→ full-body first person
→ экранный interaction ring
→ тест реального Quixel soil material
→ обнаружение UV-проблемы на Boolean-поверхностях
→ Instance Editable параметры cutter
```

Smooth-прототип уже умеет:

- построить цельный блок земли размером `500 × 500 × 300` см;
- определить точку попадания луча из камеры;
- перевести эту точку из World Space в локальные координаты земли;
- принять `ImpactPoint` и `ImpactNormal`;
- создать в точке попадания приплюснутый сферический cutter и ориентировать его по поверхности;
- вычесть cutter из геометрии земли;
- обновить collision после изменения mesh;
- повторными кликами создавать соседние округлые выемки, объединяющиеся в общую форму;
- сохранять физически проходимую collision-поверхность после большого числа пересекающихся вырезов;
- назначить импортированный Quixel Megascans soil material на `DigMesh`.

В рамках этого этапа игровым направлением стал отдельный `BP_DigPlayer_FirstPerson`: камера находится на socket скелета, тело остаётся видимым, а центральное кольцо показывает направление взаимодействия. Этот interaction layer остаётся полезным и для следующего terrain backend.

Это рабочий proof of concept одного небольшого участка, а не подтверждённое production-решение для большой карты.

## История прототипа

### 1. Voxel / Instanced Static Mesh prototype

Для ручной сборки первой версии был создан отдельный тестовый уровень:

`/Game/DiggingPrototype/DiggingFeature/L_DiggingFeature`

Основные Blueprint этой ветки:

- `/Game/DiggingPrototype/DiggingFeature/Blueprints/BP_DigPlayer`;
- `/Game/DiggingPrototype/DiggingFeature/Blueprints/BP_DiggableGround`;
- `/Game/DiggingPrototype/DiggingFeature/Blueprints/BP_DigGameMode`;
- `/Game/DiggingPrototype/DiggingFeature/Blueprints/BP_DigGameMode2`.

#### Генерация земли

Первый `BP_DiggableGround` строил объём из множества одинаковых кубов через `Instanced Static Mesh`. Общая схема `Construction Script`:

```text
Clear Instances
→ For Loop X
  → For Loop Y
    → For Loop Z
      → вычислить позицию voxel
      → Add Instance
```

Во время экспериментов использовались voxel примерно `50`, `25` и `20` см. Уменьшение размера делало ступени мельче, но быстро увеличивало число instances по трём измерениям.

#### Копание

Логика была разделена между игроком и грунтом:

```text
BP_DigPlayer
Left Mouse Button
→ TryDig
→ Line Trace из камеры
→ Break Hit Result
→ проверка типа Hit Actor
→ передача ImpactPoint земле

BP_DiggableGround
DigAtPoint(ImpactPoint)
→ Get Instances Overlapping Sphere
→ получить индексы найденных instances
→ Remove Instances
```

Архитектурный принцип появился уже здесь и сохраняется в smooth-версии:

> Игрок знает, **куда** копать. Земля знает, **как** копаться.

`BP_DigPlayer` не должен знать, из кубов, Dynamic Mesh или другой структуры сделан грунт. Он определяет точку воздействия и отправляет запрос конкретному типу копаемой земли.

#### Что показал voxel-прототип

Плюсы:

- простая, наглядная Blueprint-архитектура;
- реальные физические ямы, внутрь которых можно войти;
- `Instanced Static Mesh` заметно дешевле тысяч отдельных Actors;
- несколько экземпляров Blueprint могут иметь независимое состояние и копаться независимо.

Минусы:

- ямы остаются кубическими и ступенчатыми;
- уменьшение voxel резко увеличивает общее число instances;
- на соседних кубиках наблюдались визуальные артефакты и мерцание;
- скрытые внутренние voxel всё равно входят в структуру участка;
- подход не даёт желаемой цельной плавной поверхности.

Отдельно проверялась концепция чанков: несколько экземпляров одного Blueprint имели независимое состояние. Это показывает, что будущий мир можно разделить на `BP_DigChunk` или аналогичные участки. Однако chunk manager сознательно отложен: сначала нужно доказать качество и производительность одного smooth-участка.

### 2. Smooth Dynamic Mesh prototype — historical implementation snapshot

Коммит `48ae26f` добавил `BP_DiggableGround_Smooth` и на том этапе перевёл основное направление эксперимента на цельную изменяемую геометрию. После последующих исследований эта реализация была сохранена как frozen/reference checkpoint.

Используются:

- Geometry Script nodes;
- `Dynamic Mesh Component`;
- Boolean-операция `Subtract`;
- complex collision по актуальной геометрии.

В `BP_DiggableGround_Smooth` находятся два `Dynamic Mesh Component`:

| Компонент | Назначение |
| --- | --- |
| `DigMesh` | Настоящая видимая геометрия земли; принимает Boolean-изменения и имеет collision. |
| `DigCutter` | Служебный временный mesh инструмента вычитания; невидим и настроен как `NoCollision`. |

#### Начальная геометрия

`Construction Script` строит землю так:

```text
DigMesh
→ Get Dynamic Mesh
→ Append Box
```

Текущие тестовые параметры box:

- размеры: `500 × 500 × 300` см;
- `Origin = Center`;
- `Transform Location = (0, 0, -150)`.

Так как центр блока опущен на половину высоты, верхняя поверхность оказывается около `Z = 0` в локальных координатах Actor.

Для `DigMesh` включён режим `Enable Complex as Simple Collision`. Без него персонаж проваливался через Dynamic Mesh; после включения персонаж может стоять на поверхности тестового блока.

## Smooth Digging — historical snapshot реализации

### Запрос от игрока

Smooth-ветка вынесена в функцию `TryDigSmooth`. Она сохранена как в исходном `BP_DigPlayer`, так и в текущем `BP_DigPlayer_FirstPerson`. Старая `TryDig` остаётся voxel-эталоном и пока не должна удаляться.

```text
TryDigSmooth
→ получить Location компонента FollowCamera
→ получить Forward Vector камеры
→ рассчитать End луча
→ Line Trace By Channel
→ Break Hit Result
→ Hit Actor + Impact Point + Impact Normal
→ Cast To BP_DiggableGround_Smooth
→ DigAtPoint(ImpactPoint, ImpactNormal)
```

`ImpactPoint` — точка контакта trace с поверхностью в мировых координатах. `ImpactNormal` — направленная наружу нормаль поверхности в этой точке. Игрок не редактирует `DigMesh` напрямую: он передаёт оба значения публичной функции земли.

### Перевод координат

Сигнатура функции грунта:

```text
BP_DiggableGround_Smooth.DigAtPoint(
    ImpactPoint: Vector,
    ImpactNormal: Vector
)
```

`ImpactPoint` приходит из `Line Trace` в World Space, но геометрия cutter добавляется в локальном пространстве `DigMesh`. Поэтому точка обязательно преобразуется:

```text
DigMesh → Get World Transform
ImpactPoint + World Transform
→ Inverse Transform Location
→ LocalImpactPoint
```

Это позволяет корректно копать Actor, даже если он перемещён относительно начала мира. Если пропустить преобразование, cutter будет смещён при любом ненулевом transform грунта.

Нормаль также приходит в World Space и переводится отдельно:

```text
ImpactNormal
+ DigMesh World Transform
→ Inverse Transform Direction
→ Make Rot from Z
→ Rotation для Make Transform cutter
```

`Inverse Transform Direction` переводит направление из мирового пространства в локальное пространство `DigMesh`, не обращаясь с ним как с позицией. `Make Rot from Z` создаёт rotation, чья локальная ось Z смотрит вдоль полученной normal. Поэтому приплюснутый cutter повторяет ориентацию пола, стены или наклонной поверхности вместо сохранения одного мирового поворота.

Это техническая основа для управления глубиной выреза относительно поверхности, но сама ориентация не устраняет округлый характер текущих выемок.

### Создание cutter

Для каждого действия служебная геометрия пересоздаётся:

```text
DigCutter
→ Get Dynamic Mesh
→ Reset
→ Append Sphere Lat Long
```

В актуально сохранённом `BP_DiggableGround_Smooth` параметры cutter называются:

- `CutterBaseRadiusCm = 25` см;
- `CutterShapeScale = (1.0, 1.0, 0.35)`;
- `CutterPhiSegments = 16`;
- `CutterThetaSegments = 24`;
- `CutterInsetCm = 5` см;
- `Origin = Center`;
- `Location = LocalImpactPoint`;
- `Rotation` формируется из локальной `ImpactNormal`;
- `Scale` берётся из `CutterShapeScale`.

В ранней версии этого документа использовались старые имена `DigRadius`, `DigCutterScale`, `DigCutterPhi` и `DigCutterTheta`. Они относятся только к historical snapshot и больше не являются именами сохранённых Blueprint variables. Текущая категория пяти cutter-переменных — `Cutter`.

Это позволяет менять радиус, степень сплющивания и разрешение cutter через Details конкретного экземпляра земли без редактирования Blueprint graph. Текущая форма — scaled sphere, то есть эллипсоид, а не специальная геометрия лопаты.

Transform сферы собирается через `Make Transform`. `Reset` перед `Append Sphere Lat Long` обязателен: без него старые сферы накапливались бы в `DigCutter`, и следующий Boolean использовал бы не один новый cutter, а всю накопленную служебную геометрию.

### Boolean digging и collision

Изменение земли выполняет `Apply Mesh Boolean`:

```text
Target Mesh = DigMesh
Tool Mesh   = DigCutter
Operation   = Subtract

DigMesh - DigCutter = Excavated DigMesh
```

После Boolean вызывается:

```text
Update Collision
Target = DigMesh
```

Без `Update Collision` видимая яма и физическая поверхность могут разойтись: изображение уже изменится, а персонаж или trace продолжат взаимодействовать со старой формой.

## Что проверено в PIE

Для historical Dynamic Mesh milestone были зафиксированы следующие результаты ручной проверки в PIE:

- Dynamic Mesh box отображается;
- после включения `Enable Complex as Simple Collision` персонаж стоит на верхней поверхности;
- один клик создаёт округлую выемку;
- несколько кликов создают несколько выемок;
- соседние выемки объединяются в одну непрерывную форму;
- после большого числа пересекающихся сферических вырезов collision продолжает соответствовать изменённой форме;
- персонаж может заходить внутрь cavities, стоять на внутренних поверхностях и перемещаться среди нескольких пересекающихся полостей;
- характерное voxel-копание и мерцание соседних кубиков отсутствуют;
- на небольшом тестовом участке результат выглядит стабильнее старой voxel-версии;
- `Update Collision` включён в последовательность `DigAtPoint`;
- full-body first-person camera работает, тело видно при взгляде вниз, а yaw камеры разворачивает Character;
- interaction ring отображается по центру экрана и совпадает с направлением camera-based Line Trace;
- `MI_xdhhdhl` отображается на `DigMesh`;
- на Boolean-generated surfaces визуально проявляется сильное растяжение обычной UV-развёртки.

Пункт предыдущего плана «проверить collision внутри и вокруг нескольких перекрывающихся smooth Boolean cavities» выполнен. Это не означает, что уже проведены измеряемые stress tests на `100`/`500+` операций или доказана пригодность подхода для большого мира.

## Full-body First Person

Основная игра теперь развивается от первого лица. Копать с third-person camera оказалось неудобно, а будущая система инвентаря предполагает физическое взаимодействие с телом персонажа: при взгляде вниз игрок должен видеть torso, руки, ноги, пояс и будущие карманы.

Поэтому выбран **full-body FPS**, а не отдельная плавающая пара рук. Переход на arms-only подход не должен происходить без отдельного архитектурного решения.

### `BP_DigPlayer_FirstPerson`

Новый Blueprint создан отдельно от `BP_DigPlayer`, чтобы сохранить рабочую third-person/reference версию. Он унаследовал существующие функции и input:

- `Move`;
- `Aim`;
- `TryDig`;
- `TryDigSmooth`;
- camera-based digging `Line Trace`;
- Enhanced Input для движения, взгляда и прыжка.

`BP_DigGameMode2` использует `BP_DigPlayer_FirstPerson` как `Default Pawn Class`, а тестовый `L_DiggingFeature` ссылается на этот game mode.

### Socket `FP_Camera`

В Skeleton `/Game/Characters/Mannequins/Meshes/SK_Mannequin` создан socket `FP_Camera` с parent bone `neck_02`. Он вручную расположен в области глаз. В текущем asset его локальный transform относительно кости примерно равен:

- Location: `(14.4002, 12.8814, 0.2201)`;
- Rotation: `(0, 0, 0)`;
- Scale: `(1, 1, 1)`.

В `BP_DigPlayer_FirstPerson` компонент `FollowCamera` является дочерним для `Mesh`, прикреплён через `FP_Camera` и имеет нулевые relative Location/Rotation. `Use Pawn Control Rotation = true`.

Старый `CameraBoom` всё ещё присутствует в Blueprint как оставшийся компонент, но `FollowCamera` больше не является его дочерней. Не следует ошибочно считать boom текущим источником положения first-person camera.

### Вращение тела

Текущие настройки Character:

```text
Use Controller Rotation Pitch = false
Use Controller Rotation Yaw   = true
Use Controller Rotation Roll  = false

Character Movement:
Orient Rotation to Movement = false
```

Горизонтальный yaw теперь разворачивает весь Character вместе с камерой. Вертикальный pitch остаётся камерным и не наклоняет целиком тело. Без controller yaw камера могла повернуться относительно неподвижного тела и фактически посмотреть персонажу в шею.

### Эксперимент со скрытием головы

Проверялся вариант `BeginPlay → Hide Bone By Name(head)`. Он убирал голову из локального first-person view, но одновременно делал тень персонажа безголовой, поэтому был отменён. В текущем Event Graph узел `Hide Bone By Name(head)` ещё существует, но не подключён к execution chain и не выполняется.

Сейчас голова остаётся видимой частью full-body mesh, а socket настроен так, чтобы она не перекрывала обзор. Не следует снова включать `Hide Bone By Name(head)` как окончательное решение без сохранения корректной full-body shadow. Возможное будущее решение — отдельное first-person представление или отдельная shadow representation, но это не текущий приоритет.

## Interaction ring

`/Game/DiggingPrototype/DiggingFeature/Blueprints/WBP_DigCrosshair` — минимальный индикатор точки взаимодействия, а не оружейный crosshair.

```text
WBP_DigCrosshair
└─ Canvas Panel
   └─ Text Block: "○"
```

Text Block закреплён по центру Canvas с alignment `(0.5, 0.5)`, размером slot `24 × 24`; текущий размер шрифта — `20`. В `BP_DigPlayer_FirstPerson` виджет создаётся и добавляется во viewport из `Event BeginPlay`:

```text
Event BeginPlay
→ Create WBP_DigCrosshair Widget
→ Add to Viewport
```

Кольцо проверено в PIE: оно находится в центре и соответствует направлению camera-based Line Trace. Это временный прототип; позже Text `○` можно заменить texture- или material-based ring.

## Fab и материал грунта

### Historical snapshot: Fab import workflow

На момент этого этапа в локальной установке UE `5.8` был включён Fab UE Plugin (`Engine/Plugins/Fab`, версия `0.0.15`), а импорт выполнялся так:

```text
найти asset на Fab website
→ сохранить в My Library
→ открыть Fab внутри Unreal Editor
→ Add to Project
```

Так разработчик может импортировать конкретный рекомендованный материал из своей Fab Library непосредственно в проект.

### Quixel Megascans Soil Ground

Для визуального теста импортирован **Soil Ground** от Quixel Megascans:

- Fab listing/import id: `1e20f0ed-b2ce-46db-8aaa-54d10f56e975`;
- Content root: `/Game/Fab/Megascans/Surfaces/Soil_Ground_xdhhdhl`;
- Material Instance: `/Game/Fab/Megascans/Surfaces/Soil_Ground_xdhhdhl/Medium/xdhhdhl_tier_2/Materials/MI_xdhhdhl`;
- textures: `T_xdhhdhl_2K_B`, `T_xdhhdhl_2K_N`, `T_xdhhdhl_2K_ORM`;
- parent material: `/Game/Fab/Materials/Standard/M_MS_Srf`.

Fab также импортировал shared Materials, Material Functions, Material Parameter Collection и default textures. Эти зависимости сознательно не очищались: `MI_xdhhdhl` ссылается на master material и свои textures, а master material использует общую Megascans infrastructure.

### Historical snapshot: прямое назначение Fab Material Instance

На этом раннем этапе обычный `Override Materials` slot в Details не оказался удобным для `Dynamic Mesh Component`, поэтому `MI_xdhhdhl` назначался в `BP_DiggableGround_Smooth` через Blueprint после создания box и настройки collision:

```text
Construction Script
→ Append Box
→ Enable Complex as Simple Collision
→ Set Override Render Material
   Target   = DigMesh
   Material = MI_xdhhdhl
```

Это описание сохранено как история эксперимента. В актуально сохранённом Construction Script вместо прямого `MI_xdhhdhl` назначается проектный материал `M_DiggableSoil`.

### UV-проблема Boolean-поверхностей

После нескольких `Boolean Subtract` стало заметно, что обычная UV-based проекция Megascans плохо переносится на вновь созданные поверхности:

- верхняя исходная поверхность выглядит приемлемо;
- texture на cavities сильно растягивается;
- появляются радиальные/star-like patterns;
- внутренние стенки имеют нестабильную развёртку.

Boolean создаёт новую геометрию, для которой нет подходящей устойчивой UV-развёртки исходного box. На этом этапе следующим планировался собственный `M_DiggableSoil` с World Aligned / Triplanar projection:

```text
Base Color  → WorldAlignedTexture
Normal      → WorldAlignedNormal
Roughness/AO→ согласованная world-space projection
Scale       → настраиваемый parameter
```

Этот пункт исторического плана **выполнен**: `/Game/DiggingPrototype/DiggingFeature/Materials/M_DiggableSoil` существует и назначается на `DigMesh`. Он использует `WorldAlignedTexture` для Base Color и ORM, `WorldAlignedNormal` для Normal, а Roughness/AO читает из packed texture. Texture size пока жёстко задан как `(200, 200, 200)`. Точное актуальное состояние материала зафиксировано в [`../DiggingArchitecture.md`](../DiggingArchitecture.md).

## Historical snapshot: архитектура и ответственность Dynamic Mesh ветки

### `BP_DigPlayer` и `BP_DigPlayer_FirstPerson`

Отвечает за:

- получение input;
- работу с `FollowCamera`;
- направление и длину `Line Trace`;
- чтение `Hit Result`;
- определение `ImpactPoint` и `ImpactNormal`;
- проверку типа объекта;
- запрос `DigAtPoint`.

Не должен создавать cutter, выполнять Boolean или напрямую изменять Dynamic Mesh земли.

На этом этапе `BP_DigPlayer_FirstPerson` стал основным вариантом игрока; исходный `BP_DigPlayer` был сохранён как third-person/reference checkpoint. Full-body interaction layer по-прежнему сохраняется, но больше не означает выбор Dynamic Mesh как production backend.

### `BP_DiggableGround_Smooth`

Отвечает за:

- исходную форму грунта;
- владение `DigMesh` и `DigCutter`;
- перевод мировой точки и normal воздействия в локальные координаты;
- форму и разрешение cutter;
- Boolean-операцию;
- обновление collision;
- непосредственное изменение земли.

Такое разделение позволяет менять внутреннюю реализацию грунта, не переписывая прицеливание игрока. На описанном этапе использовался прямой `Cast To BP_DiggableGround_Smooth`; идея общего Blueprint Interface сохраняется только как историческая заметка, а не как текущий приоритет.

## Historical decision: почему Dynamic Mesh был выбран вместо маленьких voxel

Уменьшение voxel лечит только размер ступеней, но не фундаментальную дискретность поверхности. Одновременно число элементов растёт по трём измерениям: уменьшение линейного размера ячейки вдвое требует примерно в восемь раз больше voxel для того же объёма.

Dynamic Mesh даёт:

- одну цельную поверхность вместо набора видимых кубов;
- настоящее изменение геометрии;
- округлые и объединяющиеся выемки;
- collision, соответствующий изменённой форме после обновления.

Однако Boolean по Dynamic Mesh тоже имеет стоимость. Уже тогда не было доказано, что схема выдержит большую территорию, длительную сессию и сотни вырезов. На момент snapshot Dynamic Mesh был предпочтительным направлением исследования; после тестов topology cleanup он был заморожен как reference, а не принят как production architecture.

## Historical snapshot: ограничения Dynamic Mesh этапа

- Cutter остаётся scaled sphere / ellipsoid; актуальные сохранённые параметры — `CutterBaseRadiusCm = 25`, `CutterShapeScale = (1, 1, 0.35)`, `CutterPhiSegments = 16`, `CutterThetaSegments = 24` и `CutterInsetCm = 5`.
- Копание визуально всё ещё состоит из округлых «укусов».
- Нет shovel-specific cutter shape.
- Нет отдельного независимого `DigDepth`; позднее добавленный `CutterInsetCm` задаёт только offset вдоль `ImpactNormal`.
- Обычный UV-based Megascans material растягивался на Boolean-generated surfaces; позднее это обошли через world-aligned `M_DiggableSoil`.
- `WBP_DigCrosshair` пока использует prototype Text `○`.
- Full-body first person остаётся прототипом; clipping и представление тела ещё требуют дальнейшей игровой проверки.
- В smooth-ветке нет удержания ЛКМ с ограничением частоты.
- Нет `DigInterval` для smooth-копания.
- На момент snapshot не было отдельного законченного `DigReach`; позднее появился `DigReachCm` с сохранённым class default `500 cm`.
- Нет benchmark для `10`, `100` и `500+` последовательных Boolean.
- Не измерен рост числа triangles после повторных вырезов.
- Не измерена стоимость `Update Collision` после роста геометрии.
- На момент snapshot remesh/smoothing ещё не были проверены; позднейшие realtime-тесты дали неприемлемый hitch/артефакты, после чего экспериментальные nodes удалили из активного graph.
- Нет chunk manager и потоковой загрузки участков.
- Нет сохранения выкопанной геометрии.
- Нет слоёв `Dirt / Clay / Stone` и различной hardness.
- Нет ресурсов, руды и выдачи предметов за копание.
- Нет законченной системы инструментов.
- Нет частиц, вылетающей земли, decal и звуков.
- `M_DiggableSoil` остаётся prototype material, а не production-ready решением.
- Не подтверждена пригодность реализации для репликации или multiplayer.

## Historical plan дальнейшей разработки — устарел

> Этот список сохраняется как план, существовавший в конце Dynamic Mesh этапа. Он **не является текущим TODO**: `M_DiggableSoil`, `CutterInsetCm` и `DigReachCm` уже появились, remesh/smoothing были проверены и отклонены, а Dynamic Mesh polishing остановлен. Актуальное решение и следующий короткий checklist находятся только в [`../DiggingArchitecture.md`](../DiggingArchitecture.md).

Исторический приоритет работ:

1. Создать `M_DiggableSoil` из импортированных Soil Ground textures с World Aligned / Triplanar projection.
2. Проверить texture density, normal и roughness на плоском верху, вертикальной стороне и нескольких Boolean cavities.
3. На читаемом материале настроить `DigRadius` и `DigCutterScale` через Instance Editable параметры. Это старые имена; сейчас им соответствуют `CutterBaseRadiusCm` и `CutterShapeScale`.
4. Добавить независимый `DigDepth` или cutter offset внутрь земли вдоль `ImpactNormal`.
5. Спроектировать менее сферическую, shovel-like форму cutter.
6. Оценить несколько соседних cuts как единую естественную выемку.
7. При необходимости заменить Text `○` на texture-/material-based interaction ring.
8. Добавить удержание ЛКМ и параметр `DigInterval`.
9. Ввести отдельный `DigReach`, не смешивая допустимую дальность взаимодействия с длиной `Line Trace`.
10. Провести stress test на `10`, `100` и `500+` Boolean, измерить время операции и FPS.
11. Измерить рост числа triangles и стоимость `Update Collision`.
12. Только если измерения требуют этого, добавить remesh, simplification или другую стратегию ограничения сложности mesh.
13. Лишь после проверки и benchmark одного участка вернуться к chunks, `DigWorld`, загрузке/выгрузке и сохранению изменений.

## Полезные понятия

### Actor

Самостоятельный объект, который можно разместить на уровне. Здесь `BP_DigPlayer` и экземпляр `BP_DiggableGround_Smooth` являются Actors с разной ответственностью.

### Component

Часть Actor, добавляющая геометрию, коллизию, камеру или другое поведение. `DigMesh`, `DigCutter` и `FollowCamera` — компоненты соответствующих Blueprint.

### Instanced Static Mesh

Компонент, эффективно рисующий много экземпляров одного Static Mesh. В первом прототипе он позволял хранить землю как множество одинаковых кубов без отдельного Actor на каждый куб.

### Instance

Один экземпляр mesh внутри `Instanced Static Mesh Component`. Voxel-копание находило instances в сфере и удаляло их по индексам.

### Construction Script

Blueprint-граф, формирующий Actor при его создании или изменении в редакторе. В voxel-версии он создавал сетку кубов, а в smooth-версии — начальный box в `DigMesh`.

### For Loop

Blueprint-цикл по диапазону целых чисел. Три вложенных цикла использовались для перебора координат X/Y/Z voxel-сетки.

### Vector

Тройка чисел X/Y/Z, описывающая позицию, направление или размер. `ImpactPoint` и `LocalImpactPoint` в этой механике представлены Vector.

### World Space

Общая система координат уровня. `Line Trace` возвращает `ImpactPoint` именно в World Space.

### Local Space

Система координат относительно конкретного Actor или Component. Cutter добавляется в локальную геометрию `DigMesh`, поэтому мировую точку нужно преобразовать.

### Transform

Комбинация Location, Rotation и Scale. `Get World Transform` и `Inverse Transform Location` связывают мировые координаты попадания с локальными координатами земли.

### Line Trace

Лучевой запрос, который ищет первое пересечение по заданному collision channel. `BP_DigPlayer` пускает его из камеры, чтобы определить место копания.

### Hit Result

Структура с результатом попадания trace: Actor, Component, точка, нормаль и другие данные. Здесь из неё важны прежде всего `Hit Actor` и `Impact Point`.

### Impact Point

Фактическая мировая точка контакта луча с поверхностью. Она передаётся из игрока в `DigAtPoint`.

### Impact Normal

Направление, перпендикулярное поверхности в точке попадания. Оно передаётся вместе с `ImpactPoint` и используется для ориентации локальной Z-оси cutter.

### Inverse Transform Direction

Преобразует направление из World Space в Local Space без применения translation. Здесь переводит `ImpactNormal` в координаты `DigMesh`.

### Make Rot from Z

Строит rotation так, чтобы его ось Z совпала с заданным направлением. Благодаря этому сплющенный cutter ориентируется по поверхности.

### Cast

Проверка и получение ссылки конкретного Blueprint-типа. `Cast To BP_DiggableGround_Smooth` позволяет вызвать функцию smooth-грунта только при попадании в нужный Actor.

### Function

Именованный Blueprint-граф с входами и выходами. `TryDigSmooth` определяет цель, а `DigAtPoint` выполняет изменение земли.

### Dynamic Mesh

Mesh, геометрию которого можно создавать и менять во время работы. `DigMesh` хранит текущее состояние выкопанного участка.

### Geometry Script

Набор Unreal Engine API и Blueprint nodes для процедурной работы с геометрией. Здесь он используется для `Append Box`, `Append Sphere Lat Long` и `Apply Mesh Boolean`.

### Boolean Subtract

Операция вычитания объёма одного mesh из другого. Сфера `DigCutter` вычитается из `DigMesh`, формируя выемку.

### Complex as Simple Collision

Режим, в котором сложная геометрия mesh используется как игровая collision-поверхность. Он дал персонажу возможность стоять на текущем Dynamic Mesh, но его стоимость ещё нужно измерить.

### Update Collision

Явное обновление физического представления после изменения геометрии. Вызов выполняется после каждого Boolean, чтобы collision соответствовал видимой яме.

## Git milestones

### `dc5abe3fc8010f443ea89281b4cb91556de78f63`

`add manual voxel digging prototype`

Первая вручную собранная реализация ветки `DiggingFeature`: тестовый уровень, `BP_DigPlayer`, game modes и voxel-земля на `Instanced Static Mesh`.

### `48ae26f23da91e08a8de7ccffa577cbf118abd5d`

`add smooth dynamic mesh excavation`

Добавлен `BP_DiggableGround_Smooth`; `BP_DigPlayer` и `L_DiggingFeature` обновлены для эксперимента с Dynamic Mesh, Geometry Script и Boolean excavation.

### `6fa2aea0a1ff09dedb6e2cb6e60ad02d90087b88`

`add readme`

Документационный milestone с первым подробным `README.md` и `AI_CONTEXT.md`. Это был Git `HEAD` на момент того исторического обновления документации; full-body FPS, surface-aware cutter, crosshair и Fab/Soil Ground отражали более новое на тот момент состояние Unreal assets.

## Основание документации

Первоначальное состояние было сверено с Git history и Unreal assets через read-only Unreal MCP. Для актуального checkpoint повторно проверены ключевые Blueprint graphs, параметры cutter и назначение материала; итог находится в [`../DiggingArchitecture.md`](../DiggingArchitecture.md).

Технические нюансы historical snapshot:

- в старой версии member names `DigCutterScale `, `DigCutterPhi `, `DigCutterTheta ` и вход `ImpactNormal ` содержали завершающий пробел; актуальные cutter variables переименованы в `CutterBaseRadiusCm`, `CutterShapeScale`, `CutterPhiSegments`, `CutterThetaSegments` и `CutterInsetCm`;
- `CameraBoom` физически остаётся компонентом `BP_DigPlayer_FirstPerson`, хотя `FollowCamera` уже прикреплена напрямую к `Mesh`;
- `Hide Bone By Name(head)` остаётся неподключённым узлом и не выполняется;
- текущий `TryDigSmooth` всё ещё содержит prototype debug drawing и `HIT`/`MISS` Print String.

Точный текстовый diff Blueprint-графов через Git недоступен, поскольку Unreal assets хранятся как бинарные Git LFS-файлы. При дальнейшей работе фактический граф в Unreal Editor или через Unreal MCP имеет приоритет над этим документом.
