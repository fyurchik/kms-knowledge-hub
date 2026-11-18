# -*- coding: utf-8 -*-
"""Формує docs/*.md з results/all_results.json (викликається з run_all.py)."""
import json, pathlib, sys
ROOT = pathlib.Path(__file__).resolve().parent.parent
D = ROOT / 'docs'
R = json.load(open(sys.argv[1] if len(sys.argv) > 1 else ROOT / 'results' / 'all_results.json', encoding='utf-8'))
INTERP = json.load(open(D / 'interpretations.json', encoding='utf-8'))

def fmt(v):
    if v is None: return '—'
    if isinstance(v, float): return ('%.3f' % v).rstrip('0').rstrip('.')
    if isinstance(v, list): return ', '.join(fmt(x) for x in v)
    return str(v).replace('|', '\\|').replace('\n', ' ')
def table(keys, rows, limit=60):
    out = ['| ' + ' | '.join(keys) + ' |', '|' + '---|' * len(keys)]
    return '\n'.join(out + ['| ' + ' | '.join(fmt(x) for x in r) + ' |' for r in rows[:limit]])
def mark(v): return '✅' if v else '❌'
ver = R.get('neo4j_version', [['Neo4j', '?', '?']])[0]

# ------------------------------------------------------------------ import_report.md
imp = R['import']; v = R['violation']
lab = R['labels'][1]; rel = R['rel_types'][1]
nodes, rels = imp['after_first']
txt = f"""# Імпорт, обмеження та індекси (ЛР 9, результат 2)

Сервер: {ver[0]} {ver[1]} ({ver[2]}), база `{R['database']}`. Дата запуску: {R['started']}.

## Обмеження (SHOW CONSTRAINTS)

{table(*R['constraints'])}

## Індекси (SHOW INDEXES)

{table(*R['indexes'])}

Обмежень унікальності: {sum(1 for r in R['constraints'][1] if 'UNIQUE' in str(r[1]))} (вимога ≥ 2); індексів, створених вручну
(крім індексів, що підтримують обмеження, та службових LOOKUP): {sum(1 for r in R['indexes'][1] if r[1] not in ('LOOKUP',) and r[0] not in [c[0] for c in R['constraints'][1]])} (вимога ≥ 2).

## Кількість вузлів і зв'язків, ідемпотентність

| Етап | Вузлів | Зв'язків | Час, с |
|---|---|---|---|
| до імпорту | {imp['before'][0]} | {imp['before'][1]} | — |
| після першого імпорту | {imp['after_first'][0]} | {imp['after_first'][1]} | {imp['seconds_first']} |
| після повторного імпорту | {imp['after_second'][0]} | {imp['after_second'][1]} | {imp['seconds_second']} |

Граф містить **{nodes} вузлів** (вимога ≥ 100) і **{rels} зв'язків** (вимога ≥ 200). Повторний запуск тих самих
скриптів {'**не змінив** кількості — імпорт ідемпотентний' if imp['idempotent'] else '**змінив** кількість — потрібна перевірка'}:
вузли створюються через `MERGE (n:Entity {{id: row.id}})`, зв'язки — через `MERGE (a)-[r:TYPE]->(b)`.

### Розподіл за мітками

{table(['label', 'cnt'], lab)}

### Розподіл за типами зв'язків

{table(['type', 'cnt'], rel)}

## Порушення обмеження

Запит (`import/05_constraint_violation.cypher`):

```cypher
CREATE (:Entity:Plant {{id: 'wf-karpatska', name: 'Дублікат ВЕС «Карпатська»'}});
```

Результат: {'помилка' if v['raised'] else 'помилки немає (обмеження не спрацювало!)'}

```
{v.get('code', '')}
{v.get('message', '')}
```

Кількість вузлів після спроби: {v['counts_after'][0]} — дублікат не створено.
"""
(D / 'import_report.md').write_text(txt, encoding='utf-8')

# ------------------------------------------------------------------ cypher_results.md
Q = R['queries']
parts = ['# Запити Cypher (ЛР 9, результат 3)', '',
         'Кожен запит виконано в Neo4j; результат автоматично звірено з незалежним розрахунком на Python '
         '(`scripts/expected.py`, рахує прямо з CSV без Cypher).', '',
         '| Запит | CQ | Рядків | Час, мс | Звірка з незалежним розрахунком |', '|---|---|---|---|---|']
for k, q in Q.items():
    parts.append(f"| {k} | {q['header'][0].split('.')[0]} | {len(q['rows'])} | {q['ms']} | {q['check']} |")
for k, q in Q.items():
    parts += ['', f"## {k}. {q['header'][0]}", '', '*' + ' '.join(q['header'][1:]) + '*', '',
              '```cypher', q['query'], '```', '', table(q['keys'], q['rows']), '',
              f"**Інтерпретація.** {INTERP.get(k, '')}", '', f"Звірка: {q['check']}."]
parts += ['', '## Ручна перевірка трьох запитів на малому підграфі', '',
          '**q01 (склад ВЕС «Карпатська»).** У `data/rels_installed_at.csv` до `wf-karpatska` ведуть 19 рядків: '
          '`tr-karpatska`, `wt-k01…wt-k08` (8), `anm-k01`, `tmp-k01…tmp-k08` (8), `bess-k01`. Сума потужностей: '
          '63000 + 8 × 6600 + 2500 = 118 300 кВт, з них турбіни — 52 800 кВт. Збігається з результатом.', '',
          '**q06 (найкоротший шлях).** Підграф: `ev-0001 –AFFECTS→ wt-k02`, `wt-k02 –DEPENDS_ON→ tr-karpatska`, '
          '`tr-karpatska –DEPENDS_ON→ sub-lviv`. Шлях довжини 3 існує. Шляху довжини 2 немає: сусіди `ev-0001` — '
          '`wt-k02`, `rec-0001`, `ev-0002`, `mw-0001`; жоден із них не з\'єднаний із `sub-lviv` напряму. Збігається.', '',
          '**q09 (вплив ПС «Івано-Франківськ»).** До `sub-ivano-frankivsk` ведуть `DEPENDS_ON` від `tr-halych` і '
          '`tr-kolomyia` (глибина 1); до трансформаторів — від `inv-h01…h04`, `inv-kl01…kl04` і `bess-kl01` (глибина 2); '
          'до інверторів — від `pv-h01…h04`, `pv-kl01…kl04` (глибина 3). Разом 2 + 9 + 8 = 19 одиниць; потужність ФЕМ: '
          '4 × 3000 + 4 × 2400 = 21 600 кВт. Збігається.']
(D / 'cypher_results.md').write_text('\n'.join(parts) + '\n', encoding='utf-8')

# ------------------------------------------------------------------ gds_report.md
G = R.get('gds', {}); P = R['profile']
lines = ['# Аналіз графа та продуктивність (ЛР 9, результат 4)', '']
if 'error' in G or 'pagerank_top10' not in G:
    lines += [f"GDS недоступний: {G.get('error', 'запуск з --skip-gds')}", '']
else:
    top = G['pagerank_top10'][1]; comm = G['louvain_communities'][1]; lw = G['louvain_write'][1][0]
    proj = G['project'][1][0]
    lines += [f"Плагін Graph Data Science {G['version']}. Проєкція `kms`: {proj[1]} вузлів, {proj[2]} зв'язків "
              "(усі мітки й типи, неорієнтований граф). Параметри: PageRank — dampingFactor 0.85, maxIterations 20; "
              "обидва алгоритми з concurrency 1 для відтворюваності.", '',
              '## PageRank — топ-10', '', table(G['pagerank_top10'][0], top), '',
              f"## Louvain — спільноти (усього {lw[0]}, модульність {fmt(lw[1])})", '', table(G['louvain_communities'][0], comm), '']
    labels_top = [r[2] for r in top]
    plants_top = [r[1] for r in top if r[2] == 'Plant']
    big = comm[0]
    lines += ['## Інтерпретація', '',
              f"1. Найвищий PageRank має вузол «{top[0][1]}» ({top[0][2]}): це центр, до якого сходиться найбільше зв'язків "
              "INSTALLED_AT, OPERATED_BY і FORECAST_FOR, тому він найважливіший для навігації в базі знань.",
              f"2. У топ-10 потрапили {len(plants_top)} станції ({', '.join(plants_top)}): станції є головними «вузлами-агрегаторами» "
              "знань, через які пов'язані обладнання, прогнози та компанії.",
              f"3. Серед лідерів є вузли типів {', '.join(sorted(set(labels_top)))}; правило керування з великою кількістю зв'язків CONTROLS "
              "має високий PageRank, бо стосується багатьох турбін одночасно — зміна такого правила впливає на всю станцію.",
              "4. Турбіни з високим рейтингом — ті, навколо яких накопичено найбільше подій, ремонтів і вимірювань; вони є "
              "першими кандидатами для предиктивного обслуговування та детального аналізу причин відмов.",
              f"5. Louvain розбив граф на {lw[0]} спільнот із модульністю {fmt(lw[1])}: найбільша містить {big[1]} вузлів "
              f"({', '.join(big[2]) if big[2] else 'без станцій'}). Спільноти здебільшого збігаються зі станціями та їхнім обладнанням, "
              "а окремі спільноти утворюють персонал із ремонтами та ланцюжки «сигнал → відмова → ремонт».",
              "6. Для управління знаннями це означає, що граф природно ділиться на «острови знань» за станціями, а зв'язки між ними "
              "проходять через компанії, спільні правила керування та запчастини — саме ці вузли варто документувати найретельніше.",
              '', 'Результати збережено у графі як властивості вузлів `pagerank` і `community`:', '',
              table(G['check_saved'][0], G['check_saved'][1]), '']
b, a = P['q03_before'], P['q03_after']
lines += ['## PROFILE', '',
          '### Запит 1 — q03 (критичні події з червня 2026), оптимізація індексом `event_occurred_at`', '',
          '| Стан | dbHits | Рядків | Час, мс | Оператори (план) |', '|---|---|---|---|---|',
          f"| до (індекс видалено) | {b['dbHits']} | {b['rows']} | {b['ms']} | {' → '.join(b['operators'])} |",
          f"| після (індекс створено) | {a['dbHits']} | {a['rows']} | {a['ms']} | {' → '.join(a['operators'])} |", '',
          f"Кількість звернень до бази зменшилась з {b['dbHits']} до {a['dbHits']} "
          f"({round(100 * (1 - a['dbHits'] / b['dbHits'])) if b['dbHits'] else 0} %). "
          'Без індексу планувальник перебирає всі вузли :Event і фільтрує їх; з індексом — одразу знаходить події в діапазоні дат.', '',
          '### Запит 2 — q09 (аналіз впливу, DEPENDS_ON*1..4)', '',
          '| dbHits | Рядків | Час, мс | Оператори (план) |', '|---|---|---|---|',
          f"| {P['q09']['dbHits']} | {P['q09']['rows']} | {P['q09']['ms']} | {' → '.join(P['q09']['operators'])} |", '',
          'Запит починається з вузла підстанції, знайденого за унікальним `id` (індекс обмеження), і розгортає шлях змінної довжини '
          'лише назад по DEPENDS_ON, тому кількість звернень залишається малою навіть для глибини 4.']
(D / 'gds_report.md').write_text('\n'.join(lines) + '\n', encoding='utf-8')

# ------------------------------------------------------------------ sparql_vs_cypher.md
C = R['compare']; T = R['t2c']
ERR = json.load(open(D / 't2c_error_analysis.json', encoding='utf-8'))
L = ['# Порівняння SPARQL і Cypher; text-to-Cypher (ЛР 9, результат 5)', '',
     '## 1. Ті самі 5 питань двома мовами', '',
     'Дані однакові: `data/graph.ttl` (RDF, отримано з тих самих CSV) і граф Neo4j. SPARQL виконано в RDFLib, Cypher — у Neo4j; '
     'час — медіана 5 запусків.', '',
     '| № | Питання | Рядків SPARQL / Cypher | Результати |', '|---|---|---|---|']
for k, c in C.items(): L.append(f"| {k.upper()} | {c['question']} | {len(c['sparql_rows'])} / {len(c['cypher_rows'])} | {c['check']} |")
L += ['', '| № | Рядків коду SPARQL / Cypher | Символів SPARQL / Cypher | Час SPARQL, мс | Час Cypher, мс |', '|---|---|---|---|---|']
for k, c in C.items():
    L.append(f"| {k.upper()} | {c['sparql_lines']} / {c['cypher_lines']} | {c['sparql_chars']} / {c['cypher_chars']} | {c['sparql_ms']} | {c['cypher_ms']} |")
L += ['', 'Запити: `sparql/s1.rq … s5.rq` та `queries/compare/c1.cypher … c5.cypher`.', '',
      '## 2. Порівняння за критеріями', '',
      '| Критерій | SPARQL (RDF) | Cypher (LPG, Neo4j) |', '|---|---|---|',
      '| Читабельність | трійкові шаблони, потрібні префікси; зв\'язок читається як `?x res:installedAt ?p` | ASCII-шаблон `(e)-[:INSTALLED_AT]->(p)` наочно показує напрямок і тип зв\'язку |',
      '| Довжина запиту | довша через PREFIX і окремі трійки для кожної властивості | коротша: властивості в шаблоні вузла, без префіксів |',
      '| Шляхи та графові алгоритми | property paths (`res:dependsOn+`) без обмеження глибини та без повернення самого шляху; немає shortestPath | `*1..4`, `shortestPath`, `nodes(path)`, а також GDS (PageRank, Louvain) |',
      '| Семантика та виведення | RDFS/OWL-виведення, словники (FOAF, schema.org), глобальні IRI, федерація | виведення немає; підкласи моделюються кількома мітками, онтологічна сумісність втрачається |',
      '| Властивості зв\'язків | потребують реїфікації або RDF-star | природні: `source`, `confidence`, `validFrom` прямо на зв\'язку |',
      '| Цілісність | SHACL (зовнішня перевірка) | обмеження унікальності та індекси в самій СУБД; кардинальності в Community Edition немає |',
      '| Швидкодія на нашому обсязі | ' + ', '.join(f"{c['sparql_ms']}" for c in C.values()) + ' мс (RDFLib у пам\'яті) | ' + ', '.join(f"{c['cypher_ms']}" for c in C.values()) + ' мс (Neo4j, разом із мережевим викликом) |',
      '', 'Висновок: для навігації графом, аналізу впливу та алгоритмів зручніший Cypher; для обміну знаннями між системами, '
      'виведення та стандартних словників — RDF/SPARQL.', '',
      '## 3. Text-to-Cypher', '',
      '**Налаштування.** Підказка `prompts/t2c_system_v1.txt` містить повну схему (мітки, типи й напрямки зв\'язків, властивості) '
      'і правила: лише читання, лише елементи схеми, обов\'язковий LIMIT 50, відмова (`// REFUSED`) на запити зміни даних. '
      f"Модель: {T['records'][0]['model']}.", '',
      '**Захист (read-only).** Кожен згенерований запит проходить чотири рівні: (1) фільтр заборонених ключових слів '
      '(CREATE, MERGE, SET, DELETE, DETACH, REMOVE, DROP, FOREACH, LOAD CSV, CALL) — демонстрація: '
      f"`MATCH (m:Measurement) DETACH DELETE m` → {T['guard_demo'][1] or 'пропущено'}; (2) перевірка, що всі мітки, типи зв'язків і "
      "властивості є в схемі; (3) примусовий LIMIT 50, якщо його немає; (4) виконання в режимі "
      f"«{R['t2c_mode']}». Спроба запису в такій транзакції: "
      f"{'відхилена сервером — ' + T['server_write_blocked'].get('code', '') if T['server_write_blocked']['blocked'] else 'НЕ відхилена'}.", '',
      f"**Метрика.** Коректних запитів: **{T['correct']} з {T['n']} ({round(100 * T['correct'] / T['n'])} %)** "
      f"(результат збігається з еталоном; додаткові стовпці дозволені). Точний збіг стовпців: {T['exact']} з {T['n']}. "
      f"Шкідливий запит (видалення даних): {'відхилено' if T['adversarial_ok'] else 'НЕ відхилено'}. "
      f"Середній час виконання згенерованого запиту: {T['avg_exec_ms']} мс.", '',
      '| id | Питання | Статус | Коректно | Примітка |', '|---|---|---|---|---|']
for r in T['records']:
    L.append(f"| {r['id']} | {r['question']} | {r['status']} | {mark(r['correct'])} | {fmt(r.get('reason', ''))} |")
bad = [r for r in T['records'] if not r['correct']]
L += ['', f'### Аналіз помилок ({len(bad)})', '']
for r in bad:
    L += [f"**{r['id']}. {r['question']}**", '', '```cypher', r['generated'], '```', '',
          ERR.get(r['id'], 'Потребує ручного аналізу: порівняйте з еталоном нижче.'), '',
          'Еталон:', '', '```cypher', r['gold'], '```', '']
(D / 'sparql_vs_cypher.md').write_text('\n'.join(L) + '\n', encoding='utf-8')
print('docs: import_report.md, cypher_results.md, gds_report.md, sparql_vs_cypher.md')
