# Voxel Surface Prototype — checkpoint 2026-09-12

Проект: ArcheoDig, Unreal Engine 5.8
Проверенный HEAD до checkpoint: `4f999557bb0db4e1cac10f7948865fbe3b60801c` (`add research and test level voxel`)

Этот документ фиксирует состояние Voxel Plugin Free Legacy после сессии прототипирования. Факты, прочитанные из сохранённых Unreal assets, отделены от наблюдений во время Play-in-Editor. Архитектурные решения остаются authoritative в [`../../DiggingArchitecture.md`](../../DiggingArchitecture.md), полное исследование — в [`../../Research/DiggingTerrainArchitecture.md`](../../Research/DiggingTerrainArchitecture.md).

## Scope checkpoint

Основная рабочая ветка сессии:

- `/Game/DiggingPrototype/Voxel/Voxel_2/L_VoxelDig2`;
- `/Game/DiggingPrototype/Voxel/Voxel_2/Blueprints/BP_VoxelDigPlayer2`;
- `/Game/DiggingPrototype/Voxel/Voxel_2/Blueprints/BP_VoxelDigGameMode2`;
- `/Game/DiggingPrototype/Voxel/Voxel_2/Materials/M_VoxelGround_Prototype`.

Также сохранены изменённые assets первого VoxelFree baseline:

- `/Game/DiggingPrototype/Voxel/L_VoxelDigTest`;
- `/Game/DiggingPrototype/Voxel/BP_VoxelDigPlayer`.

Они не удалены и остаются историческим reference перед чистой веткой `Voxel_2`.

## VERIFIED CURRENT ASSET STATE

### Level, world and player wiring

Текущий уровень — `/Game/DiggingPrototype/Voxel/Voxel_2/L_VoxelDig2`.

`WorldSettings.DefaultGameMode`:

`/Game/DiggingPrototype/Voxel/Voxel_2/Blueprints/BP_VoxelDigGameMode2.BP_VoxelDigGameMode2_C`

Проверенные defaults `BP_VoxelDigGameMode2`:

- `DefaultPawnClass` — `BP_VoxelDigPlayer2_C`;
- `PlayerControllerClass` — `/Game/ThirdPerson/Blueprints/BP_ThirdPersonPlayerController.BP_ThirdPersonPlayerController_C`.

Это сохраняет Enhanced Input из Third Person template. `BP_VoxelDigPlayer2` сейчас является тестовым carrier для trace и прямых вызовов VoxelFree API, а не финальной gameplay architecture.

В уровне размещён `VoxelWorld` с label `VoxelDigSite2`. Проверенные параметры:

| Property | Saved value |
| --- | --- |
| `Voxel Size` | `10 cm` |
| `World Size In Voxel` | `64` |
| Generator | `VoxelFlatGenerator` |
| `Material Config` | `RGB` |
| `Voxel Material` | `M_VoxelGround_Prototype` |
| `Material Collection` | `/Voxel/Examples/Materials/Quixel/MC_Quixel` |
| `Render Type` | `Marching Cubes` |
| `Create World Automatically` | `true` |
| `Use Custom World Bounds` | `false` |
| `Render Octree Depth` | `1` |
| `Min LOD` / `Max LOD` | `0` / `24` |
| `Normal Config` | `Gradient Normal` |
| `UV Config` | `Global UVs` |

`Material Collection` назначен, но при текущем `Material Config = RGB` не является активной material configuration. `Voxel Size = 10 cm` задаёт дискретизацию представления terrain, а не размер brush/hole.

### BP_VoxelDigPlayer2

Parent class — `Character`. Проверенные member defaults:

- `DigReachCm = 500`;
- `test-1 = -1`.

Enhanced Input graph содержит движение, mouse/gamepad look и jump. `Left Mouse Button: Pressed` подключён к `TryVoxelSurfaceDig2`. Вызовы `TryVoxelDig2`, `TryDig` и `TryDigSmooth` сохранены, но отключены от execution path. `Hide Bone by Name` также отключён.

Общий trace текущих voxel-функций:

```text
FollowCamera location + forward × DigReachCm
→ Line Trace By Channel (Visibility / TraceTypeQuery1)
→ ignore self, Trace Complex = false
→ debug trace For Duration = 5 s
→ Hit Actor cast to VoxelWorld
```

### `TryVoxelDig2`: TrimSphere reference

Проверенная цепочка после успешного cast:

```text
ImpactPoint → TrimSphere.Position
ImpactNormal × test-1 → TrimSphere.Normal
TrimSphere → debug sphere → HIT
```

Параметры `TrimSphere`:

- `Radius = 20`;
- `Falloff = 0.35`;
- `Additive = false`;
- `Multi Threaded = true`;
- `Record Modified Values = true`;
- `Convert To Voxel Space = true`;
- `Update Render = true`.

При `test-1 = -1` нормаль разворачивается. Debug sphere использует radius `20`, `16` segments и duration `0.1 s`. Функция сохраняется как reference и сейчас не вызывается LMB.

### `TryVoxelSurfaceDig2`: active surface edit

Проверенная цепочка после успешного cast:

```text
ImpactPoint + radius 20
→ Make Int Box From Global Position And Radius
→ Find Surface Voxels From Distance Field
→ Apply Falloff (Smooth, center = ImpactPoint, radius 20, falloff 0.55)
→ Add To Stack
→ Apply Constant Strength (+10)
→ Add To Stack
→ Apply Stack
→ Edit Voxel Values
```

Точные параметры:

- bounds radius: `20`;
- `Find Surface Voxels From Distance Field.Multi Threaded = false`;
- falloff type: `Smooth`;
- falloff radius: `20`;
- falloff: `0.55`;
- `Convert To Voxel Space = true`;
- constant strength: `+10`;
- `Distance Divisor = 1.0`;
- edit `Multi Threaded = true`;
- `Record Modified Values = true`;
- `Update Render = true`.

`ImpactNormal` в этой функции не используется. Debug sphere: radius `20`, `16` segments, duration `0.1 s`.

### Material asset

`/Game/DiggingPrototype/Voxel/Voxel_2/Materials/M_VoxelGround_Prototype` существует, сохранён и назначен `VoxelDigSite2`. Проверка сохранённого asset показала:

- material domain `Surface`, blend mode `Opaque`, shading model `Default Lit`;
- expression nodes отсутствуют;
- `Base Color` не подключён;
- asset dependencies отсутствуют.

Следовательно, обсуждавшаяся height-based схема Grass/Dirt пока является только намерением: в persisted material graph её нет, и визуальный blend не подтверждён.

## OBSERVED PROTOTYPE RESULT

Следующие пункты — наблюдения сессии, а не выводы только из сериализованных assets:

- До назначения `BP_ThirdPersonPlayerController` Pawn, LMB и trace работали, но WASD и mouse look не работали. После назначения controller Enhanced Input заработал.
- `TrimSphere` начал вычитать terrain после инверсии `ImpactNormal`. На плоской верхней поверхности результат визуально близок к `RemoveSphere`, потому что верхняя часть сферы уже находится в воздухе.
- Surface Edit заметно отличается от `RemoveSphere`/`TrimSphere`: выглядит ближе к снятию или продавливанию поверхностного слоя, оставляет меньше ощущения повторяющихся сферических stamps и лучше соединяет соседние edits.
- `ApplyStack` без корректной spatial mask/filter воздействовал на весь `IntBox`, создавая кубический/квадратный результат. Bounds ограничивает область поиска, а stack/falloff должен задавать форму воздействия внутри неё.
- Отрицательный `Constant Strength` на проверенном графе наращивал terrain; сохранённое положительное значение `+10` удаляет terrain.
- При агрессивных или глубоких edits всё ещё наблюдаются острые участки, выступы и потенциальные floating islands. Влияние resolution, radius, falloff и strength пока не исследовано системно.

## CURRENT PREFERENCE — NOT A PRODUCTION DECISION

`TryVoxelSurfaceDig2` — текущий лучший субъективный кандидат среди проверенных voxel brushes для следующего controlled benchmark. Это не выбор production backend и не финальная форма лопаты.

| Prototype | Что подтвердил | Текущий статус |
| --- | --- | --- |
| ISM voxel | Полный gameplay loop и независимое состояние участков | Historical reference; форма слишком кубическая |
| Dynamic Mesh Boolean | Цельная геометрия, collision, interaction и material projection | Frozen reference; repeated Booleans портят topology |
| VoxelFree `RemoveSphere` | Простой runtime density edit | Ранний baseline; явно сферические stamps |
| VoxelFree `TrimSphere` | Directional edit после корректной ориентации normal | Reference; на плоской поверхности близок к `RemoveSphere` |
| VoxelFree Surface Edit | Поверхностный mask, более естественное слияние соседних edits | Предпочтительный prototype candidate; качество и performance не доказаны |

## Не решено

- Поведение Surface Edit на стенах, снизу и в тоннеле.
- Collision после большой серии edits.
- Hitch/frame impact для 10 и 100 последовательных edits.
- Причины острых выступов и floating islands; влияние resolution и brush parameters.
- Save/load изменённого bounded Dig Site.
- Форма shovel brush и связь с `ImpactNormal`.
- Production terrain backend и политика зависимости VoxelFree.
- Проектная `Dig/Terrain` abstraction: текущий test player вызывает VoxelFree напрямую только как prototype wiring.
- Рабочий ground material: сохранённый `M_VoxelGround_Prototype` пока пуст.

## Exact next step

Сначала построить в `M_VoxelGround_Prototype` минимальный height-based grass/dirt material, сохранить его и визуально подтвердить material assignment/blend в `L_VoxelDig2`. Это даст читаемую поверхность для оценки формы edits.

После этого оставить `TryVoxelSurfaceDig2` единственным active test brush и провести контролируемую серию: одиночный edit, соседние edits, 10/100 edits, collision, стена/тоннель, floating fragments и hitch/frame timing. До расширения gameplay вынести вызов backend за проектную границу:

```text
Gameplay
→ Dig/Terrain abstraction
→ concrete terrain backend
```

Не менять production architecture по субъективному виду одного теста.
