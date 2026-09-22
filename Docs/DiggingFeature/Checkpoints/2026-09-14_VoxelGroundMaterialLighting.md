# Voxel Ground Material + Lighting Prototype — checkpoint 2026-09-14

> **Historical snapshot:** material wiring below records the state before hotfix `c00dd30` from 2026-09-22. The later `VertexNormalWS` orientation mask, shared Base Color/Normal mask and C++ workflow are documented in [C++ Workflow and Digging Migration — 2026-09-22](2026-09-22_CPPWorkflowAndDiggingMigration.md). Остальной текст этого checkpoint сохранён без ретроспективного переписывания.

Проект: Artifact Digger / ArcheoDig, Unreal Engine 5.8.

HEAD при проверке: `81a291237a1e96135067f050a1c6258d81e06210` — `voxel surface digging prototype checkpoint`.

Предыдущий этап: [Voxel Surface Prototype — 2026-09-12](2026-09-12_VoxelSurfacePrototype.md). Его описание пустого материала сохраняет историческую ценность, но больше не отражает текущий graph. Архитектурные решения: [DiggingArchitecture.md](../../DiggingArchitecture.md); research и benchmark roadmap: [DiggingTerrainArchitecture.md](../../Research/DiggingTerrainArchitecture.md).

## Scope и достоверность checkpoint

Задача — документация текущего visual prototype материала и освещения. Gameplay, terrain architecture, digging parameters и benchmark logic в рамках checkpoint не изменялись. Unreal assets не редактировались и не пересохранялись; Git commit не создавался.

Параметры и подключения ниже прочитаны через Unreal Editor API. `M_VoxelGround_Prototype` при проверке не dirty; **`L_VoxelDig2` имеет несохранённые изменения**. Поэтому world/lighting значения описывают текущий загруженный уровень, а их совпадение с `.umap` на диске не гарантируется. Сохранение уровня остаётся отдельным действием пользователя. Визуальная оценка взята из описания сессии пользователем; новый PIE-тест и shader compile в этой documentation task не выполнялись.

На входе в задачу Git показывал изменённые `BP_VoxelDigPlayer2`, `L_VoxelDig2`, `M_VoxelGround_Prototype`, девять staged Dirt Ground assets и untracked `Content/GrassMat/`. Binary diff показывает изменения LFS pointers и не раскрывает graph. Существующие изменения и staging сохранены.

## VERIFIED CURRENT ASSET STATE

### Voxel World

Level: `/Game/DiggingPrototype/Voxel/Voxel_2/L_VoxelDig2`.

Actor label: `VoxelDigSite2`; UObject: `L_VoxelDig2.L_VoxelDig2:PersistentLevel.VoxelWorld_1`.

| Параметр | Текущий уровень в Editor |
| --- | --- |
| Render Type | Marching Cubes |
| Voxel Size | `5 cm` |
| World Size In Voxel | `256` |
| Material Config | `RGB` |
| Voxel Material | `/Game/DiggingPrototype/Voxel/Voxel_2/Materials/M_VoxelGround_Prototype` |

Материал непосредственно назначен основным материалом Voxel World. Это visual prototype. `5 cm` и `256` — параметры текущего эксперимента, не новые production constants и не замена research benchmark `5 × 5 × 3 m @ 10 cm`. В checkpoint 12 сентября были `10 cm` и `64`.

### Реальные пути Grass / Dirt

По описанию пользователя источники — бесплатный Fab Grass Material Pack и бесплатный Quixel/Megascans Dirt Ground. Локально подтверждены следующие assets; бесплатность и название Fab listing отдельно не проверялись.

| Назначение | Content Browser path |
| --- | --- |
| Grass Base Color, подключён | `/Game/GrassMat/Texture/T_GrassMat3_basecolor` |
| Grass pack master | `/Game/GrassMat/Materials/MM/MM_GrassMat` |
| Grass pack instance 3 | `/Game/GrassMat/Materials/IM_GrassMat_Inst3` |
| Dirt Base Color, подключён | `/Game/Fab/Megascans/Surfaces/Dirt_Ground_xdhhdgq/Raw/xdhhdgq_tier_0/Textures/T_xdhhdgq_8K_B` |
| Dirt Normal, подключён | `/Game/Fab/Megascans/Surfaces/Dirt_Ground_xdhhdgq/High/xdhhdgq_tier_1/Textures/T_xdhhdgq_4K_N` |
| Dirt Height, импортирован, не используется в outputs | `/Game/Fab/Megascans/Surfaces/Dirt_Ground_xdhhdgq/High/xdhhdgq_tier_1/Textures/T_xdhhdgq_4K_H` |
| Dirt ORM, доступен для следующего этапа | `/Game/Fab/Megascans/Surfaces/Dirt_Ground_xdhhdgq/High/xdhhdgq_tier_1/Textures/T_xdhhdgq_4K_ORM` |
| Dirt ORM, Raw-вариант | `/Game/Fab/Megascans/Surfaces/Dirt_Ground_xdhhdgq/Raw/xdhhdgq_tier_0/Textures/T_xdhhdgq_8K_ORM` |

Также присутствуют `T_xdhhdgq_4K_B`, `T_xdhhdgq_8K_N` и `MI_xdhhdgq` в обеих папках `High/xdhhdgq_tier_1/Materials` и `Raw/xdhhdgq_tier_0/Materials`. Наличие импортированного asset не означает, что он подключён в текущем материале. В частности, Base Color сейчас 8K, а Normal — 4K.

### Base Color и параметры

Обе поверхности используют `Texture Object` и `WorldAlignedTexture`, выход `XYZ Texture`. Каждый цвет умножается на свой Tint через `Multiply`. Тонированный Dirt подключён во вход `A` основного `Lerp`, Grass — в `B`, итоговая маска — в `Alpha`; результат идёт в Material Base Color. Проекция использует world space и не требует обычной mesh UV-развёртки.

| Параметр | Проверенное значение |
| --- | --- |
| GrassTint | sRGB `#A4B896`; linear RGB ≈ `(0.371238, 0.479320, 0.304987)` |
| DirtTint | sRGB `#C2A189`; linear RGB ≈ `(0.539480, 0.356400, 0.250158)` |
| SurfaceZ | `0` |
| GrassDepth | `6` |
| BlendWidth | `2` |
| Power, Const Exponent | `4` |
| DirtTextureSize | `180` |
| Tangent Space Normal | отключён |

Tint — приятная рабочая база, не окончательный art direction. Значения маски и масштаба также остаются prototype settings.

### Grass / Dirt mask

Проверенная высотная цепочка использует Absolute World Position, выход `Z`:

```text
heightMask = Saturate((WorldPosition.Z - (SurfaceZ - GrassDepth)) / BlendWidth)
orientationMask = Power(Saturate(PixelNormalWS.B), 4)
grassMask = heightMask * orientationMask
```

При текущих значениях высотный переход идёт от `Z = -6` до `Z = -4 cm`. `ComponentMask` выбирает только `B`, то есть Z-компонент normal. Маска ориентации оставляет Grass преимущественно на обращённых вверх поверхностях, а вертикальные и сильно наклонённые стенки делает Dirt. Увеличение exponent сильнее ограничивает Grass поверхностями, направленными вверх.

### Texture scale и Normal

`DirtTextureSize = 180` подключён к `TextureSize` как у `WorldAlignedTexture` с Dirt Base Color, так и у `WorldAlignedNormal` с Dirt Normal. У `WorldAlignedTexture` с Grass вход `TextureSize` не подключён; отдельного `GrassTextureSize` пока нет.

Подтверждённая normal chain:

```text
Texture Object (T_xdhhdgq_4K_N)
→ WorldAlignedNormal: XYZ Texture
→ Lerp: A
VertexNormalWS → тот же Lerp: B
Lerp → Normalize → Material Normal
```

**Расхождение с описанием сессии:** `Alpha` этого normal `Lerp` сейчас подключён к `MaterialExpressionMultiply_1`, то есть к Dirt Base Color после Tint. Основной Base Color `Lerp` получает маску из `MaterialExpressionMultiply_0`. Поэтому нельзя утверждать, что нормали уже смешиваются той же Grass/Dirt mask. Намерение — использовать общую маску; текущее подключение требует проверки в Editor перед дальнейшей настройкой normal. В этой задаче оно не исправлялось.

Также требуется визуальная/shader-проверка совместимости `PixelNormalWS` с предполагаемой общей маской, если она будет участвовать в вычислении Material Normal; успешная компиляция такого будущего подключения не заявляется.

`T_xdhhdgq_4K_H` присутствует в graph как `Texture Sample`, но не участвует в проверенных Base Color / Normal outputs. Height остаётся unused asset / TODO; displacement или parallax не реализованы этим checkpoint.

### Roughness

Material Roughness не имеет подключённой expression. ORM/Roughness map пока не реализована. Пользователь сообщает о прежней высокой постоянной roughness около `0.9`; численное значение fallback у output через доступный запрос прочитать не удалось, поэтому **текущие `0.9` не подтверждены** и требуют проверки Details в Editor.

## LIGHTING — текущие значения загруженного уровня

Lighting создаёт стабильные условия для material development. Это рабочая база, не финальное художественное освещение.

| Actor / настройка | Проверенное значение |
| --- | --- |
| `DirectionalLight_0`, Rotation X / Y / Z | `0 / -45 / -45°` (Roll / Pitch / Yaw) |
| Directional Light Intensity | `25` |
| Use Temperature / Temperature | включено / `5200 K` |
| Source Angle / Source Soft Angle | `2 / 0` |
| Shadow Amount | `0.75` |
| `SkyLight_0`, Intensity | `3.0` |
| SkyLight Real Time Capture | включён |
| `PostProcessVolume_0`, Infinite Extent / Unbound | включён |
| Min EV100 / Max EV100 | `3 / 3`, оба override включены |
| Exposure Compensation | `1.1`, override включён |
| Lumen Diffuse Color Boost | `1.3`, override включён |
| Lumen Skylight Leaking | `0.005`, override включён |

Light components: `DirectionalLight_0.LightComponent0` и `SkyLight_0.SkyLightComponent0` внутри `L_VoxelDig2.L_VoxelDig2:PersistentLevel`. Rotation прочитан с root light component. В исходных заметках Pitch был `-35`, а Skylight Leaking — `0.003`; таблица использует текущие значения Editor. Уровень dirty: перед использованием этой таблицы как сохранённого preset проверить сохранение `.umap`.

GI — Lumen: `Config/DefaultEngine.ini` содержит `r.DynamicGlobalIlluminationMethod=1`. В PostProcessVolume поле GI также `Lumen`, но его override отключён — используется project setting. Расширенный диапазон exposure включён в Config; одинаковые Min/Max EV100 фиксируют адаптацию для предсказуемой оценки материалов.

Directional Light — солнце уровня: Pitch меняет высоту солнца и длину теней, Yaw — сторону освещения, Roll в текущей схеме практически не нужен. SkyLight заполняет теневые области. Увеличение SkyLight Intensity осветляет тени, но чрезмерное значение делает сцену плоской. Увеличение Exposure Compensation осветляет всю картинку камеры.

## OBSERVED PROTOTYPE RESULT / ART DIRECTION

По наблюдениям пользователя, тестировались Dirt TextureSize `20`, `16`, `200`; около `180–200` камушки и неровности читаются лучше. Меньший TextureSize чаще повторяет рисунок и уменьшает детали; больший делает рисунок крупнее. `180` оставлен рабочей точкой. Проверять это нужно на обычном игровом расстоянии, а не только в close-up.

В ходе сессии увеличивали SkyLight, корректировали солнечные тени через Shadow Amount и фиксировали exposure. Пользователь почти не заметил пользы от изменения Skylight Leaking с `0.003` на `0.005`; при проверке в Editor всё же стоит `0.005`. Это наблюдение и текущее значение, а не рекомендация дополнительно повышать leaking.

Дизайнерский принцип глубины:

- поверхность и неглубокая яма читаются при естественном свете;
- средняя глубина темнее, но геометрия ещё различима;
- глубокая шахта может практически терять естественный свет;
- условные сотни метров / километр вниз требуют собственного света игрока.

Не осветлять любую глубину искусственно через SkyLight/Lumen. Позже flashlight, mining lamp, portable lights и, возможно, battery/power mechanics могут стать gameplay; сейчас это намерение, не реализованные системы.

Визуальное направление — **semi-stylized PBR / stylized realism**. Главный reference — **A Game About Digging A Hole**; дополнительные — Hydroneer, Palworld и немного 7 Days to Die. Нужны простые читаемые формы, PBR response, умеренная детализация, чистая игровая картинка, читаемые земля/камни и слегка стилизованные цвета. Не целиться в photoreal Megascans, ultra realism, toon/cel shading или чистый low-poly. На prototype этапе используются бесплатные assets; подбор платных/финальных материалов отложен.

## Ближайшие шаги

1. **Dirt material:** подключить Roughness из ORM через world-aligned projection, проверить визуально, при необходимости добавить `DirtRoughness`; затем сделать `DirtNormalStrength` и проверить согласованность Normal/Base Color scale. Перед настройкой нормалей проверить выявленное подключение Alpha.
2. **Grass:** решить необходимость отдельного Normal, добавить Grass Roughness и отдельный `GrassTextureSize`, проверить transition.
3. **Graph:** организовать комментарии `Dirt BaseColor`, `Grass BaseColor`, `Grass/Dirt Mask`, `Normals`, `Roughness`, `Outputs`.
4. **Material Instance / параметры:** подготовить удобный workflow с `DirtTint`, `GrassTint`, `DirtTextureSize`, `GrassTextureSize`, `DirtNormalStrength`, `DirtRoughness`, `GrassRoughness`, `GrassDepth`, `BlendWidth`. Уже существующие параметры сохранить; отсутствующие здесь перечислены как TODO.
5. **Читаемость:** оценить края ямы, стенки и дно на нормальном игровом расстоянии, а не оптимизировать только close-up.
6. **Позже:** particles/dirt debris, sound feedback, visual digging feedback и подземное освещение игрока.

**Следующий конкретный шаг:** в небольшой обучающей итерации найти `T_xdhhdgq_4K_ORM`, проверить назначение roughness-канала, затем начать world-aligned подключение Dirt Roughness с тем же `DirtTextureSize = 180`. Проверить результат до перехода к Normal Strength. Текущее расхождение normal Alpha и fallback Roughness проверить по graph/Details, не считать уже исправленными.

Архитектура и benchmark roadmap остаются прежними. Обязательная граница: `Gameplay → Dig/Terrain abstraction → concrete terrain backend`. Этот material/lighting checkpoint не выбирает production backend и не добавляет gameplay systems.
