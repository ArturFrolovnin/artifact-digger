# Digging Feature

Документ описывает текущее состояние механики копания в Unreal Engine 5-проекте **ArcheoDig / artifact-digger**. Последний зафиксированный документационный коммит — `6fa2aea0a1ff09dedb6e2cb6e60ad02d90087b88` (`add readme`); описанные ниже последующие изменения проверены в текущих Unreal assets. Основной тестовый контур находится в `/Game/DiggingPrototype/DiggingFeature`.

> В проекте есть два разных ассета с именем `BP_DiggableGround`: `/Game/DiggingPrototype/BP_DiggableGround` относится к более раннему отдельному voxel-тесту `L_DiggingTest`, а `/Game/DiggingPrototype/DiggingFeature/Blueprints/BP_DiggableGround` — к описанной здесь ветке `DiggingFeature`. При проверке и изменениях всегда сверяйте полный Content Browser path.

## Цель механики

Цель — получить копание грунта, похожее по ощущению на **A Game About Digging A Hole** и **Hydroneer**: игрок должен постепенно вынимать объём земли, а поверхность и физическая коллизия должны принимать форму получившейся ямы.

Главный ориентир — не разрушение заранее подготовленных кубов, а визуально плавное изменение цельной геометрии. На текущем этапе сознательно решается задача одного качественного копаемого участка. Большой мир, загрузка чанков и сохранение изменений пока не проектируются.

## Текущий статус

В репозитории сохранены два последовательных прототипа:

1. `BP_DiggableGround` на основе `Instanced Static Mesh` — рабочий и понятный voxel-эталон.
2. `BP_DiggableGround_Smooth` на основе `Dynamic Mesh`, Geometry Script и Boolean Subtract — текущее основное направление разработки.

Эволюция текущей ветки выглядит так:

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

Текущим игровым направлением стал отдельный `BP_DigPlayer_FirstPerson`: камера находится на socket скелета, тело остаётся видимым, а центральное кольцо показывает направление взаимодействия.

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

### 2. Smooth Dynamic Mesh prototype

Коммит `48ae26f` добавил `BP_DiggableGround_Smooth` и перевёл основное направление эксперимента на цельную изменяемую геометрию.

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

## Smooth Digging — текущая реализация

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

Параметры cutter вынесены в переменные `BP_DiggableGround_Smooth`, имеют `Instance Editable = true` и сгруппированы в категории `Digging|Cutter`:

- `DigRadius = 25` см;
- `DigCutterScale = (1.0, 1.0, 0.35)`;
- `DigCutterPhi = 16`;
- `DigCutterTheta = 24`;
- `Origin = Center`;
- `Location = LocalImpactPoint`;
- `Rotation` формируется из локальной `ImpactNormal`;
- `Scale` берётся из `DigCutterScale`.

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

Для текущего prototype milestone зафиксированы следующие результаты ручной проверки в PIE:

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

### Текущий Fab workflow

В локальную установку UE `5.8` установлен и включён по умолчанию Fab UE Plugin (`Engine/Plugins/Fab`, версия `0.0.15`). Текущий рабочий процесс:

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

### Назначение на Dynamic Mesh

Обычный `Override Materials` slot в Details не оказался удобным для `Dynamic Mesh Component`, поэтому материал назначается в `BP_DiggableGround_Smooth` через Blueprint после создания box и настройки collision:

```text
Construction Script
→ Append Box
→ Enable Complex as Simple Collision
→ Set Override Render Material
   Target   = DigMesh
   Material = MI_xdhhdhl
```

Soil Ground отображается на `DigMesh`, но этот Material Instance нельзя считать готовым материалом копаемой земли.

### UV-проблема Boolean-поверхностей

После нескольких `Boolean Subtract` стало заметно, что обычная UV-based проекция Megascans плохо переносится на вновь созданные поверхности:

- верхняя исходная поверхность выглядит приемлемо;
- texture на cavities сильно растягивается;
- появляются радиальные/star-like patterns;
- внутренние стенки имеют нестабильную развёртку.

Boolean создаёт новую геометрию, для которой нет подходящей устойчивой UV-развёртки исходного box. Ближайшее направление — собственный `M_DiggableSoil` с World Aligned / Triplanar projection:

```text
Base Color  → WorldAlignedTexture
Normal      → WorldAlignedNormal
Roughness/AO→ согласованная world-space projection
Scale       → настраиваемый parameter
```

`M_DiggableSoil` пока **не создан**. Сначала нужно собрать его из импортированных Soil Ground textures и проверить одинаковую плотность texture на плоском верху, вертикальной стене и нескольких Boolean cavities. Fab/Megascans dependencies нельзя удалять до появления проверенной независимой замены.

## Архитектура и ответственность

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

`BP_DigPlayer_FirstPerson` — текущее направление игрока; исходный `BP_DigPlayer` сохраняется как third-person/reference checkpoint.

### `BP_DiggableGround_Smooth`

Отвечает за:

- исходную форму грунта;
- владение `DigMesh` и `DigCutter`;
- перевод мировой точки и normal воздействия в локальные координаты;
- форму и разрешение cutter;
- Boolean-операцию;
- обновление collision;
- непосредственное изменение земли.

Такое разделение позволяет позже менять внутреннюю реализацию грунта, не переписывая прицеливание игрока. Следующий естественный шаг для снижения связанности — общий Blueprint Interface для копаемых объектов, но в текущем prototype используется прямой `Cast To BP_DiggableGround_Smooth`.

## Почему Dynamic Mesh выбран вместо маленьких voxel

Уменьшение voxel лечит только размер ступеней, но не фундаментальную дискретность поверхности. Одновременно число элементов растёт по трём измерениям: уменьшение линейного размера ячейки вдвое требует примерно в восемь раз больше voxel для того же объёма.

Dynamic Mesh даёт:

- одну цельную поверхность вместо набора видимых кубов;
- настоящее изменение геометрии;
- округлые и объединяющиеся выемки;
- collision, соответствующий изменённой форме после обновления.

Однако Boolean по Dynamic Mesh тоже имеет стоимость. Пока не доказано, что текущая схема выдержит большую территорию, длительную сессию и сотни вырезов. Выбор Dynamic Mesh — предпочтительное направление текущего исследования, а не завершённое решение масштабирования.

## Текущие ограничения

- Cutter остаётся scaled sphere / ellipsoid с тестовыми `DigRadius = 25` и `DigCutterScale = (1, 1, 0.35)`.
- Копание визуально всё ещё состоит из округлых «укусов».
- Нет shovel-specific cutter shape.
- Нет отдельного независимого `DigDepth` или offset вдоль `ImpactNormal`.
- Обычный UV-based Megascans material растягивается на Boolean-generated surfaces.
- `M_DiggableSoil` с World Aligned / Triplanar projection ещё не реализован.
- `WBP_DigCrosshair` пока использует prototype Text `○`.
- Full-body first person остаётся прототипом; clipping и представление тела ещё требуют дальнейшей игровой проверки.
- В smooth-ветке нет удержания ЛКМ с ограничением частоты.
- Нет `DigInterval` для smooth-копания.
- Нет отдельного законченного параметра `DigReach`; длина trace и допустимая дальность копания ещё должны быть разведены.
- Нет benchmark для `10`, `100` и `500+` последовательных Boolean.
- Не измерен рост числа triangles после повторных вырезов.
- Не измерена стоимость `Update Collision` после роста геометрии.
- Не внедрены remesh, simplification или другая очистка геометрии.
- Нет chunk manager и потоковой загрузки участков.
- Нет сохранения выкопанной геометрии.
- Нет слоёв `Dirt / Clay / Stone` и различной hardness.
- Нет ресурсов, руды и выдачи предметов за копание.
- Нет законченной системы инструментов.
- Нет частиц, вылетающей земли, decal и звуков.
- Текущий Soil Ground material остаётся визуальным тестом, а не production-ready решением.
- Не подтверждена пригодность реализации для репликации или multiplayer.

## План дальнейшей разработки

Приоритет работ:

1. Создать `M_DiggableSoil` из импортированных Soil Ground textures с World Aligned / Triplanar projection.
2. Проверить texture density, normal и roughness на плоском верху, вертикальной стороне и нескольких Boolean cavities.
3. На читаемом материале настроить `DigRadius` и `DigCutterScale` через Instance Editable параметры.
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

Документационный milestone с первым подробным `README.md` и `AI_CONTEXT.md`. Это текущий Git `HEAD` на момент обновления документации; full-body FPS, surface-aware cutter, crosshair и Fab/Soil Ground отражают более новое текущее состояние Unreal assets.

## Основание документации

Состояние сверено с Git history и текущими Unreal assets через read-only Unreal MCP. Подтверждены Blueprint graphs, функции, зависимости, параметры cutter, component hierarchy, rotation settings, socket, widget tree и назначение материала.

Выявленные технические нюансы текущих assets:

- member names `DigCutterScale `, `DigCutterPhi `, `DigCutterTheta ` и вход `ImpactNormal ` фактически содержат завершающий пробел; в документации используются читаемые имена без пробела;
- `CameraBoom` физически остаётся компонентом `BP_DigPlayer_FirstPerson`, хотя `FollowCamera` уже прикреплена напрямую к `Mesh`;
- `Hide Bone By Name(head)` остаётся неподключённым узлом и не выполняется;
- текущий `TryDigSmooth` всё ещё содержит prototype debug drawing и `HIT`/`MISS` Print String.

Точный текстовый diff Blueprint-графов через Git недоступен, поскольку Unreal assets хранятся как бинарные Git LFS-файлы. При дальнейшей работе фактический граф в Unreal Editor или через Unreal MCP имеет приоритет над этим документом.
