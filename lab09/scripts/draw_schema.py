# -*- coding: utf-8 -*-
"""Діаграма графової схеми (мітки, типи зв'язків, ключові властивості) -> docs/graph_schema.png"""
import subprocess, pathlib, csv, collections
ROOT = pathlib.Path(__file__).resolve().parent.parent
LBL = {  # мітка: (ключові властивості, додаткові мітки)
 'Region': ('id, name', ''), 'Company': ('id, name, taxId', ''), 'GridNode': ('id, name, voltageKV', ''),
 'Plant': ('id, name, installedCapacityMW,\\ncommissioningDate', ':WindFarm | :SolarPlant'),
 'Equipment': ('id, name, kind, model,\\nratedPowerKW, stateOfHealth', ':WindTurbine :PVArray :Inverter\\n:Transformer :Substation :Sensor …'),
 'Component': ('id, name, kind', ':Rotor :Gearbox :Generator'),
 'Measurement': ('id, value, unit, observedAt', ''), 'Event': ('id, name, kind, occurredAt,\\nseverity, durationH', ':FailureEvent :AlarmEvent\\n:CurtailmentEvent'),
 'MaintenanceWork': ('id, name, kind, costEUR, startedAt', ':CorrectiveRepair\\n:PlannedMaintenance'),
 'Employee': ('id, name, position, email', ''), 'SparePart': ('id, name, unitCostEUR', ''), 'Record': ('id, number, date', ''),
 'Forecast': ('id, forecastDate, forecastMWh', ''), 'WeatherData': ('id, windSpeedMS, irradianceWm2', ''),
 'ControlRule': ('id, name, conditionText', '')}
# типи зв'язків визначаємо з даних: (мітка джерела, тип, мітка цілі)
lab = {}
for f in (ROOT / 'data').glob('nodes_*.csv'):
    L = {'gridnode': 'GridNode', 'sparepart': 'SparePart', 'maintenancework': 'MaintenanceWork', 'weatherdata': 'WeatherData',
         'controlrule': 'ControlRule'}.get(f.stem.split('_', 1)[1], f.stem.split('_', 1)[1].title())
    for r in csv.DictReader(open(f, encoding='utf-8')): lab[r['id']] = L
pairs = collections.Counter()
for f in (ROOT / 'data').glob('rels_*.csv'):
    t = f.stem.split('_', 1)[1].upper()
    for r in csv.DictReader(open(f, encoding='utf-8')): pairs[(lab[r['from']], t, lab[r['to']])] += 1
L = ['digraph S {', 'graph [rankdir=LR, nodesep=0.35, ranksep=0.9, fontname="Liberation Sans", pad=0.2, splines=true];',
     'node [shape=plain, fontname="Liberation Sans"];', 'edge [fontname="Liberation Sans", fontsize=10, color="#555555", arrowsize=0.7];']
for l, (props, extra) in LBL.items():
    ex = f'<tr><td align="left"><font point-size="9" color="#555555">{extra.replace(chr(92)+"n","<br/>")}</font></td></tr>' if extra else ''
    L.append(f'{l} [label=<<table border="1" cellborder="0" cellspacing="0" cellpadding="4" bgcolor="#eef4fb" color="#1f4e79">'
             f'<tr><td bgcolor="#1f4e79"><font color="white"><b>:{l}</b></font></td></tr>'
             f'<tr><td align="left"><font point-size="9">{props.replace(chr(92)+"n","<br/>")}</font></td></tr>{ex}</table>>];')
for (a, t, b), n in sorted(pairs.items()):
    L.append(f'{a} -> {b} [label="{t}"];')
L.append('note [shape=note, fontsize=9, label="На всіх зв\'язках: source, confidence, validFrom\\nНа всіх вузлах: додаткова мітка :Entity (унікальний id)"];')
L.append('}')
(ROOT / 'docs' / 'graph_schema.dot').write_text('\n'.join(L), encoding='utf-8')
subprocess.run(['dot', '-Tpng', '-Gdpi=150', str(ROOT / 'docs' / 'graph_schema.dot'), '-o', str(ROOT / 'docs' / 'graph_schema.png')], check=True)
print('міток:', len(LBL), 'типів зв\'язків:', len({t for _, t, _ in pairs}), 'пар (мітка-тип-мітка):', len(pairs))
