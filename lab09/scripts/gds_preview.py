# -*- coding: utf-8 -*-
"""Попередній розрахунок PageRank і Louvain у networkx (для перевірки результатів GDS)."""
import csv, json, pathlib, networkx as nx
ROOT = pathlib.Path(__file__).resolve().parent.parent
G = nx.Graph(); name = {}; lab = {}
for f in (ROOT / 'data').glob('nodes_*.csv'):
    for r in csv.DictReader(open(f, encoding='utf-8')):
        G.add_node(r['id']); name[r['id']] = r.get('name') or r['id']; lab[r['id']] = f.stem.split('_', 1)[1]
for f in (ROOT / 'data').glob('rels_*.csv'):
    for r in csv.DictReader(open(f, encoding='utf-8')): G.add_edge(r['from'], r['to'])
pr = nx.pagerank(G, alpha=0.85, max_iter=100)
top = sorted(pr.items(), key=lambda x: -x[1])[:10]
comms = nx.community.louvain_communities(G, seed=42)
comms = sorted(comms, key=len, reverse=True)
res = {'top10': [[i, name[i], lab[i], round(s, 4)] for i, s in top],
       'communities': [{'size': len(c), 'plants': sorted(name[x] for x in c if lab[x] == 'plant'),
                        'labels': dict(sorted({l: sum(1 for x in c if lab[x] == l) for l in set(lab[x] for x in c)}.items(), key=lambda kv: -kv[1]))} for c in comms],
       'modularity': round(nx.community.modularity(G, comms), 3), 'n': G.number_of_nodes(), 'm': G.number_of_edges(),
       'components': nx.number_connected_components(G)}
json.dump(res, open(ROOT / 'tests' / 'gds_preview.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('вузлів', res['n'], 'ребер', res['m'], 'компонент', res['components'])
print('PageRank top-10:'); [print('  ', r) for r in res['top10']]
print('Louvain: спільнот', len(comms), 'модульність', res['modularity'])
for c in res['communities'][:10]: print('  ', c['size'], c['plants'], list(c['labels'].items())[:5])
