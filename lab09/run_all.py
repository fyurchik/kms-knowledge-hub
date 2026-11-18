# -*- coding: utf-8 -*-
"""ЛР 9 — запуск усіх результатів у Neo4j і формування docs/*.md з фактичними результатами.

Використання:
    export NEO4J_PASSWORD=...           # (Windows: set NEO4J_PASSWORD=...)
    python run_all.py                    # дані беруться через LOAD CSV з теки import бази Neo4j
    python run_all.py --no-load-csv      # якщо CSV не скопійовано в import/ бази: рядки передаються параметром
    python run_all.py --skip-gds         # якщо не встановлено плагін Graph Data Science
    python run_all.py --live             # text-to-Cypher через API (потрібні ANTHROPIC_API_KEY і T2C_MODEL)
Змінні: NEO4J_URI (neo4j://localhost:7687), NEO4J_USER (neo4j), NEO4J_PASSWORD, NEO4J_DATABASE (neo4j),
        T2C_USER / T2C_PASSWORD — read-only користувач (якщо створено скриптом import/06_readonly_user.cypher).
"""
import os, sys, json, csv, re, time, pathlib, statistics, datetime, subprocess
import neo4j
from neo4j import GraphDatabase
from neo4j.exceptions import Neo4jError
ROOT = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / 'scripts'))
import t2c
try: sys.stdout.reconfigure(encoding='utf-8')
except Exception: pass

ARGS = set(sys.argv[1:])
URI = os.getenv('NEO4J_URI', 'neo4j://localhost:7687')
USER = os.getenv('NEO4J_USER', 'neo4j'); PWD = os.getenv('NEO4J_PASSWORD', 'password')
DB = os.getenv('NEO4J_DATABASE', 'neo4j')
RES = {'started': datetime.datetime.now().isoformat(timespec='seconds'), 'uri': URI, 'database': DB}
DOCS = ROOT / 'docs'; DOCS.mkdir(exist_ok=True); (ROOT / 'results').mkdir(exist_ok=True)

def h(t): print('\n' + '=' * 78 + f'\n{t}\n' + '=' * 78)
def statements(path):
    lines = [l for l in pathlib.Path(path).read_text(encoding='utf-8').split('\n') if not l.strip().startswith('//')]
    return [s.strip() for s in '\n'.join(lines).split(';') if s.strip()]
def plain(v):
    if v is None: return None
    if isinstance(v, (int, float, str, bool)): return v
    if isinstance(v, (list, tuple)): return [plain(x) for x in v]
    if isinstance(v, dict): return {k: plain(x) for k, x in v.items()}
    return str(v)
def run(s, q, **p):
    r = s.run(q, **p); keys = list(r.keys()); rows = [[plain(x) for x in rec.values()] for rec in r]
    return keys, rows
def fmt(v):
    if v is None: return '—'
    if isinstance(v, float): return ('%.3f' % v).rstrip('0').rstrip('.')
    if isinstance(v, list): return ', '.join(fmt(x) for x in v)
    return str(v).replace('|', '\\|')
def md_table(keys, rows, limit=50):
    out = ['| ' + ' | '.join(keys) + ' |', '|' + '---|' * len(keys)]
    out += ['| ' + ' | '.join(fmt(x) for x in r) + ' |' for r in rows[:limit]]
    return '\n'.join(out)
def counts(s):
    n = run(s, 'MATCH (n) RETURN count(n)')[1][0][0]; r = run(s, 'MATCH ()-[r]->() RETURN count(r)')[1][0][0]
    return n, r
def nrm(v):
    if isinstance(v, bool) or v is None: return v
    if isinstance(v, (int, float)): return round(float(v), 2)
    if isinstance(v, list): return [nrm(x) for x in v]
    return str(v)
def same(a, b):
    A, B = [nrm(r) for r in a], [nrm(r) for r in b]
    if A == B: return 'збігається'
    if sorted(map(str, A)) == sorted(map(str, B)): return 'збігається (інший порядок рядків)'
    return 'ВІДРІЗНЯЄТЬСЯ'

driver = GraphDatabase.driver(URI, auth=(USER, PWD))
driver.verify_connectivity()
with driver.session(database=DB) as s:
    RES['neo4j_version'] = run(s, 'CALL dbms.components() YIELD name, versions, edition RETURN name, versions[0], edition')[1]
print('Підключено:', URI, RES['neo4j_version'])

# =====================================================================================
h('РЕЗУЛЬТАТ 2. Обмеження, індекси, імпорт, ідемпотентність, порушення обмеження')
def do_import(s):
    for f in ['02_nodes.cypher', '03_relationships.cypher']:
        for st in statements(ROOT / 'import' / f):
            if '--no-load-csv' in ARGS:
                fn = re.search(r"file:///([\w.]+)", st).group(1)
                rows = list(csv.DictReader(open(ROOT / 'data' / fn, encoding='utf-8')))
                st2 = re.sub(r"LOAD CSV WITH HEADERS FROM 'file:///[\w.]+' AS row", 'UNWIND $rows AS row', st)
                s.run(st2, rows=rows).consume()
            else:
                s.run(st).consume()
with driver.session(database=DB) as s:
    for st in statements(ROOT / 'import' / '01_schema.cypher'): s.run(st).consume()
    s.run('CALL db.awaitIndexes(300)').consume()
    RES['constraints'] = run(s, 'SHOW CONSTRAINTS YIELD name, type, labelsOrTypes, properties RETURN name, type, labelsOrTypes, properties ORDER BY name')
    RES['indexes'] = run(s, 'SHOW INDEXES YIELD name, type, labelsOrTypes, properties, state RETURN name, type, labelsOrTypes, properties, state ORDER BY name')
    before = counts(s)
    t0 = time.perf_counter(); do_import(s); t_first = time.perf_counter() - t0
    first = counts(s)
    t0 = time.perf_counter(); do_import(s); t_second = time.perf_counter() - t0
    second = counts(s)
    RES['import'] = {'before': before, 'after_first': first, 'after_second': second,
                     'seconds_first': round(t_first, 2), 'seconds_second': round(t_second, 2),
                     'idempotent': first == second}
    RES['labels'] = run(s, "MATCH (n) UNWIND labels(n) AS label RETURN label, count(*) AS cnt ORDER BY cnt DESC, label")
    RES['rel_types'] = run(s, 'MATCH ()-[r]->() RETURN type(r) AS type, count(*) AS cnt ORDER BY cnt DESC, type')
    try:
        s.run(statements(ROOT / 'import' / '05_constraint_violation.cypher')[0]).consume()
        RES['violation'] = {'raised': False}
    except Neo4jError as e:
        RES['violation'] = {'raised': True, 'code': e.code, 'message': e.message}
    RES['violation']['counts_after'] = counts(s)
print('Вузлів/зв\'язків після 1-го імпорту:', first, ', після 2-го:', second, '→ ідемпотентно:', first == second)
print('Порушення обмеження:', RES['violation'].get('code'), '|', (RES['violation'].get('message') or '')[:160])

# =====================================================================================
h('РЕЗУЛЬТАТ 3. Запити Cypher (порівняння з незалежним розрахунком tests/expected.json)')
EXP = json.load(open(ROOT / 'tests' / 'expected.json', encoding='utf-8'))
INTERP = json.load(open(ROOT / 'docs' / 'interpretations.json', encoding='utf-8'))
RES['queries'] = {}
with driver.session(database=DB) as s:
    for f in sorted((ROOT / 'queries').glob('q*.cypher')):
        text = f.read_text(encoding='utf-8'); key = f.stem[:3]
        header = [l[3:] for l in text.split('\n') if l.startswith('// ')]
        q = '\n'.join(l for l in text.split('\n') if not l.startswith('//')).strip().rstrip(';')
        t0 = time.perf_counter(); keys, rows = run(s, q); ms = round((time.perf_counter() - t0) * 1000, 1)
        verdict = same(rows, EXP.get(key, []))
        RES['queries'][key] = {'file': f.name, 'header': header, 'query': q, 'keys': keys, 'rows': rows, 'ms': ms, 'check': verdict}
        print(f'{f.name}: {len(rows)} рядків, {ms} мс, перевірка: {verdict}')

# =====================================================================================
h('РЕЗУЛЬТАТ 4. GDS (PageRank, Louvain) і PROFILE')
def profile(s, q):
    r = s.run('PROFILE ' + q); summ = r.consume(); p = summ.profile or {}
    def walk(n):
        yield n
        for c in n.get('children', []): yield from walk(c)
    ops = list(walk(p))
    return {'dbHits': sum(o.get('dbHits', 0) for o in ops), 'rows': p.get('rows'),
            'operators': [o.get('operatorType', '').split('@')[0] for o in ops],
            'ms': (summ.result_available_after or 0) + (summ.result_consumed_after or 0)}
with driver.session(database=DB) as s:
    RES['gds'] = {}
    if '--skip-gds' not in ARGS:
        try:
            RES['gds']['version'] = run(s, 'RETURN gds.version()')[1][0][0]
            st = statements(ROOT / 'queries' / 'gds.cypher')
            names = ['drop', 'project', 'pagerank_top10', 'louvain_communities', 'pagerank_write', 'louvain_write', 'check_saved']
            for name, q in zip(names, st):
                RES['gds'][name] = run(s, q)
            print('GDS', RES['gds']['version'], '| PageRank топ-1:', RES['gds']['pagerank_top10'][1][0],
                  '| спільнот:', RES['gds']['louvain_write'][1][0])
        except Neo4jError as e:
            RES['gds']['error'] = f'{e.code}: {e.message}'; print('GDS недоступний:', e.message[:200])
    # PROFILE: запит q03 до і після індексу; запит q09
    q03 = RES['queries']['q03']['query']; q09 = RES['queries']['q09']['query']
    s.run('DROP INDEX event_occurred_at IF EXISTS').consume()
    profile(s, q03); before = profile(s, q03)
    s.run('CREATE INDEX event_occurred_at IF NOT EXISTS FOR (n:Event) ON (n.occurredAt)').consume()
    s.run('CALL db.awaitIndexes(300)').consume()
    profile(s, q03); after = profile(s, q03)
    profile(s, q09); p09 = profile(s, q09)
    RES['profile'] = {'q03_before': before, 'q03_after': after, 'q09': p09}
    print('PROFILE q03: dbHits до', before['dbHits'], '→ після', after['dbHits'])

# =====================================================================================
h('РЕЗУЛЬТАТ 5a. SPARQL і Cypher на однакових даних')
subprocess.run([sys.executable, str(ROOT / 'scripts' / 'run_sparql.py')], check=True, capture_output=True)
SP = json.load(open(ROOT / 'tests' / 'sparql_results.json', encoding='utf-8'))
RES['compare'] = {}
with driver.session(database=DB) as s:
    for i in range(1, 6):
        text = (ROOT / 'queries' / 'compare' / f'c{i}.cypher').read_text(encoding='utf-8')
        q = '\n'.join(l for l in text.split('\n') if not l.startswith('//')).strip().rstrip(';')
        run(s, q); ts = []
        for _ in range(5):
            t0 = time.perf_counter(); keys, rows = run(s, q); ts.append((time.perf_counter() - t0) * 1000)
        body = [l for l in q.split('\n') if l.strip()]
        sp = SP[f's{i}']
        RES['compare'][f'p{i}'] = {'question': text.split('\n')[0][3:], 'cypher_rows': rows, 'sparql_rows': sp['rows'],
                                   'cypher_ms': round(statistics.median(ts), 2), 'sparql_ms': sp['ms'],
                                   'cypher_lines': len(body), 'cypher_chars': len(' '.join(body)),
                                   'sparql_lines': sp['lines'], 'sparql_chars': sp['chars'], 'check': same(rows, sp['rows'])}
        print(f'P{i}: Cypher {len(rows)} рядків / SPARQL {len(sp["rows"])} → {RES["compare"][f"p{i}"]["check"]}')

# =====================================================================================
h('РЕЗУЛЬТАТ 5b. Text-to-Cypher')
ro = None
if os.getenv('T2C_USER'):
    ro = GraphDatabase.driver(URI, auth=(os.getenv('T2C_USER'), os.getenv('T2C_PASSWORD', '')))
    ro.verify_connectivity()
RES['t2c_mode'] = 'окремий користувач з роллю reader' if ro else 'транзакції READ (default_access_mode=READ)'
recs = t2c.evaluate(driver, DB, live='--live' in ARGS, model=os.getenv('T2C_MODEL'), ro_driver=ro)
normal = [r for r in recs if not r['adversarial']]
RES['t2c'] = {'n': len(normal), 'correct': sum(r['correct'] for r in normal), 'exact': sum(bool(r.get('exact')) for r in normal),
              'adversarial_ok': all(r['correct'] for r in recs if r['adversarial']),
              'avg_exec_ms': round(statistics.mean([r['exec_ms'] for r in normal if 'exec_ms' in r] or [0]), 1),
              'records': recs}
# демонстрація захисту: (1) фільтр ключових слів, (2) сервер відхиляє запис у READ-транзакції
RES['t2c']['guard_demo'] = t2c.guard('MATCH (m:Measurement) DETACH DELETE m')
try:
    with (ro or driver).session(database=DB, default_access_mode=neo4j.READ_ACCESS) as s:
        s.execute_read(lambda tx: tx.run("CREATE (:T2CWriteTest {x: 1})").consume())
    RES['t2c']['server_write_blocked'] = {'blocked': False}
except Neo4jError as e:
    RES['t2c']['server_write_blocked'] = {'blocked': True, 'code': e.code, 'message': e.message[:300]}
with driver.session(database=DB) as s: s.run('MATCH (n:T2CWriteTest) DELETE n').consume()
print(f"Text-to-Cypher: коректно {RES['t2c']['correct']}/{RES['t2c']['n']}, точний збіг {RES['t2c']['exact']}/{RES['t2c']['n']}, "
      f"шкідливий запит відхилено: {RES['t2c']['adversarial_ok']}, запис на сервері заблоковано: {RES['t2c']['server_write_blocked']['blocked']}")

# =====================================================================================
h('Формування docs/*.md і results/all_results.json')
json.dump(RES, open(ROOT / 'results' / 'all_results.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1, default=str)
subprocess.run([sys.executable, str(ROOT / 'scripts' / 'write_docs.py')], check=True)
print('Готово. Надішліть файл results/all_results.json і скріншоти Neo4j Browser.')
driver.close()
