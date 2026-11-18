# Імпорт, обмеження та індекси (ЛР 9, результат 2)

Сервер: Neo4j Kernel 2026.10.2 (enterprise), база `neo4j`. Дата запуску: 2026-11-18T14:14:06.

## Обмеження (SHOW CONSTRAINTS)

| name | type | labelsOrTypes | properties |
|---|---|---|---|
| employee_email_unique | NODE_PROPERTY_UNIQUENESS | Employee | email |
| entity_id_unique | NODE_PROPERTY_UNIQUENESS | Entity | id |
| record_number_unique | NODE_PROPERTY_UNIQUENESS | Record | number |

## Індекси (SHOW INDEXES)

| name | type | labelsOrTypes | properties | state |
|---|---|---|---|---|
| employee_email_unique | RANGE | Employee | email | ONLINE |
| entity_id_unique | RANGE | Entity | id | ONLINE |
| entity_name_text | TEXT | Entity | name | ONLINE |
| equipment_health | RANGE | Equipment | stateOfHealth | ONLINE |
| event_occurred_at | RANGE | Event | occurredAt | ONLINE |
| index_1b9dcc97 | LOOKUP | — | — | ONLINE |
| index_460996c0 | LOOKUP | — | — | ONLINE |
| measurement_observed_at | RANGE | Measurement | observedAt | ONLINE |
| record_number_unique | RANGE | Record | number | ONLINE |

Обмежень унікальності: 3 (вимога ≥ 2); індексів, створених вручну
(крім індексів, що підтримують обмеження, та службових LOOKUP): 4 (вимога ≥ 2).

## Кількість вузлів і зв'язків, ідемпотентність

| Етап | Вузлів | Зв'язків | Час, с |
|---|---|---|---|
| до імпорту | 307 | 500 | — |
| після першого імпорту | 307 | 500 | 3.28 |
| після повторного імпорту | 307 | 500 | 2.0 |

Граф містить **307 вузлів** (вимога ≥ 100) і **500 зв'язків** (вимога ≥ 200). Повторний запуск тих самих
скриптів **не змінив** кількості — імпорт ідемпотентний:
вузли створюються через `MERGE (n:Entity {id: row.id})`, зв'язки — через `MERGE (a)-[r:TYPE]->(b)`.

### Розподіл за мітками

| label | cnt |
|---|---|
| Entity | 307 |
| Equipment | 81 |
| Component | 60 |
| Measurement | 52 |
| GeneratingUnit | 32 |
| Event | 28 |
| MaintenanceWork | 28 |
| Sensor | 26 |
| Gearbox | 20 |
| Generator | 20 |
| Rotor | 20 |
| TemperatureSensor | 20 |
| WindTurbine | 20 |
| PlannedMaintenance | 16 |
| CorrectiveRepair | 12 |
| Employee | 12 |
| FailureEvent | 12 |
| Inverter | 12 |
| PVArray | 12 |
| AlarmEvent | 11 |
| SparePart | 10 |
| Record | 7 |
| Forecast | 6 |
| Plant | 6 |
| Transformer | 6 |
| WeatherData | 6 |
| CurtailmentEvent | 5 |
| ControlRule | 4 |
| Anemometer | 3 |
| Company | 3 |
| Pyranometer | 3 |
| Region | 3 |
| SolarPlant | 3 |
| Substation | 3 |
| WindFarm | 3 |
| BatteryStorage | 2 |
| GridNode | 1 |

### Розподіл за типами зв'язків

| type | cnt |
|---|---|
| INSTALLED_AT | 78 |
| HAS_PART | 60 |
| DEPENDS_ON | 55 |
| MEASURED_BY | 52 |
| CONTROLS | 42 |
| USES_PART | 37 |
| AFFECTS | 28 |
| PERFORMED_BY | 28 |
| TARGETS | 28 |
| OBSERVES | 26 |
| EMPLOYED_BY | 12 |
| TRIGGERED_BY | 12 |
| CAUSED_BY | 11 |
| DOCUMENTED_IN | 7 |
| BASED_ON | 6 |
| FORECAST_FOR | 6 |
| LOCATED_IN | 6 |
| OPERATED_BY | 6 |

## Порушення обмеження

Запит (`import/05_constraint_violation.cypher`):

```cypher
CREATE (:Entity:Plant {id: 'wf-karpatska', name: 'Дублікат ВЕС «Карпатська»'});
```

Результат: помилка

```
Neo.ClientError.Schema.ConstraintValidationFailed
Node(275) already exists with label `Entity` and property `id` = 'wf-karpatska'
```

Кількість вузлів після спроби: 307 — дублікат не створено.
