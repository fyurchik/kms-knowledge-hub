# Графова схема під CQ (ЛР 9, результат 1)

Домен: управління відновлюваними ресурсами (варіант 21). Модель — LPG (labeled property graph) у Neo4j 5.

Діаграма схеми: `docs/graph_schema.png` (джерело `docs/graph_schema.dot`).

## 1. Мітки та типи зв'язків

**15 міток вузлів:** `Region`, `Company`, `GridNode`, `Plant`, `Equipment`, `Component`, `Measurement`, `Event`,
`MaintenanceWork`, `Employee`, `SparePart`, `Record`, `Forecast`, `WeatherData`, `ControlRule`.
Додаткові мітки-підтипи задаються полем `kind`: `:WindFarm`, `:SolarPlant`, `:WindTurbine`, `:PVArray`,
`:GeneratingUnit`, `:Inverter`, `:Transformer`, `:Substation`, `:BatteryStorage`, `:Sensor`, `:Anemometer`,
`:Pyranometer`, `:TemperatureSensor`, `:Rotor`, `:Gearbox`, `:Generator`, `:FailureEvent`, `:AlarmEvent`,
`:CurtailmentEvent`, `:CorrectiveRepair`, `:PlannedMaintenance`. Усі вузли також мають мітку `:Entity`
з унікальним `id` — це спрощує імпорт зв'язків і гарантує цілісність.

**18 типів зв'язків:** `LOCATED_IN`, `OPERATED_BY`, `INSTALLED_AT`, `HAS_PART`, `DEPENDS_ON`, `OBSERVES`,
`MEASURED_BY`, `AFFECTS`, `CAUSED_BY`, `DOCUMENTED_IN`, `TARGETS`, `PERFORMED_BY`, `TRIGGERED_BY`, `USES_PART`,
`EMPLOYED_BY`, `FORECAST_FOR`, `BASED_ON`, `CONTROLS`.

## 2. Властивості походження на зв'язках

Кожен зв'язок має три властивості:

| Властивість | Тип | Призначення | Приклад |
|---|---|---|---|
| `source` | рядок | система або документ, з якого взято зв'язок | `scada`, `cmms`, `onto-lab06`, `hr-register`, `forecast-model` |
| `confidence` | число 0–1 | довіра до зв'язку | `1.0` для паспортних даних, `0.6–0.95` для `CAUSED_BY` (причинність встановлено аналізом) |
| `validFrom` | дата | з якої дати зв'язок чинний | дата події, ремонту, вимірювання; `2026-01-01` для статичних зв'язків |

## 3. Компетентнісні питання → шаблони шляхів Cypher

| CQ | Питання | Шаблон шляху | Запит |
|---|---|---|---|
| CQ1 | Яке обладнання встановлено на станції і якої потужності? | `(e:Equipment)-[:INSTALLED_AT]->(p:Plant)` | `q01` |
| CQ2 | Які датчики контролюють турбіни та яке їхнє останнє вимірювання? | `(t:WindTurbine)<-[:OBSERVES]-(s:Sensor)<-[:MEASURED_BY]-(m:Measurement)` | `q02` |
| CQ3 | Які критичні події сталися за період і де? | `(ev:Event)-[:AFFECTS]->(e:Equipment)-[:INSTALLED_AT]->(p:Plant)` | `q03` |
| CQ4 | Хто виконував аварійні ремонти і скільки вони коштували? | `(w:CorrectiveRepair)-[:PERFORMED_BY]->(emp:Employee)-[:EMPLOYED_BY]->(c:Company)` | `q04` |
| CQ5 | З чого складається станція на будь-якій глибині? | `(p:Plant)-[:INSTALLED_AT\|HAS_PART*1..2]-(x)` | `q05` |
| CQ6 | Як пов'язані подія і підстанція? | `shortestPath((ev:Event)-[*..6]-(s:Substation))` | `q06` |
| CQ7 | Яке обладнання в поганому стані і чи заплановано ТО? | `(e:Equipment)` + `OPTIONAL (w:PlannedMaintenance)-[:TARGETS]->(e)` | `q07` |
| CQ8 | Які запчастини використовуються найчастіше? | `(w:MaintenanceWork)-[:USES_PART]->(sp:SparePart)` | `q08` |
| CQ9 | Що зупиниться при відмові підстанції? (вплив) | `(x:Equipment)-[:DEPENDS_ON*1..4]->(s:Substation)` | `q09` |
| CQ10 | Які запчастини спричинили сигнали, що переросли у відмови? (вплив) | `(a:AlarmEvent)<-[:CAUSED_BY]-(f:FailureEvent)<-[:TRIGGERED_BY]-(w)-[:USES_PART]->(sp)` | `q10` |

## 4. Порівняння з онтологією ЛР 6–7

| Елемент онтології (OWL) | Елемент графа (LPG) | Рішення та причина |
|---|---|---|
| клас `res:PowerPlant`, підкласи `WindFarm`, `SolarPlant` | мітка `:Plant` + додаткова мітка `:WindFarm`/`:SolarPlant` | ієрархія класів → набір міток на вузлі; запит за загальною міткою знаходить усі підтипи без reasoner'а |
| клас `res:Equipment` і 9 підкласів | мітка `:Equipment` + підтипні мітки, поле `kind` | глибоку ієрархію сплющено до двох рівнів міток; `kind` зручний для групування в агрегаціях |
| об'єктна властивість `res:installedAt` | тип зв'язку `INSTALLED_AT` | об'єктні властивості → типи зв'язків (UPPER_SNAKE_CASE) |
| датна властивість `res:stateOfHealth`, `res:ratedPowerKW` | властивості вузла `stateOfHealth`, `ratedPowerKW` | датні властивості → властивості вузлів; для `stateOfHealth` створено індекс |
| `res:partOf` / `res:hasPart` (обернені, транзитивні) | один напрямлений зв'язок `HAS_PART` | в LPG обернені властивості не потрібні: зв'язок проходиться в обидва боки; транзитивність замінено шляхом змінної довжини `*1..n` |
| клас `res:MaintenanceRecord` | мітка `:Record` з унікальним `number` | номер акта став ключем з обмеженням унікальності |
| клас `res:Region` (`schema:Place`) | мітка `:Region` | зовнішні суперкласи (schema.org, FOAF, PROV-O) в LPG не відтворюються — це втрата семантичної сумісності |
| `owl:AllDisjointClasses` | — | диз'юнктність в Neo4j не задається; контролюється на рівні імпорту (кожен CSV-файл дає одну основну мітку) |
| `owl:qualifiedCardinality` (`measuredBy exactly 1`) | — | кардинальність не задається схемою Community Edition; перевіряється запитом (див. `import/04_checks.cypher`) |
| — (нове) | зв'язки `DEPENDS_ON`, `CAUSED_BY`, `USES_PART`, мітки `:SparePart`, `:GridNode` | додано для аналізу впливу (CQ9, CQ10), якого не було в онтології |
| — (нове) | властивості зв'язків `source`, `confidence`, `validFrom` | в OWL для цього потрібна реїфікація або RDF-star; в LPG властивості зв'язку — природна частина моделі |
