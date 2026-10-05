# Blender → UE5 Building Workflow

Статус: **working production workflow for city blockout**.

С 2026-10-01 Blender используется как отдельный инструмент для создания и правки 3D-макетов зданий перед размещением в Unreal Engine.

## Зачем добавлен Blender

Первый университет был собран напрямую в UE5 большим количеством отдельных Static Mesh Actor'ов. Для быстрого прототипа это сработало, но для дальнейших итераций оказалось неудобно:

- изменение общей формы требует править много отдельных частей;
- Outliner быстро разрастается;
- сложнее масштабировать фасад, крышу и пропорции как единое здание;
- неудобно использовать такую сборку как повторно редактируемый source asset.

Поэтому принято разделение:

~~~text
Blender
→ создание и редактирование самого здания

Unreal Engine 5
→ расстановка зданий
→ проверка масштаба персонажем
→ дороги / город / gameplay
~~~

Blender не заменяет UE5 level design. Весь город по-прежнему собирается в Unreal.

## Инструменты

Текущая связка:

- **Blender 5.2.2 LTS**;
- официальный **Blender Lab MCP add-on 1.0.3**;
- локальный MCP Bridge: localhost:9875;
- Codex / Astra управляет Blender через MCP;
- сервер запускается через uv;
- проектный MCP config находится в .codex/config.toml.

Blender и UE MCP могут использоваться в одном проекте: Astra может отдельно работать со сценой Blender и с Unreal.

## Базовый pipeline здания

~~~text
1. Game Design docs
   ↓
2. Размер / этажность / роль
   ↓
3. Визуальный reference
   ↓
4. Astra строит editable модель в Blender
   ↓
5. Проверка формы и пропорций в Blender
   ↓
6. FBX export
   ↓
7. Import как Static Mesh в UE5
   ↓
8. Проверка рядом с персонажем и другими зданиями
   ↓
9. Правка исходного .blend
   ↓
10. Re-export / Reimport
~~~

На текущем этапе это **blockout / city mockup workflow**, а не pipeline финальных production assets.

## Правила для blockout-моделей

В Blender важнее всего:

- правильный footprint;
- этажность;
- высота;
- общий силуэт;
- окна и входы в правильном масштабе;
- крыша и крупные архитектурные элементы;
- понятная структура объектов.

Пока не нужны:

- полноценные интерьеры;
- high-poly;
- сложная UV-развёртка;
- production textures;
- игровые двери;
- сложная collision setup;
- финальные LOD.

Исходный .blend должен оставаться редактируемым. Если для UE нужен единый mesh, объединение выполняется только на экспортной копии / этапе экспорта.

## Организация Blender-сцены

Для каждого здания желательно:

~~~text
BLD_BuildingName
└── BuildingName_ROOT
    ├── Walls
    ├── Roof
    ├── Windows
    ├── Doors
    ├── Trim
    └── Props
~~~

ROOT:

- находится в центре здания на уровне земли;
- используется для перемещения всей сборки;
- все части здания parent'ятся к нему.

Перед экспортом:

- ground min Z = 0;
- Rotation / Scale применены;
- нормали проверены;
- экспортируется только здание;
- Camera / Light / helper objects не экспортируются.

## Blender и Unreal выглядят по-разному

Это важный вывод первого импорта общежития.

Один и тот же объект может заметно отличаться визуально из-за:

- Blender AgX / viewport lighting;
- UE tonemapper и exposure;
- Directional Light / SkyLight / Atmosphere;
- отличий Blender shader nodes от UE materials;
- ограниченного переноса материалов через FBX.

Поэтому:

**геометрию и базовую палитру удобно создавать в Blender, но финальный внешний вид здания оценивается в UE5.**

Для blockout желательно использовать простые материалы:

- Base Color;
- Roughness;
- Metallic;
- минимум сложных Blender-only shader effects.

Позже полезно сделать отдельный UE level L_BuildingPreview с фиксированным светом и exposure, чтобы все здания сравнивались в одинаковых условиях.

## Первый проверенный asset — Dormitory

Первый полный тест pipeline:

~~~text
reference
→ Astra + Blender MCP
→ editable .blend
→ FBX
→ UE Static Mesh
→ размещение на Level_6
~~~

Текущие source / export:

- Content/TestLevel/Level_6/Blender/Source/Dormitory_Blockout.blend
- Content/TestLevel/Level_6/Blender/Source/SM_Dormitory_Blockout.fbx
- UE asset: /Game/TestLevel/Level_6/Blender/SM_Dormitory_Blockout

Технические размеры и параметры импорта находятся в:

- Content/TestLevel/Level_6/Blender/README.md

## Важный художественный вывод

Первый вариант общежития с плоской крышей, кондиционерами и техническим оборудованием визуально получился слишком похожим на современную школу / административное здание.

После правки текущая модель получила:

- тёплый кирпич;
- светлую каменную отделку;
- тёмную скатную крышу;
- центральное крыльцо;
- более спокойный университетский характер.

Правило для campus-зданий:

~~~text
University = богатый исторический landmark
Dormitory = более простой функциональный родственник того же ансамбля
~~~

При этом не нужно буквально копировать архитектуру университета.
