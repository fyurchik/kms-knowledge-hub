# -*- coding: utf-8 -*-
"""Ті самі дані у RDF (data/graph.ttl) — для порівняння SPARQL і Cypher на однакових даних."""
import csv, pathlib, sys
from rdflib import Graph, Namespace, Literal, RDF, RDFS, XSD
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from build_import import FLOAT, INT, DATETIME, DATE, LABEL, KIND_LABELS
ROOT = pathlib.Path(__file__).resolve().parent.parent
RES = Namespace('https://kms.lnu.edu.ua/fenyn/res#'); ID = Namespace('https://kms.lnu.edu.ua/fenyn/res/id/')
g = Graph(); g.bind('res', RES); g.bind('id', ID)
for f in sorted((ROOT / 'data').glob('nodes_*.csv')):
    L = LABEL[f.stem.split('_', 1)[1]]
    for r in csv.DictReader(open(f, encoding='utf-8')):
        s = ID[r['id']]; g.add((s, RDF.type, RES[L]))
        for extra in KIND_LABELS.get(r.get('kind', ''), []): g.add((s, RDF.type, RES[extra]))
        for k, v in r.items():
            if k == 'id' or v == '': continue
            if k == 'name': g.add((s, RDFS.label, Literal(v, lang='uk'))); continue
            dt = XSD.decimal if k in FLOAT else XSD.integer if k in INT else XSD.dateTime if k in DATETIME else XSD.date if k in DATE else None
            g.add((s, RES[k], Literal(v, datatype=dt) if dt else Literal(v)))
def camel(t): p = t.lower().split('_'); return p[0] + ''.join(x.title() for x in p[1:])
for f in sorted((ROOT / 'data').glob('rels_*.csv')):
    t = camel(f.stem.split('_', 1)[1].upper())
    for r in csv.DictReader(open(f, encoding='utf-8')): g.add((ID[r['from']], RES[t], ID[r['to']]))
g.serialize(ROOT / 'data' / 'graph.ttl', format='turtle')
print('RDF тріплетів:', len(g))
