# AI-assisted art production tooling — decision record 2026-09-24

Проект: **Artifact Digger / ArcheoDig**.

Этот документ фиксирует текущий рабочий набор инструментов для производства графики, анимации и звука. Это не vendor lock-in и не финальный список на весь production. Инструменты выбираются по задаче и могут быть заменены после реальных тестов на ассетах проекта.

Цены ниже — ориентиры на момент фиксации документа, **2026-09-24**. Перед покупкой подписки цену и лицензию нужно перепроверять.

## Основной принцип production

Сначала доказать игру, затем вкладываться в финальный визуал.

Рабочая последовательность:

1. Собрать gameplay prototype на простых placeholder-объектах.
2. Довести основные системы, сценарии, progression и взаимодействия до рабочего состояния.
3. Сделать небольшой vertical slice с почти финальным качеством.
4. После подтверждения gameplay постепенно заменять placeholders на финальные ассеты.
5. Gameplay logic хранить отдельно от визуальной оболочки, чтобы замена mesh/material/VFX не требовала переписывать механику.

Пример структуры: BP_DisplayCase содержит StaticMeshComponent, ArtifactSlot, InteractionComponent, Highlight и Gameplay Logic. Сегодня StaticMeshComponent может содержать placeholder, позже — финальный mesh.

Такой подход позволяет долго программировать игру без дорогого art-production и подключить основные платные инструменты только тогда, когда они реально нужны.

## Art direction

Зафиксированное визуальное направление проекта:

- semi-stylized PBR / stylized realism;
- простые и читаемые формы;
- умеренная детализация;
- PBR response;
- слегка стилизованные цвета;
- без photoreal Megascans look как основной цели;
- без toon/cel shading;
- без чистого low-poly как общего направления.

Главный reference: **A Game About Digging A Hole**. Дополнительные references: **Hydroneer**, **Palworld**, немного **7 Days to Die**.

Цель tooling pipeline — не просто генерировать отдельные красивые объекты, а сохранять этот визуальный язык между разными категориями ассетов.

---

# Выбранный базовый стек

## 1. ChatGPT / OpenAI Images

**Ориентир по цене:** ChatGPT Plus — около **$20/month**.

**Роль:**

- art direction;
- style bible;
- concept art;
- reference images;
- orthographic-like views для Image-to-3D;
- варианты одного объекта;
- material references;
- moodboards;
- помощь с Blender, Unreal, Substance и пайплайном;
- описание ассетов и production requirements.

OpenAI на текущем этапе используется как **art director / concept assistant**, а не как основной генератор готовых FBX/GLB mesh.

**Почему выбран:** уже используется в проекте и хорошо подходит для удержания общего визуального языка между разными категориями ассетов.

## 2. Tripo Pro — основной кандидат для 3D generation

**Ориентир по цене:** около **$20/month**.

**Задачи:**

- Image-to-3D;
- Text-to-3D;
- props;
- мебель;
- музейные объекты;
- техника;
- инструменты;
- артефакты;
- часть растительности;
- базовые NPC/character meshes;
- initial PBR textures;
- retopology / smart mesh;
- подготовка моделей для дальнейшей обработки;
- Blender/DCC workflow.

**Ориентир тарифа:** около **3000 monthly credits / ~200 standard models** по текущей оценке сервиса.

**Почему выбран:**

- хороший баланс цена / объём;
- подходит для массового производства игровых ассетов;
- есть Blender integration;
- умеет работать с PBR;
- есть инструменты post-processing и retopology;
- подходит программисту, которому нужен быстрый base mesh, а не ручное моделирование с нуля.

### Важное ограничение

Tripo не заменяет полноценную систему игровых материалов.

Он хорошо подходит для материала конкретной модели, initial texture и leather/metal/fabric look конкретного ассета.

Reusable материалы вроде soil, grass, concrete, stone, fabric, glass, wet surfaces и foliage shaders лучше делать отдельным material pipeline.

## 3. Blender

**Цена:** **free**.

**Роль:**

- cleanup AI-generated mesh;
- исправление пропорций;
- scale;
- pivot;
- разделение модели на части;
- удаление лишней геометрии;
- простая retopology;
- UV fixes;
- подготовка export;
- rig/skin fixes;
- подготовка modular assets;
- FBX/GLB bridge между генераторами и Unreal.

**Почему выбран:** нужен как универсальный технический редактор между AI generation и Unreal Engine. Цель — не становиться full-time 3D artist, а знать достаточно Blender для исправления и подготовки сгенерированных ассетов.

## 4. Adobe Substance 3D Texturing

**Ориентир по цене:** около **$24.99/month**.

Подключать не обязательно на prototype stage. Покупать, когда начнётся production финальных материалов.

**Роль:**

- reusable PBR materials;
- tileable surfaces;
- soil;
- sand;
- clay;
- rock;
- concrete;
- plaster;
- brick;
- wood;
- metal;
- rust;
- painted metal;
- leather;
- fabric;
- plastic;
- rubber;
- dirt;
- moss;
- dust;
- texturing конкретных props;
- создание Base Color / Normal / Roughness / Height / AO / Metallic maps.

**Почему выбран:** проекту нужно не только создавать meshes, но и держать одинаковый material language между сотнями объектов. Вместо уникального случайного AI-материала на каждом ассете предпочтительно использовать небольшую библиотеку master/reusable материалов.

Пример: M_Fabric_Master может иметь instances MI_Jacket_Fabric, MI_Backpack_Fabric, MI_FieldBag_Fabric и MI_Tent_Fabric.

## 5. Unreal Engine 5

**Цена:** без отдельной monthly subscription для текущей разработки; коммерческие условия проверять перед релизом.

**Роль:**

- финальная сборка levels;
- Blueprints / C++ gameplay;
- Actors;
- Master Materials;
- Material Instances;
- Landscape / terrain;
- Voxel terrain;
- foliage;
- PCG;
- Nanite;
- Lumen;
- collisions;
- Niagara VFX;
- animation blueprints;
- IK Retargeting;
- audio integration;
- level lighting.

**Почему выбран:** UE является финальной точкой всего visual pipeline. Внешние AI tools должны поставлять assets; игровой runtime и визуальная система должны оставаться управляемыми внутри проекта.

---

# Альтернативный 3D generator: Sloyd

## Sloyd Plus

**Ориентир:** около **$15/month**.

Интересен как дешёвый вариант для большого количества итераций:

- Text-to-3D;
- Image-to-3D;
- AI retexturing;
- rigging/animation;
- plugin workflow;
- 1 Custom Art Style;
- standard generations заявлены как unlimited.

**Когда использовать:** если во время тестов окажется, что для production важнее большое количество дешёвых итераций и удержание одного custom style, чем возможности Tripo.

## Sloyd Pro

**Ориентир:** около **$50/month**.

Главная потенциальная ценность для Artifact Digger:

- unlimited Custom Art Styles;
- больше parallel generations;
- priority workflow.

**Когда переходить:** не покупать одновременно с Tripo без причины. Сначала сравнить одинаковые ассеты в обоих сервисах. Если Tripo лучше по geometry — оставить Tripo. Если Sloyd заметно лучше удерживает Artifact Digger style на большом наборе объектов — рассмотреть замену Tripo на Sloyd Pro.

---

# Более дорогой 3D tier: Tripo Max

**Ориентир:** около **$90/month**.

**Что добавляет:**

- существенно больше monthly credits;
- ориентир сервиса — около 1660 standard models/month;
- большой batch throughput;
- много concurrent tasks;
- более удобный high-volume production.

**Решение сейчас:** **не нужен**.

Переходить только если Tripo Pro станет реальным production bottleneck. Для solo development узкое место, скорее всего, будет не generation count, а отбор моделей, cleanup, материалы, collision, интеграция, gameplay, placement и testing.

---

# Hyper3D / Rodin

**Ориентир Creator:** около **$30/month**.

Потенциально полезен для:

- quality-focused Image-to-3D;
- multi-image generation;
- PBR;
- Smart Low-Poly;
- HD/custom textures;
- Blender / Unreal integrations.

**Решение сейчас:** не baseline tool. Оставляем как альтернативу для теста, если Tripo/Sloyd будут плохо справляться с конкретной категорией ассетов.

# Kaedim

Сервис ориентирован больше на studio / production outsourcing workflow.

**Решение сейчас:** не использовать.

Причина: для solo/indie production стоимость не оправдывает преимущества на текущем этапе.

---

# Animation pipeline

Для обычных NPC не планируется генерировать locomotion с нуля.

## Epic Game Animation Sample

**Цена:** free.

Использовать как источник и reference для walk, run, starts/stops, turns, traversal и современного UE locomotion pipeline.

## Mixamo

**Цена:** free на текущих условиях Adobe.

Использовать для готовых humanoid animations:

- idle;
- walk;
- run;
- sitting;
- gestures;
- simple interactions.

Через UE IK Rig / IK Retargeter одна библиотека движений должна переиспользоваться между разными humanoid NPC: Archaeologist, Museum Worker, Scientist, Guard, Visitor и другими.

## Rokoko / DeepMotion

Подключать только при необходимости уникальной анимации.

Примеры:

- поднять артефакт;
- осмотреть вазу;
- передать предмет другому NPC;
- работать кисточкой;
- специфичное действие инструмента.

Workflow: phone video / text motion → Rokoko or DeepMotion → FBX animation → UE IK Retargeter → NPC.

На prototype stage отдельная платная подписка на animation AI не требуется.

---

# Audio pipeline

Звук рассматривается отдельно от 3D/graphics.

## ElevenLabs

**Starter ориентир:** около **$6/month**.  
**Creator ориентир:** около **$22/month**.

Использовать для:

- digging SFX;
- rock impacts;
- soil/debris;
- footsteps;
- doors;
- machinery;
- ambience elements;
- NPC voices / temporary voice acting.

Для prototype можно использовать placeholders и подключить ElevenLabs ближе к audio pass.

## Stable Audio / отдельный music generator

Рассматривать позже для:

- ambient beds;
- music drafts;
- environmental sound layers.

Перед использованием любой AI-generated music в релизе обязательно отдельно проверить актуальную commercial/game license.

---

# Три уровня бюджета

## Tier 1 — дешёвый prototype

Инструменты:

- ChatGPT;
- Sloyd Plus или Tripo Pro;
- Blender;
- Unreal Engine;
- Epic animations / Mixamo;
- placeholder audio.

Ориентир дополнительных затрат сверх уже имеющегося ChatGPT: примерно 15–20 USD/month.

**Цель:** gameplay prototype + первые реальные asset tests.

## Tier 2 — основной price/quality production

Инструменты:

- ChatGPT;
- Tripo Pro;
- Blender;
- Substance 3D Texturing;
- Unreal Engine;
- Epic animations;
- Mixamo;
- ElevenLabs при начале audio production;
- Rokoko/DeepMotion только точечно.

Ориентир полного monthly stack при активном production — примерно **70–100 USD/month**, в зависимости от подключённых в конкретный месяц audio tools.

**Это текущий предпочтительный production tier.**

## Tier 3 — Pro без избыточного enterprise tooling

Инструменты:

- ChatGPT;
- Tripo Max;
- Blender;
- Substance 3D Texturing;
- Unreal Engine;
- Sloyd Pro вместо Tripo Max, если style consistency окажется важнее geometry throughput;
- ElevenLabs Creator;
- Rokoko/DeepMotion при необходимости.

Ориентир — примерно **150–180 USD/month** в месяцы максимального art production.

**Сейчас не нужен.** Переходить только после появления реального ограничения по throughput.

---

# Предлагаемый production pipeline

Основной flow:

ChatGPT → concept / style bible → reference images → Tripo Pro / Sloyd → base 3D geometry → Blender cleanup/edit → Substance PBR production и UE special materials → Unreal Engine → Blueprint / C++ Actors → final gameplay.

Animation:

Epic / Mixamo → IK Retargeter → NPC Animation Blueprint.

Unique animation:

Video / motion prompt → Rokoko / DeepMotion → IK Retargeter → NPC.

Audio:

ElevenLabs / dedicated audio tools → SFX / voices / ambience → Unreal audio system.

---

# Current decision

На текущем этапе **не закупать весь stack заранее**.

Приоритет:

1. Продолжать gameplay development на placeholders.
2. Для первого production test сравнить **Tripo Pro** и **Sloyd** на одинаковом наборе ассетов.
3. Базовым кандидатом считать **Tripo Pro** из-за price/quality/volume и 3D pipeline.
4. **Sloyd** держать как сильную альтернативу, особенно для custom style consistency.
5. **Blender** использовать как обязательный технический cleanup layer.
6. **Substance** подключить при начале системного material production.
7. **Epic Animation Sample + Mixamo** использовать как бесплатную основу NPC locomotion.
8. **Rokoko / DeepMotion** использовать только для уникальных движений.
9. **ElevenLabs** подключать на audio-production этапе.
10. Переходить на Tripo Max / более дорогие планы только после появления реального production bottleneck.

Главная цель: **не учиться вручную производить каждый asset с нуля, а построить управляемый AI-assisted pipeline, в котором программист может самостоятельно довести игру до цельного визуального качества.**
