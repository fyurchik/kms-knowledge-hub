# Запити Cypher (ЛР 9, результат 3)

Кожен запит виконано в Neo4j; результат автоматично звірено з незалежним розрахунком на Python (`scripts/expected.py`, рахує прямо з CSV без Cypher).

| Запит | CQ | Рядків | Час, мс | Звірка з незалежним розрахунком |
|---|---|---|---|---|
| q01 | CQ1 | 5 | 76.2 | збігається |
| q02 | CQ2 | 5 | 115.2 | збігається |
| q03 | CQ3 | 4 | 30.4 | збігається |
| q04 | CQ4 | 7 | 69.1 | збігається |
| q05 | CQ5 | 8 | 55.2 | збігається |
| q06 | CQ6 | 1 | 57.8 | збігається |
| q07 | CQ7 | 7 | 95.5 | збігається |
| q08 | CQ8 | 5 | 71.2 | збігається |
| q09 | CQ9 (аналіз впливу) | 7 | 43.9 | збігається |
| q10 | CQ10 (аналіз впливу) | 10 | 101.8 | збігається |

## q01. CQ1. Яке обладнання встановлено на ВЕС «Карпатська» і яка сумарна потужність за типами?

*Конструкції: шаблон з властивістю, агрегація count/sum, coalesce, ORDER BY*

```cypher
MATCH (e:Equipment)-[:INSTALLED_AT]->(p:Plant {id: 'wf-karpatska'})
RETURN e.kind AS kind, count(e) AS units, sum(coalesce(e.ratedPowerKW, 0)) AS totalKW
ORDER BY totalKW DESC, kind
```

| kind | units | totalKW |
|---|---|---|
| Transformer | 1 | 63000 |
| WindTurbine | 8 | 52800 |
| BatteryStorage | 1 | 2500 |
| Anemometer | 1 | 0 |
| TemperatureSensor | 8 | 0 |

**Інтерпретація.** На ВЕС «Карпатська» встановлено 19 одиниць обладнання п'яти типів. Генеруюча потужність станції — вісім турбін Siemens Gamesa по 6,6 МВт (52,8 МВт); трансформатор 63 МВА розрахований з запасом. Датчики потужності не мають, тому їхній внесок нульовий — це видно завдяки coalesce(). Запит дає інженеру повний перелік активів станції однією таблицею.

Звірка: збігається.

## q02. CQ2. Які датчики контролюють турбіни ВЕС «Карпатська» і яке їхнє останнє вимірювання?

*Конструкції: OPTIONAL MATCH, WITH + ORDER BY + collect()[0] (останнє значення), LIMIT*

```cypher
MATCH (t:WindTurbine)-[:INSTALLED_AT]->(:Plant {id: 'wf-karpatska'})
OPTIONAL MATCH (s:Sensor)-[:OBSERVES]->(t)
OPTIONAL MATCH (m:Measurement)-[:MEASURED_BY]->(s)
WITH t, s, m ORDER BY m.observedAt DESC
WITH t, s, collect(m)[0] AS last
RETURN t.id AS turbine, s.id AS sensor, last.value AS lastValue, last.unit AS unit
ORDER BY lastValue DESC, turbine
LIMIT 5
```

| turbine | sensor | lastValue | unit |
|---|---|---|---|
| wt-k02 | tmp-k02 | 88.5 | °C |
| wt-k07 | tmp-k07 | 76.3 | °C |
| wt-k05 | tmp-k05 | 73.5 | °C |
| wt-k04 | tmp-k04 | 71.8 | °C |
| wt-k08 | tmp-k08 | 70.3 | °C |

**Інтерпретація.** Найвищу останню температуру показує датчик турбіни K-02 — 88,5 °C, що перевищує поріг 85 °C у правилі керування rule-overheat. Решта турбін працюють у межах 70–76 °C. Так модель пов'язує поточні дані SCADA з конкретною турбіною і правилом, яке має спрацювати.

Звірка: збігається.

## q03. CQ3. Які події з критичністю ≥ 4 сталися з червня 2026 року, на якому обладнанні та станції?

*Конструкції: фільтр за діапазоном дат (індекс event_occurred_at), WHERE, ланцюг з двох зв'язків*

```cypher
MATCH (ev:Event)-[:AFFECTS]->(e:Equipment)-[:INSTALLED_AT]->(p:Plant)
WHERE ev.occurredAt >= localdatetime('2026-06-01T00:00:00') AND ev.severity >= 4
RETURN ev.id AS event, ev.kind AS kind, ev.severity AS severity, e.id AS equipment, p.name AS plant
ORDER BY ev.occurredAt DESC
```

| event | kind | severity | equipment | plant |
|---|---|---|---|---|
| ev-0001 | FailureEvent | 4 | wt-k02 | ВЕС «Карпатська» |
| ev-0007 | FailureEvent | 5 | wt-u04 | ВЕС «Ужоцька» |
| ev-0011 | FailureEvent | 4 | wt-k06 | ВЕС «Карпатська» |
| ev-0005 | FailureEvent | 5 | wt-s03 | ВЕС «Самбірська» |

**Інтерпретація.** З червня 2026 року сталося чотири відмови з критичністю 4–5: дві на ВЕС «Карпатська» (зокрема перегрів редуктора K-02) і по одній на «Ужоцькій» та «Самбірській». Усі критичні події — відмови, а не попереджувальні сигнали, що підтверджує коректність класифікації подій. Запит використовує індекс event_occurred_at (див. PROFILE).

Звірка: збігається.

## q04. CQ4. Хто виконував аварійні ремонти, скільки їх було і скільки вони коштували?

*Конструкції: агрегація count/sum, WITH + фільтр після агрегації, ORDER BY*

```cypher
MATCH (w:CorrectiveRepair)-[:PERFORMED_BY]->(emp:Employee)-[:EMPLOYED_BY]->(c:Company)
WITH emp, c, count(w) AS repairs, sum(w.costEUR) AS totalEUR
WHERE repairs >= 1
RETURN emp.name AS employee, c.name AS company, repairs, totalEUR
ORDER BY totalEUR DESC
```

| employee | company | repairs | totalEUR |
|---|---|---|---|
| Олег Ковальчук | ТОВ «Захід ВДЕ» | 2 | 10370 |
| Роман Данилюк | ТОВ «Захід ВДЕ» | 2 | 7950 |
| Андрій Бойко | ТОВ «Галич Солар» | 2 | 6200 |
| Софія Білик | ТОВ «Карпати Енерджі» | 2 | 4300 |
| Іван Попович | ТОВ «Карпати Енерджі» | 2 | 3655 |
| Ірина Мельник | ТОВ «Захід ВДЕ» | 1 | 1375 |
| Петро Кравець | ТОВ «Галич Солар» | 1 | 1220 |

**Інтерпретація.** Найбільше на аварійні ремонти витрачено роботами О. Ковальчука (10 370 EUR, зокрема ремонт редуктора K-02 за 8400 EUR). Витрати розподілені між трьома компаніями, що дозволяє оцінити навантаження на служби ТО. Фільтр WHERE після WITH застосовано вже до агрегованих значень.

Звірка: збігається.

## q05. CQ5. З чого складається ВЕС «Карпатська» на будь-якому рівні вкладеності (обладнання → вузли)?

*Конструкції: шлях змінної довжини *1..2 з кількома типами зв'язків, count(DISTINCT)*

```cypher
MATCH (p:Plant {id: 'wf-karpatska'})-[:INSTALLED_AT|HAS_PART*1..2]-(x)
WHERE x <> p
RETURN x.kind AS kind, count(DISTINCT x) AS cnt
ORDER BY cnt DESC, kind
```

| kind | cnt |
|---|---|
| Gearbox | 8 |
| Generator | 8 |
| Rotor | 8 |
| TemperatureSensor | 8 |
| WindTurbine | 8 |
| Anemometer | 1 |
| BatteryStorage | 1 |
| Transformer | 1 |

**Інтерпретація.** До складу ВЕС «Карпатська» на двох рівнях вкладеності входять 43 об'єкти: 19 одиниць обладнання та 24 вузли (по 8 роторів, редукторів і генераторів). Шлях змінної довжини замінює транзитивну властивість partOf з онтології: окреме правило виведення не потрібне.

Звірка: збігається.

## q06. CQ6. Як пов'язані відмова редуктора K-02 і підстанція «Львів-Західна» (найкоротший шлях)?

*Конструкції: shortestPath, неорієнтований шлях змінної довжини, nodes()/relationships()*

```cypher
MATCH (a:Event {id: 'ev-0001'}), (b:Substation {id: 'sub-lviv'})
MATCH path = shortestPath((a)-[*..6]-(b))
RETURN [n IN nodes(path) | n.id] AS chain, [r IN relationships(path) | type(r)] AS rels, length(path) AS hops
```

| chain | rels | hops |
|---|---|---|
| ev-0001, wt-k02, tr-karpatska, sub-lviv | AFFECTS, DEPENDS_ON, DEPENDS_ON | 3 |

**Інтерпретація.** Відмова ev-0001 пов'язана з підстанцією «Львів-Західна» ланцюгом довжиною 3: відмова → турбіна K-02 → трансформатор станції → підстанція. Найкоротший шлях пояснює, через які активи проблема на підстанції вплинула б на цю турбіну.

Звірка: збігається.

## q07. CQ7. Яке обладнання має технічний стан нижче 80 % і чи заплановано для нього ТО?

*Конструкції: фільтр за індексованою властивістю, OPTIONAL MATCH, WITH + count, CASE*

```cypher
MATCH (e:Equipment)-[:INSTALLED_AT]->(p:Plant)
WHERE e.stateOfHealth < 80
OPTIONAL MATCH (w:PlannedMaintenance)-[:TARGETS]->(e)
WITH e, p, count(w) AS planned
RETURN e.id AS equipment, e.kind AS kind, e.stateOfHealth AS health, p.name AS plant,
       CASE WHEN planned = 0 THEN 'немає ТО' ELSE 'ТО заплановано' END AS status
ORDER BY health, equipment
```

| equipment | kind | health | plant | status |
|---|---|---|---|---|
| inv-h02 | Inverter | 62 | СЕС «Галич-1» | ТО заплановано |
| wt-k03 | WindTurbine | 71 | ВЕС «Карпатська» | немає ТО |
| wt-u03 | WindTurbine | 71 | ВЕС «Ужоцька» | ТО заплановано |
| wt-u06 | WindTurbine | 73 | ВЕС «Ужоцька» | ТО заплановано |
| wt-k02 | WindTurbine | 74 | ВЕС «Карпатська» | немає ТО |
| wt-s05 | WindTurbine | 75 | ВЕС «Самбірська» | немає ТО |
| wt-k04 | WindTurbine | 79 | ВЕС «Карпатська» | немає ТО |

**Інтерпретація.** Сім одиниць обладнання мають стан нижче 80 %; для чотирьох із них (K-02, K-03, K-04, S-05) планове ТО не заплановано — це кандидати на першочергове обслуговування. Інвертор H-02 має найнижчий стан (62 %), але ТО для нього вже є. OPTIONAL MATCH зберігає обладнання без робіт у результаті.

Звірка: збігається.

## q08. CQ8. Які запчастини використовуються найчастіше і скільки на них витрачено?

*Конструкції: агрегація count/sum, ORDER BY, LIMIT*

```cypher
MATCH (w:MaintenanceWork)-[:USES_PART]->(sp:SparePart)
RETURN sp.name AS part, count(w) AS usedIn, sum(sp.unitCostEUR) AS partsCostEUR
ORDER BY usedIn DESC, part
LIMIT 5
```

| part | usedIn | partsCostEUR |
|---|---|---|
| Фільтр мастила | 10 | 950 |
| Мастило редукторне 20 л | 7 | 1260 |
| Кабель DC 6 мм², 50 м | 5 | 1050 |
| Підшипник вихідного вала | 3 | 7200 |
| IGBT-модуль інвертора | 2 | 2900 |

**Інтерпретація.** Найчастіше використовуються витратні матеріали — фільтр мастила (10 робіт) і редукторне мастило (7), а найбільші витрати припадають на підшипники вихідного вала (7200 EUR за 3 використання). Це підказує, які запчастини тримати на складі та де шукати економію.

Звірка: збігається.

## q09. CQ9 (аналіз впливу). Що зупиниться, якщо відмовить ПС «Івано-Франківськ»?

*Залежності до глибини 4: ФЕМ → інвертор → трансформатор → підстанція. Конструкції: шлях змінної довжини DEPENDS_ON*1..4, WITH, агрегація, CASE з перевіркою мітки*

```cypher
MATCH path = (x:Equipment)-[:DEPENDS_ON*1..4]->(s:Substation {id: 'sub-ivano-frankivsk'})
MATCH (x)-[:INSTALLED_AT]->(p:Plant)
WITH p, x, length(path) AS depth
RETURN p.name AS plant, x.kind AS kind, count(DISTINCT x) AS affectedUnits, max(depth) AS depth,
       sum(CASE WHEN x:GeneratingUnit THEN x.ratedPowerKW ELSE 0 END) AS lostGenerationKW
ORDER BY plant, depth, kind
```

| plant | kind | affectedUnits | depth | lostGenerationKW |
|---|---|---|---|---|
| СЕС «Галич-1» | Transformer | 1 | 1 | 0 |
| СЕС «Галич-1» | Inverter | 4 | 2 | 0 |
| СЕС «Галич-1» | PVArray | 4 | 3 | 12000 |
| СЕС «Коломия» | Transformer | 1 | 1 | 0 |
| СЕС «Коломия» | BatteryStorage | 1 | 2 | 0 |
| СЕС «Коломия» | Inverter | 4 | 2 | 0 |
| СЕС «Коломия» | PVArray | 4 | 3 | 9600 |

**Інтерпретація.** Відмова ПС «Івано-Франківськ» зупинить дві сонячні станції: «Галич-1» і «Коломия». Уражено 19 одиниць обладнання на глибині до 3 зв'язків, а втрата генерації становить 21,6 МВт (12,0 + 9,6). Запит показує ланцюг залежностей ФЕМ → інвертор → трансформатор → підстанція, якого немає в жодній таблиці окремо.

Звірка: збігається.

## q10. CQ10 (аналіз впливу). Які запчастини і витрати спричинили попереджувальні сигнали,

*що переросли у відмови? Ланцюг глибиною 3: сигнал ← відмова ← ремонт → запчастина. Конструкції: шлях фіксованої довжини 3, length(), WITH, агрегація, collect(DISTINCT)*

```cypher
MATCH path = (a:AlarmEvent)<-[:CAUSED_BY]-(f:FailureEvent)<-[:TRIGGERED_BY]-(w:MaintenanceWork)-[:USES_PART]->(sp:SparePart)
WITH sp, length(path) AS depth, count(DISTINCT a) AS alarms, collect(DISTINCT f.id) AS failures
RETURN sp.name AS part, alarms, size(failures) AS failuresCnt, depth
ORDER BY alarms DESC, part
```

| part | alarms | failuresCnt | depth |
|---|---|---|---|
| Мастило редукторне 20 л | 3 | 3 | 3 |
| Підшипник вихідного вала | 3 | 3 | 3 |
| Вентилятор охолодження | 2 | 2 | 3 |
| Датчик температури PT100 | 2 | 2 | 3 |
| Привід кута атаки | 2 | 2 | 3 |
| Щітки генератора | 2 | 2 | 3 |
| IGBT-модуль інвертора | 1 | 1 | 3 |
| Запобіжник DC 1500 В | 1 | 1 | 3 |
| Кабель DC 6 мм², 50 м | 1 | 1 | 3 |
| Фільтр мастила | 1 | 1 | 3 |

**Інтерпретація.** Найбільше відмов, що почалися з попереджувальних сигналів, вимагали мастила редукторного та підшипників вихідного вала (по 3 ланцюжки). Отже, сигнали перегріву та вібрації редукторів — головне джерело витрат, і саме на них варто налаштувати предиктивне обслуговування. Глибина аналізу — 3 зв'язки (сигнал ← відмова ← ремонт → запчастина).

Звірка: збігається.

## Ручна перевірка трьох запитів на малому підграфі

**q01 (склад ВЕС «Карпатська»).** У `data/rels_installed_at.csv` до `wf-karpatska` ведуть 19 рядків: `tr-karpatska`, `wt-k01…wt-k08` (8), `anm-k01`, `tmp-k01…tmp-k08` (8), `bess-k01`. Сума потужностей: 63000 + 8 × 6600 + 2500 = 118 300 кВт, з них турбіни — 52 800 кВт. Збігається з результатом.

**q06 (найкоротший шлях).** Підграф: `ev-0001 –AFFECTS→ wt-k02`, `wt-k02 –DEPENDS_ON→ tr-karpatska`, `tr-karpatska –DEPENDS_ON→ sub-lviv`. Шлях довжини 3 існує. Шляху довжини 2 немає: сусіди `ev-0001` — `wt-k02`, `rec-0001`, `ev-0002`, `mw-0001`; жоден із них не з'єднаний із `sub-lviv` напряму. Збігається.

**q09 (вплив ПС «Івано-Франківськ»).** До `sub-ivano-frankivsk` ведуть `DEPENDS_ON` від `tr-halych` і `tr-kolomyia` (глибина 1); до трансформаторів — від `inv-h01…h04`, `inv-kl01…kl04` і `bess-kl01` (глибина 2); до інверторів — від `pv-h01…h04`, `pv-kl01…kl04` (глибина 3). Разом 2 + 9 + 8 = 19 одиниць; потужність ФЕМ: 4 × 3000 + 4 × 2400 = 21 600 кВт. Збігається.
