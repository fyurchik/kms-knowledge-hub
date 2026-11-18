# ЛР 9 — Графова база знань у Neo4j

Фенин Ю.М., ФеІ-42. Предметна область: управління відновлюваними ресурсами (варіант 21). Гілка репозиторію: `lab09`.

## Структура

| Тека / файл | Результат | Що всередині |
|---|---|---|
| `docs/graph_schema.png`, `docs/cq_mapping.md` | 1 | схема LPG (15 міток, 18 типів), 10 CQ → шаблони шляхів, походження, порівняння з онтологією |
| `data/*.csv` | 2 | 15 файлів вузлів, 18 файлів зв'язків (307 вузлів, 500 зв'язків); `graph.ttl` — ті самі дані в RDF |
| `import/*.cypher` | 2 | 01 обмеження та індекси, 02 вузли, 03 зв'язки, 04 перевірки, 05 порушення обмеження, 06 read-only користувач |
| `queries/q01…q10.cypher` | 3 | 10 запитів Cypher (q09, q10 — аналіз впливу) |
| `queries/gds.cypher` | 4 | PageRank, Louvain, запис результатів у вузли |
| `sparql/s1…s5.rq`, `queries/compare/c1…c5.cypher` | 5 | ті самі 5 питань у SPARQL і Cypher |
| `prompts/t2c_system_v1.txt`, `tests/t2c_*.jsonl`, `scripts/t2c.py` | 5 | text-to-Cypher |
| `llm_log/`, `claims/claims.csv` | протокол | журнал взаємодії з LLM, таблиця тверджень |
| `run_all.py` | 2–5 | виконує все в Neo4j і створює `docs/*.md` з фактичними результатами |

Дані згенеровано скриптом `scripts/generate_data.py` (seed = 42) на основі онтології ЛР 6–8. Основу становлять реальні сутності
з попередніх робіт (ВЕС «Карпатська», турбіна K-02, відмова ev-0001…), а розширення до ≥ 100 вузлів — **синтетичне**.

## Версії

Neo4j 5.x (перевірено для 5.20+), плагін Graph Data Science 2.x, Python 3.10+, `neo4j` ≥ 5.20, `rdflib` ≥ 7.0, `networkx` ≥ 3.0.

## Запуск з нуля

### Варіант А — Neo4j Desktop (рекомендовано, macOS / Windows)

1. Встановити Neo4j Desktop (neo4j.com/download), створити проєкт і локальну базу **Neo4j 5.x**, задати пароль.
2. Вибрати базу → вкладка **Plugins** → встановити **Graph Data Science Library**.
3. Запустити базу (**Start**).
4. Скопіювати всі файли `data/*.csv` у теку імпорту бази: біля бази **⋯ → Open folder → Import**.
5. У терміналі в теці проєкту:
   ```bash
   pip install -r requirements.txt
   export NEO4J_PASSWORD='ваш_пароль'        # Windows: set NEO4J_PASSWORD=ваш_пароль
   python run_all.py
   ```

### Варіант Б — Docker

```bash
docker run -d --name kms-neo4j -p 7474:7474 -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/kms-lab09-pass -e NEO4J_PLUGINS='["graph-data-science"]' \
  -v "$PWD/data":/import neo4j:5
export NEO4J_PASSWORD=kms-lab09-pass
python run_all.py
```

### Якщо не вдалося скопіювати CSV у теку import

`python run_all.py --no-load-csv` — ті самі Cypher-скрипти, але рядки передаються параметром (`UNWIND $rows AS row`) замість `LOAD CSV`.

### Без плагіна GDS

`python run_all.py --skip-gds` — пропускає PageRank/Louvain (результат 4 буде неповним).

### Read-only користувач для text-to-Cypher (лише Neo4j Desktop / Enterprise)

У Neo4j Browser: `:use system`, виконати `import/06_readonly_user.cypher`, потім:
```bash
export T2C_USER=t2c T2C_PASSWORD=readonly-t2c
python run_all.py
```
Без цього кроку запити виконуються в транзакціях режиму READ — сервер однаково відхиляє будь-який запис.

## Що створює run_all.py

| Файл | Зміст |
|---|---|
| `docs/import_report.md` | обмеження, індекси, кількості, ідемпотентність, повідомлення про порушення обмеження |
| `docs/cypher_results.md` | 10 запитів: CQ, текст, результат, інтерпретація, звірка з незалежним розрахунком, ручна перевірка 3 запитів |
| `docs/gds_report.md` | PageRank топ-10, спільноти Louvain, інтерпретація, PROFILE до/після оптимізації |
| `docs/sparql_vs_cypher.md` | 5 питань двома мовами, таблиця порівняння, text-to-Cypher: захист, метрика, аналіз помилок |
| `tests/t2c.jsonl` | кожен запит text-to-Cypher зі статусом і результатом перевірки |
| `results/all_results.json` | усі сирі результати |

## Перевірки без Neo4j

```bash
python scripts/expected.py      # незалежний розрахунок відповідей q01–q10 (tests/expected.json)
python scripts/run_sparql.py    # SPARQL-частина порівняння
python scripts/gds_preview.py   # PageRank/Louvain у networkx для звірки з GDS
```

## Ключі та дані

Ключі API не зберігаються в коді: для `--live` використовуються змінні `ANTHROPIC_API_KEY` і `T2C_MODEL`.
Персональні дані не використовуються: імена працівників і компанії — вигадані для навчального набору.
