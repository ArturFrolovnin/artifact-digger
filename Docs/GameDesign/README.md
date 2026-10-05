# ArcheoDig — Game Design Documentation

Эта папка хранит **текущую рабочую модель игры**.

После обсуждений 2026-09-27 большой `ScenarioIdeas.md` был разделён по областям: город, персонажи и системы уже перестали быть просто набором сырых идей.

## Статусы

- **Working model** — сформулированное текущее решение, которое ещё можно менять.
- **Approved scenario** — утверждённые сюжетные решения.
- **Ideas / Open questions** — то, что ещё обсуждается.

## Структура

```text
GameDesign/
├── README.md
├── References.md
├── Story/
│   ├── Scenario.md
│   ├── ScenarioIdeas.md
│   └── Lore.md
├── World/
│   ├── Town.md
│   └── DigSites.md
├── Buildings/
│   ├── README.md
│   ├── Dimensions.md
│   ├── StyleGuide.md
│   ├── BlenderWorkflow.md
│   ├── University.md
│   ├── Dormitory.md
│   └── References/
│       └── README.md
├── Characters/
│   ├── README.md
│   └── RudyDexon.md
├── Systems/
│   ├── Economy.md
│   ├── Progression.md
│   ├── Expeditions.md
│   ├── Relationships.md
│   └── Museum.md
└── Archive/
    └── ScenarioIdeas_2026-09-27.md
```

## Куда писать дальше

- общая планировка города / районы / связи → `World/Town.md`
- размеры, этажность и внешний стиль конкретных зданий → `Buildings/`
- Blender → UE5 workflow для макетов зданий → `Buildings/BlenderWorkflow.md`
- раскопочные уровни → `World/DigSites.md`
- важный NPC → отдельный файл в `Characters/`
- общие отношения → `Systems/Relationships.md`
- деньги → `Systems/Economy.md`
- характеристики героя → `Systems/Progression.md`
- travel / loadout / rescue → `Systems/Expeditions.md`
- музей → `Systems/Museum.md`
- сюжет → `Story/`
- референсы → `References.md`

Не создавать отдельный файл на каждое здание, пока оно не разрослось в самостоятельную систему.
