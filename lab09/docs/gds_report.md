# Аналіз графа та продуктивність (ЛР 9, результат 4)

Плагін Graph Data Science 2026.10.2. Проєкція `kms`: 307 вузлів, 1000 зв'язків (усі мітки й типи, неорієнтований граф). Параметри: PageRank — dampingFactor 0.85, maxIterations 20; обидва алгоритми з concurrency 1 для відтворюваності.

## PageRank — топ-10

| id | name | label | pagerank |
|---|---|---|---|
| wf-karpatska | ВЕС «Карпатська» | Plant | 5.907 |
| rule-storm-stop | Зупинка при штормовому вітрі | ControlRule | 5.017 |
| wf-sambir | ВЕС «Самбірська» | Plant | 4.767 |
| wf-uzhok | ВЕС «Ужоцька» | Plant | 4.572 |
| wt-u05 | ВЕУ U-05 | Equipment | 3.762 |
| wt-k02 | ВЕУ K-02 | Equipment | 3.326 |
| sp-kolomyia | СЕС «Коломия» | Plant | 3.292 |
| wt-k08 | ВЕУ K-08 | Equipment | 3.227 |
| sp-mukachevo | СЕС «Мукачево» | Plant | 3.068 |
| wt-u01 | ВЕУ U-01 | Equipment | 3.065 |

## Louvain — спільноти (усього 10, модульність 0.708)

| communityId | size | plants | sample |
|---|---|---|---|
| 138 | 58 | ВЕС «Карпатська» | rotor-k01, gearbox-k01, generator-k01, rotor-k02, gearbox-k02, generator-k02 |
| 106 | 44 | ВЕС «Ужоцька» | rotor-u01, gearbox-u01, generator-u01, rotor-u02, gearbox-u02, generator-u02 |
| 96 | 38 | ВЕС «Самбірська» | rotor-s01, gearbox-s01, generator-s01, rotor-s02, gearbox-s02, generator-s02 |
| 115 | 29 | СЕС «Галич-1» | co-halych-solar, emp-boiko, emp-kravets, tr-halych, inv-h01, pv-h01 |
| 164 | 28 |  | rotor-s03, gearbox-s03, generator-s03, rotor-u05, gearbox-u05, generator-u05 |
| 133 | 26 | СЕС «Мукачево» | co-karpaty-energy, rule-inverter-derate, emp-fedak, emp-lukach, emp-bilyk, tr-mukachevo |
| 69 | 25 |  | co-zakhid-vde, rotor-u04, gearbox-u04, generator-u04, emp-kovalchuk, emp-hnatiuk |
| 168 | 24 |  | rotor-k08, gearbox-k08, generator-k08, rotor-s05, gearbox-s05, generator-s05 |
| 123 | 24 | СЕС «Коломия» | sub-lviv, sub-ivano-frankivsk, sub-zakarpattia, tr-kolomyia, inv-kl01, pv-kl01 |
| 170 | 11 |  | rotor-k06, gearbox-k06, generator-k06, emp-melnyk, wt-k06, tmp-k06 |

## Інтерпретація

1. Найвищий PageRank має вузол «ВЕС «Карпатська»» (Plant): це центр, до якого сходиться найбільше зв'язків INSTALLED_AT, OPERATED_BY і FORECAST_FOR, тому він найважливіший для навігації в базі знань.
2. У топ-10 потрапили 5 станції (ВЕС «Карпатська», ВЕС «Самбірська», ВЕС «Ужоцька», СЕС «Коломия», СЕС «Мукачево»): станції є головними «вузлами-агрегаторами» знань, через які пов'язані обладнання, прогнози та компанії.
3. Серед лідерів є вузли типів ControlRule, Equipment, Plant; правило керування з великою кількістю зв'язків CONTROLS має високий PageRank, бо стосується багатьох турбін одночасно — зміна такого правила впливає на всю станцію.
4. Турбіни з високим рейтингом — ті, навколо яких накопичено найбільше подій, ремонтів і вимірювань; вони є першими кандидатами для предиктивного обслуговування та детального аналізу причин відмов.
5. Louvain розбив граф на 10 спільнот із модульністю 0.708: найбільша містить 58 вузлів (ВЕС «Карпатська»). Спільноти здебільшого збігаються зі станціями та їхнім обладнанням, а окремі спільноти утворюють персонал із ремонтами та ланцюжки «сигнал → відмова → ремонт».
6. Для управління знаннями це означає, що граф природно ділиться на «острови знань» за станціями, а зв'язки між ними проходять через компанії, спільні правила керування та запчастини — саме ці вузли варто документувати найретельніше.

Результати збережено у графі як властивості вузлів `pagerank` і `community`:

| nodesWithResults | communities |
|---|---|
| 307 | 10 |

## PROFILE

### Запит 1 — q03 (критичні події з червня 2026), оптимізація індексом `event_occurred_at`

| Стан | dbHits | Рядків | Час, мс | Оператори (план) |
|---|---|---|---|---|
| до (індекс видалено) | 120 | 4 | 2 | ProduceResults → Projection → CacheProperties → Sort → Projection → Filter → Expand(All) → Filter → Expand(All) → Filter → NodeByLabelScan |
| після (індекс створено) | 89 | 4 | 5 | ProduceResults → Projection → CacheProperties → Filter → Expand(All) → Filter → Expand(All) → Filter → NodeIndexSeekByRange |

Кількість звернень до бази зменшилась з 120 до 89 (26 %). Без індексу планувальник перебирає всі вузли :Event і фільтрує їх; з індексом — одразу знаходить події в діапазоні дат.

### Запит 2 — q09 (аналіз впливу, DEPENDS_ON*1..4)

| dbHits | Рядків | Час, мс | Оператори (план) |
|---|---|---|---|
| 290 | 7 | 4 | ProduceResults → Sort → EagerAggregation → Projection → Filter → Expand(All) → Filter → VarLengthExpand(All) → Filter → NodeByLabelScan |

Запит починається з вузла підстанції, знайденого за унікальним `id` (індекс обмеження), і розгортає шлях змінної довжини лише назад по DEPENDS_ON, тому кількість звернень залишається малою навіть для глибини 4.
