# -*- coding: utf-8 -*-
"""Виконання SPARQL-частини порівняння (RDFLib, без Neo4j). Вихід: tests/sparql_results.json"""
import json, pathlib, time, rdflib
ROOT = pathlib.Path(__file__).resolve().parent.parent
g = rdflib.Graph().parse(ROOT / 'data' / 'graph.ttl')
def norm(v):
    if v is None: return None
    if isinstance(v, rdflib.Literal):
        x = v.toPython()
        if hasattr(x, 'is_integer') or type(x).__name__ in ('Decimal', 'float'): return float(x)
        if isinstance(x, int): return x
        return str(x)
    s = str(v); return s.split('/id/')[-1] if '/id/' in s else s
out = {}
for f in sorted((ROOT / 'sparql').glob('s*.rq')):
    q = f.read_text(encoding='utf-8')
    g.query(q)                                   # прогрів
    t = []
    for _ in range(5):
        t0 = time.perf_counter(); rows = list(g.query(q)); t.append((time.perf_counter() - t0) * 1000)
    res = [[norm(x) for x in r] for r in rows]
    body = [l for l in q.split('\n') if l.strip() and not l.startswith('#') and not l.startswith('PREFIX')]
    out[f.stem] = {'rows': res, 'ms': round(sorted(t)[2], 2), 'lines': len(body), 'chars': len(' '.join(body))}
    print(f'{f.stem}: {len(res)} рядків, медіана {out[f.stem]["ms"]} мс, {out[f.stem]["lines"]} рядків коду')
    for r in res[:8]: print('    ', r)
json.dump(out, open(ROOT / 'tests' / 'sparql_results.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
