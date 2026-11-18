# -*- coding: utf-8 -*-
"""Незалежна перевірка результатів запитів Cypher (ЛР 9, результат 3, крок 4).

Відповіді обчислюються прямо з CSV звичайним Python, без Neo4j і без Cypher.
run_all.py порівнює з ними фактичні результати Neo4j.
Вихід: tests/expected.json
"""
import csv, json, pathlib, datetime as dt
from collections import defaultdict, Counter, deque
ROOT = pathlib.Path(__file__).resolve().parent.parent
D = ROOT / 'data'

N = {}                       # id -> властивості (+ '_label')
for f in D.glob('nodes_*.csv'):
    for r in csv.DictReader(open(f, encoding='utf-8')):
        r['_label'] = f.stem.split('_', 1)[1]; N[r['id']] = r
E = []                       # (from, type, to)
for f in D.glob('rels_*.csv'):
    t = f.stem.split('_', 1)[1].upper()
    for r in csv.DictReader(open(f, encoding='utf-8')): E.append((r['from'], t, r['to']))
out_ = defaultdict(list); in_ = defaultdict(list)
for a, t, b in E: out_[a].append((t, b)); in_[b].append((t, a))
fl = lambda x: float(x) if x not in ('', None) else None
def kind(i): return N[i].get('kind', '')
def is_sensor(i): return kind(i) in ('Anemometer', 'Pyranometer', 'TemperatureSensor')

R = {}
# q01
agg = defaultdict(lambda: [0, 0.0])
for a, t, b in E:
    if t == 'INSTALLED_AT' and b == 'wf-karpatska' and N[a]['_label'] == 'equipment':
        agg[kind(a)][0] += 1; agg[kind(a)][1] += fl(N[a].get('ratedPowerKW')) or 0.0
R['q01'] = sorted([[k, v[0], v[1]] for k, v in agg.items()], key=lambda r: (-r[2], r[0]))
# q02
rows = []
turb = [a for a, t, b in E if t == 'INSTALLED_AT' and b == 'wf-karpatska' and kind(a) == 'WindTurbine']
for tid in turb:
    sens = [a for t, a in in_[tid] if t == 'OBSERVES' and is_sensor(a)] or [None]
    for s in sens:
        ms = [a for t, a in in_[s] if t == 'MEASURED_BY'] if s else []
        last = max(ms, key=lambda m: N[m]['observedAt']) if ms else None
        rows.append([tid, s, fl(N[last]['value']) if last else None, N[last]['unit'] if last else None])
rows.sort(key=lambda r: (-(r[2] if r[2] is not None else -1e9), r[0]))
R['q02'] = rows[:5]
# q03
rows = []
for a, t, b in E:
    if t == 'AFFECTS':
        ev = N[a]
        if ev['occurredAt'] >= '2026-06-01T00:00:00' and int(ev['severity']) >= 4:
            plant = [p for tt, p in out_[b] if tt == 'INSTALLED_AT'][0]
            rows.append((ev['occurredAt'], [a, ev['kind'], int(ev['severity']), b, N[plant]['name']]))
R['q03'] = [r for _, r in sorted(rows, key=lambda x: x[0], reverse=True)]
# q04
agg = defaultdict(lambda: [0, 0.0])
for a, t, b in E:
    if t == 'PERFORMED_BY' and kind(a) == 'CorrectiveRepair':
        agg[b][0] += 1; agg[b][1] += fl(N[a]['costEUR'])
rows = []
for emp, (c, s) in agg.items():
    co = [x for tt, x in out_[emp] if tt == 'EMPLOYED_BY'][0]
    rows.append([N[emp]['name'], N[co]['name'], c, s])
R['q04'] = sorted(rows, key=lambda r: -r[3])
# q05 (неорієнтований обхід INSTALLED_AT|HAS_PART до глибини 2)
adj = defaultdict(list)
for a, t, b in E:
    if t in ('INSTALLED_AT', 'HAS_PART'): adj[a].append(b); adj[b].append(a)
seen = set(); frontier = {'wf-karpatska'}
for _ in range(2):
    nxt = set()
    for u in frontier:
        for v in adj[u]:
            if v != 'wf-karpatska': nxt.add(v)
    seen |= nxt; frontier = nxt
R['q05'] = sorted([[k, c] for k, c in Counter(kind(x) for x in seen).items()], key=lambda r: (-r[1], r[0]))
# q06 (BFS по неорієнтованому графу)
und = defaultdict(list)
for a, t, b in E: und[a].append((b, t)); und[b].append((a, t))
prev = {'ev-0001': None}; q = deque(['ev-0001'])
while q:
    u = q.popleft()
    if u == 'sub-lviv': break
    for v, t in und[u]:
        if v not in prev: prev[v] = (u, t); q.append(v)
chain, rels_, x = [], [], 'sub-lviv'
while x: chain.append(x); p = prev[x]; (rels_.append(p[1]) if p else None); x = p[0] if p else None
R['q06'] = [[chain[::-1], rels_[::-1], len(rels_)]]
# q07
rows = []
for a, t, b in E:
    if t == 'INSTALLED_AT' and N[a]['_label'] == 'equipment':
        h = fl(N[a].get('stateOfHealth'))
        if h is not None and h < 80:
            planned = sum(1 for tt, w in in_[a] if tt == 'TARGETS' and kind(w) == 'PlannedMaintenance')
            rows.append([a, kind(a), h, N[b]['name'], 'немає ТО' if planned == 0 else 'ТО заплановано'])
R['q07'] = sorted(rows, key=lambda r: (r[2], r[0]))
# q08
agg = defaultdict(lambda: [0, 0.0])
for a, t, b in E:
    if t == 'USES_PART': agg[b][0] += 1; agg[b][1] += fl(N[b]['unitCostEUR'])
R['q08'] = sorted([[N[k]['name'], v[0], v[1]] for k, v in agg.items()], key=lambda r: (-r[1], r[0]))[:5]
# q09 (зворотний обхід DEPENDS_ON до глибини 4)
dep_in = defaultdict(list)
for a, t, b in E:
    if t == 'DEPENDS_ON': dep_in[b].append(a)
depth = {}; frontier = ['sub-ivano-frankivsk']
for d in range(1, 5):
    nxt = []
    for u in frontier:
        for v in dep_in[u]:
            if v not in depth: depth[v] = d; nxt.append(v)
    frontier = nxt
agg = defaultdict(lambda: [0, 0, 0.0])
for x, d in depth.items():
    pl = [p for tt, p in out_[x] if tt == 'INSTALLED_AT']
    if not pl: continue
    k = (N[pl[0]]['name'], kind(x)); agg[k][0] += 1; agg[k][1] = max(agg[k][1], d)
    if kind(x) in ('WindTurbine', 'PVArray'): agg[k][2] += fl(N[x]['ratedPowerKW'])
R['q09'] = sorted([[p, k, v[0], v[1], v[2]] for (p, k), v in agg.items()], key=lambda r: (r[0], r[3], r[1]))
# q10
agg = defaultdict(lambda: [set(), set()])
for f, t, a in E:
    if t != 'CAUSED_BY' or kind(f) != 'FailureEvent' or kind(a) != 'AlarmEvent': continue
    for tt, w in in_[f]:
        if tt != 'TRIGGERED_BY': continue
        for t3, sp in out_[w]:
            if t3 == 'USES_PART': agg[sp][0].add(a); agg[sp][1].add(f)
R['q10'] = sorted([[N[sp]['name'], len(v[0]), len(v[1]), 3] for sp, v in agg.items()], key=lambda r: (-r[1], r[0]))

json.dump(R, open(ROOT / 'tests' / 'expected.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
for k, v in R.items():
    print(f'== {k} ({len(v)} рядків)')
    for r in v[:12]: print('   ', r)
