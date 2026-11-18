# -*- coding: utf-8 -*-
"""Будує import/*.cypher з CSV-файлів data/ (LOAD CSV + MERGE, ідемпотентно)."""
import csv, pathlib
ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA, IMP = ROOT / 'data', ROOT / 'import'
IMP.mkdir(exist_ok=True)

FLOAT = {'ratedPowerKW', 'stateOfHealth', 'hubHeightM', 'capacityMWh', 'installedCapacityMW', 'value', 'costEUR',
         'unitCostEUR', 'durationH', 'forecastMWh', 'windSpeedMS', 'irradianceWm2'}
INT = {'severity', 'voltageKV'}
DATETIME = {'occurredAt', 'observedAt', 'startedAt'}
DATE = {'commissioningDate', 'date', 'forecastDate'}
LABEL = {'region': 'Region', 'company': 'Company', 'gridnode': 'GridNode', 'plant': 'Plant', 'equipment': 'Equipment',
         'component': 'Component', 'measurement': 'Measurement', 'employee': 'Employee', 'sparepart': 'SparePart',
         'event': 'Event', 'record': 'Record', 'maintenancework': 'MaintenanceWork', 'weatherdata': 'WeatherData',
         'forecast': 'Forecast', 'controlrule': 'ControlRule'}
# додаткові мітки за полем kind
KIND_LABELS = {
    'WindFarm': ['WindFarm'], 'SolarPlant': ['SolarPlant'],
    'WindTurbine': ['WindTurbine', 'GeneratingUnit'], 'PVArray': ['PVArray', 'GeneratingUnit'],
    'Inverter': ['Inverter'], 'BatteryStorage': ['BatteryStorage'], 'Transformer': ['Transformer'],
    'Substation': ['Substation'], 'Anemometer': ['Anemometer', 'Sensor'], 'Pyranometer': ['Pyranometer', 'Sensor'],
    'TemperatureSensor': ['TemperatureSensor', 'Sensor'],
    'Rotor': ['Rotor'], 'Gearbox': ['Gearbox'], 'Generator': ['Generator'],
    'AlarmEvent': ['AlarmEvent'], 'FailureEvent': ['FailureEvent'], 'CurtailmentEvent': ['CurtailmentEvent'],
    'CorrectiveRepair': ['CorrectiveRepair'], 'PlannedMaintenance': ['PlannedMaintenance'],
}

def conv(k):
    v = f'row.{k}'
    if k in FLOAT: return f'toFloat({v})'
    if k in INT: return f'toInteger({v})'
    if k in DATETIME: return f"CASE WHEN {v} = '' THEN null ELSE localdatetime({v}) END"
    if k in DATE: return f"CASE WHEN {v} = '' THEN null ELSE date({v}) END"
    return f"CASE WHEN {v} = '' THEN null ELSE {v} END"

def main():
    # ---------- 01: обмеження та індекси ----------
    (IMP / '01_schema.cypher').write_text('''// 01 — обмеження цілісності та індекси (ідемпотентно: IF NOT EXISTS)
    CREATE CONSTRAINT entity_id_unique IF NOT EXISTS FOR (n:Entity) REQUIRE n.id IS UNIQUE;
    CREATE CONSTRAINT employee_email_unique IF NOT EXISTS FOR (n:Employee) REQUIRE n.email IS UNIQUE;
    CREATE CONSTRAINT record_number_unique IF NOT EXISTS FOR (n:Record) REQUIRE n.number IS UNIQUE;
    CREATE INDEX event_occurred_at IF NOT EXISTS FOR (n:Event) ON (n.occurredAt);
    CREATE INDEX equipment_health IF NOT EXISTS FOR (n:Equipment) ON (n.stateOfHealth);
    CREATE INDEX measurement_observed_at IF NOT EXISTS FOR (n:Measurement) ON (n.observedAt);
    CREATE TEXT INDEX entity_name_text IF NOT EXISTS FOR (n:Entity) ON (n.name);
    ''', encoding='utf-8')

    # ---------- 02: вузли ----------
    out = ['// 02 — імпорт вузлів (LOAD CSV + MERGE за унікальним id; повторний запуск не створює дублікатів)',
           '// CSV-файли мають лежати в теці import/ бази Neo4j (див. README)']
    for f in sorted(DATA.glob('nodes_*.csv')):
        key = f.stem.split('_', 1)[1]; label = LABEL[key]
        cols = next(csv.reader(open(f, encoding='utf-8')))
        sets = [f'n.{c} = {conv(c)}' for c in cols if c != 'id']
        q = [f"LOAD CSV WITH HEADERS FROM 'file:///{f.name}' AS row",
             f"MERGE (n:Entity {{id: row.id}})",
             f"SET n:{label},", "    " + ",\n    ".join(sets)]
        if 'kind' in cols:
            kinds = sorted({r['kind'] for r in csv.DictReader(open(f, encoding='utf-8'))})
            for k in kinds:
                labs = ':'.join(KIND_LABELS[k])
                q.append(f"FOREACH (_ IN CASE WHEN row.kind = '{k}' THEN [1] ELSE [] END | SET n:{labs})")
        out.append('\n'.join(q) + ';')
    (IMP / '02_nodes.cypher').write_text('\n\n'.join(out) + '\n', encoding='utf-8')

    # ---------- 03: зв'язки ----------
    out = ['// 03 — імпорт зв\'язків з властивостями походження (source, confidence, validFrom)']
    for f in sorted(DATA.glob('rels_*.csv')):
        t = f.stem.split('_', 1)[1].upper()
        out.append(f"""LOAD CSV WITH HEADERS FROM 'file:///{f.name}' AS row
    MATCH (a:Entity {{id: row.from}})
    MATCH (b:Entity {{id: row.to}})
    MERGE (a)-[r:{t}]->(b)
    SET r.source = row.source, r.confidence = toFloat(row.confidence), r.validFrom = date(row.validFrom);""")
    (IMP / '03_relationships.cypher').write_text('\n\n'.join(out) + '\n', encoding='utf-8')

    # ---------- 04: перевірки ----------
    (IMP / '04_checks.cypher').write_text('''// 04 — перевірки після імпорту
    MATCH (n) RETURN count(n) AS nodes;
    MATCH ()-[r]->() RETURN count(r) AS relationships;
    MATCH (n) UNWIND labels(n) AS label RETURN label, count(*) AS cnt ORDER BY cnt DESC;
    MATCH ()-[r]->() RETURN type(r) AS type, count(*) AS cnt ORDER BY cnt DESC;
    SHOW CONSTRAINTS YIELD name, type, labelsOrTypes, properties;
    SHOW INDEXES YIELD name, type, labelsOrTypes, properties, state;
    ''', encoding='utf-8')

    # ---------- 05: демонстрація порушення обмеження ----------
    (IMP / '05_constraint_violation.cypher').write_text('''// 05 — навмисне порушення унікальності: має завершитися помилкою
    // Neo.ClientError.Schema.ConstraintValidationFailed
    CREATE (:Entity:Plant {id: 'wf-karpatska', name: 'Дублікат ВЕС «Карпатська»'});
    ''', encoding='utf-8')

    # ---------- 06: read-only користувач для text-to-Cypher (лише Enterprise / Neo4j Desktop) ----------
    (IMP / '06_readonly_user.cypher').write_text('''// 06 — read-only користувач для text-to-Cypher.
    // Виконувати в базі `system` (:use system). Працює в Neo4j Enterprise (Neo4j Desktop містить
    // Enterprise Edition для розробки). У Community Edition ролей немає — тоді t2c.py
    // використовує транзакції в режимі READ (сервер відхиляє будь-який запис).
    CREATE USER t2c IF NOT EXISTS SET PASSWORD 'readonly-t2c' CHANGE NOT REQUIRED;
    GRANT ROLE reader TO t2c;
    SHOW USERS;
    ''', encoding='utf-8')
    print('import/: ', ', '.join(sorted(p.name for p in IMP.glob('*.cypher'))))


if __name__ == '__main__':
    main()
