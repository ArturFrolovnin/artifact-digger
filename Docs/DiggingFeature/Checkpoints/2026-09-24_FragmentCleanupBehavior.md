# Fragment Cleanup Behavior and Engine Direction — decision record 2026-09-24

Проект: **Artifact Digger / ArcheoDig**, Unreal Engine 5.8.

Этот документ фиксирует выводы сегодняшнего тестирования terrain cleanup и обсуждение того, как должны вести себя отделившиеся куски земли разного размера. Код сегодня не меняется: это design/engineering checkpoint для следующей C++ итерации.

## Контекст

Текущий preferred digging prototype — `Try Surface Dig C++` из `UVoxelDigTestLibrary`.

Первая версия `CleanupFloatingFragments()` уже работает как local connected-components cleanup:

- после Surface Dig берётся локальный Bounds вокруг `ImpactPoint`;
- terrain data читается одним блоком;
- используется 6-neighbor flood fill;
- маленькие isolated components удаляются;
- boundary-touching и слишком большие components сохраняются;
- cleanup остаётся prototype, а не финальной collapse system.

## OBSERVED — результат сегодняшнего теста

Пользователь продолжил тестировать `Try Surface Dig C++` с cleanup.

Пример тестовых параметров в Blueprint:

```text
Radius = 30
Cleanup Floating Fragments = true
Cleanup Radius = 200
Max Fragment Voxels = 200
```

Наблюдение:

- мелкие отделившиеся куски исчезают хорошо и почти не создают визуальных проблем;
- если подкопать и полностью отделить большой пласт грунта, он может остаться висеть в воздухе;
- это ожидаемое ограничение текущего алгоритма, потому что большой component может превышать `MaxFragmentVoxels` и/или касаться границы локального Cleanup Bounds.

Текущий cleanup хорошо решает задачу **мелкого мусора**, но пока не определяет финальное gameplay-поведение больших detached masses.

## Главное design-решение

Не использовать одно правило:

```text
detached terrain
→ always delete
```

для всех размеров.

Мгновенное исчезновение крупной глыбы или пласта в несколько кубических метров будет визуально странным и разрушит ощущение физичности копания.

Нужно разделить:

```text
Fragment Detection
!=
Fragment Presentation
```

Первая система определяет, что terrain component отделился и оценивает его размер.

Вторая решает, что с ним делать визуально и геймплейно.

## Предлагаемая классификация detached fragments

Вместо трёх независимых size variables использовать **две границы**, которые автоматически создают три size classes.

Планируемые Blueprint-facing параметры:

```text
Instant Delete Max Volume
Collapse Max Volume
```

Логика:

```text
Volume <= InstantDeleteMax
→ TINY
→ удалить сразу

InstantDeleteMax < Volume <= CollapseMax
→ MEDIUM
→ будущий collapse / crumble

Volume > CollapseMax
→ LARGE
→ не удалять автоматически
```

Это проще и однозначнее, чем три отдельных порога Small / Medium / Large.

## Почему лучше volume, а не raw voxel count

Текущий `MaxFragmentVoxels` удобен алгоритму, но плохо читается как gameplay parameter.

Game designer мыслит:

```text
0.03 m³
0.3 m³
1.0 m³
```

а не:

```text
237 voxel samples
4180 voxel samples
```

Поэтому предпочтительное направление — показывать в Blueprint physical-ish volume thresholds, а внутренний C++ уже переводит их в подходящее representation для текущего voxel resolution.

При voxel size около `5 cm` один кубический метр грубо соответствует примерно `20 × 20 × 20 = 8000` voxel cells. Это только ориентир: реальный density surface и partially filled samples требуют аккуратной интерпретации.

## Cleanup v1.5 — ближайший кодовый эксперимент

Не реализовывать physics/collapse сразу.

Следующая итерация должна прежде всего классифицировать найденные detached components.

Предлагаемые состояния:

```text
TINY
→ delete immediately

MEDIUM
→ keep for now
→ debug classification
→ future collapse candidate

LARGE
→ keep
→ future large-collapse / unstable slab logic

UNKNOWN
→ component touches local Bounds
→ local analysis insufficient
→ keep
```

То есть первая версия новой ноды/логики должна дать возможность **играть и собирать ощущения от размеров**, не пытаясь сразу строить сложную physics system.

Пример debug:

```text
TINY FRAGMENT: 0.02 m³ → deleted
MEDIUM FRAGMENT: 0.35 m³ → collapse candidate
LARGE FRAGMENT: 2.8 m³ → kept
UNKNOWN: component reaches cleanup bounds
```

Точные thresholds заранее не фиксируются. Их нужно подобрать в PIE методом тестов.

## Почему большие fragments пока лучше оставлять

До появления collapse presentation:

```text
large detached fragment
→ keep
```

лучше, чем:

```text
large detached fragment
→ instant pop/disappear
```

Висящий большой пласт является заметным prototype limitation, но мгновенное исчезновение нескольких кубометров земли будет выглядеть ещё менее естественно.

## Будущая collapse system

Для medium/large fragments потенциальное направление:

```text
detached component detected
→ remove from voxel terrain
→ spawn simplified debris / several chunks
→ short physics simulation
→ Pawn collision = Ignore or non-blocking
→ dust / crumble VFX
→ destroy debris after short lifetime
```

Большой terrain component не обязан превращаться в точную физическую копию всего voxel fragment. Визуально его можно представить несколькими simplified debris chunks.

Для крупных пластов возможен более выраженный event:

```text
mark unstable
→ short delay
→ crack sound / dust
→ collapse
```

Это может стать частью game feel, а не только техническим cleanup.

## Connectivity: local cleanup и large-fragment validation — разные задачи

Текущий local cleanup должен остаться дешёвым и частым:

```text
terrain edit
→ small local cleanup
→ remove tiny detached noise
```

Для больших масс в перспективе нужен отдельный support/connectivity check.

Более надёжная модель:

```text
known supported / anchor terrain
→ flood fill through solid terrain
→ reached voxels = supported
→ unreached solid components = detached
```

Для bounded Dig Site anchor-областью потенциально может быть нижний/опорный слой участка.

Такой анализ не следует запускать по всему Dig Site на каждый click.

Возможный scheduling:

```text
per dig
→ cheap local cleanup

after burst / mouse release / timer
→ larger connectivity validation
```

или анализ только dirty chunks + neighbours.

## Thin bridges / overhangs

Важно не путать:

- полностью disconnected component;
- connected overhang / tunnel ceiling;
- component, соединённый тонким мостиком.

Обычный flood fill считает thin bridge настоящим соединением и не удалит такой участок.

Это отдельная будущая задача thickness/neighbour/support analysis и не должна решаться агрессивным удалением больших components.

## Soil behavior в перспективе

Fragment presentation может зависеть не только от объёма, но и от типа грунта:

```text
Loose Soil
→ легче осыпается

Clay
→ дольше держит навесы и крупные куски

Rock
→ может сохранять большие detached/near-detached формы или требовать отдельной fracture logic
```

Это пока design direction, не реализованная система.

## Engine direction — Unreal Engine остаётся выбранным направлением

Сегодня отдельно сравнивались Unity и Unreal Engine в контексте ArcheoDig.

Вывод не меняет стек проекта: **миграция на Unity не рассматривается**.

Unity был бы проще для быстрого gameplay scripting благодаря C# и простому component workflow, особенно для programmer-first iteration.

Unreal сложнее на входе из-за C++, reflection/build workflow и разделения Editor/C++ layers, но лучше соответствует долгосрочной траектории ArcheoDig:

- изменяемый volumetric terrain является центральной системой;
- тяжёлые terrain algorithms удобно держать в C++;
- можно использовать Blueprint как orchestration/config layer;
- доступен глубокий plugin/engine integration;
- high-end rendering/world tooling уже является частью общей экосистемы;
- собственный terrain backend можно постепенно развивать без смены движка.

Практически подтверждённый удобный паттерн проекта:

```text
Blueprint
→ one coarse C++ operation
→ heavy implementation inside C++
```

Например:

```text
Left Mouse Button
→ Try Surface Dig C++
```

вместо большого Blueprint graph.

## Следующий рекомендуемый code step

Когда разработка продолжится за компьютером:

1. Не переписывать `TrySurfaceDig`.
2. Оставить существующий small-fragment cleanup.
3. Добавить две Blueprint-facing границы размера/объёма.
4. Ввести classification TINY / MEDIUM / LARGE / UNKNOWN.
5. Реально удалять пока только TINY.
6. MEDIUM / LARGE оставлять и показывать debug classification.
7. По результатам PIE-тестов подобрать реальные thresholds.
8. Только после этого проектировать collapse/debris presentation.

Главная цель следующего этапа — сначала понять **какие размеры должны вести себя по-разному**, а не сразу строить сложную physics system.
