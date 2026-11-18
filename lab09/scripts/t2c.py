# -*- coding: utf-8 -*-
"""Text-to-Cypher (ЛР 9, результат 5): перевірка безпеки, перевірка схеми, LIMIT, виконання в режимі
лише читання, порівняння з еталоном.

Джерело запитів LLM:
  * за замовчуванням — збережені відповіді tests/t2c_llm_raw.jsonl (згенеровані в чаті, див. llm_log/);
  * з прапорцем --live і змінною ANTHROPIC_API_KEY — нова генерація через API (модель у T2C_MODEL).
Ключ API ніде не зберігається: лише змінна середовища.
"""
import json, os, re, time, pathlib
from collections import Counter
ROOT = pathlib.Path(__file__).resolve().parent.parent

LABELS = {'Entity', 'Region', 'Company', 'GridNode', 'Plant', 'WindFarm', 'SolarPlant', 'Equipment', 'WindTurbine', 'PVArray',
          'GeneratingUnit', 'Inverter', 'Transformer', 'Substation', 'BatteryStorage', 'Sensor', 'Anemometer', 'Pyranometer',
          'TemperatureSensor', 'Component', 'Rotor', 'Gearbox', 'Generator', 'Measurement', 'Event', 'FailureEvent', 'AlarmEvent',
          'CurtailmentEvent', 'MaintenanceWork', 'CorrectiveRepair', 'PlannedMaintenance', 'Employee', 'SparePart', 'Record',
          'Forecast', 'WeatherData', 'ControlRule'}
REL_TYPES = {'LOCATED_IN', 'OPERATED_BY', 'INSTALLED_AT', 'HAS_PART', 'DEPENDS_ON', 'OBSERVES', 'MEASURED_BY', 'AFFECTS',
             'CAUSED_BY', 'DOCUMENTED_IN', 'TARGETS', 'PERFORMED_BY', 'TRIGGERED_BY', 'USES_PART', 'EMPLOYED_BY',
             'FORECAST_FOR', 'BASED_ON', 'CONTROLS'}
PROPS = {'id', 'name', 'kind', 'taxId', 'voltageKV', 'installedCapacityMW', 'commissioningDate', 'model', 'ratedPowerKW',
         'stateOfHealth', 'hubHeightM', 'capacityMWh', 'value', 'unit', 'observedAt', 'occurredAt', 'severity', 'durationH',
         'costEUR', 'startedAt', 'position', 'email', 'unitCostEUR', 'number', 'date', 'forecastDate', 'forecastMWh',
         'windSpeedMS', 'irradianceWm2', 'conditionText', 'source', 'confidence', 'validFrom', 'pagerank', 'community'}
FORBIDDEN = re.compile(r'\b(CREATE|MERGE|DELETE|DETACH|SET|REMOVE|DROP|FOREACH|LOAD\s+CSV|CALL)\b', re.I)
DEFAULT_LIMIT = 50

def guard(q):
    """Повертає (ok, причина). Блокує записувальні та службові конструкції."""
    body = '\n'.join(l for l in q.split('\n') if not l.strip().startswith('//'))
    m = FORBIDDEN.search(body)
    return (False, f'заборонене ключове слово: {m.group(1).upper()}') if m else (True, '')

def schema_check(q):
    """Перевіряє, що всі мітки, типи зв'язків і властивості є в схемі."""
    body = re.sub(r"'[^']*'", "''", q)                     # прибрати рядкові літерали
    errs = []
    for grp in re.findall(r'\(\s*\w*\s*((?::\s*\w+)+)', body):
        for l in re.findall(r':\s*(\w+)', grp):
            if l not in LABELS: errs.append(f'невідома мітка :{l}')
    for grp in re.findall(r'\[\s*\w*\s*:\s*([\w|:\s]+?)\s*[\*\]\{]', body):
        for t in re.split(r'[|:\s]+', grp):
            if t and t not in REL_TYPES: errs.append(f'невідомий тип зв\'язку :{t}')
    for p in re.findall(r'\b[a-z]\w*\.([A-Za-z]\w*)\b', body):
        if p not in PROPS: errs.append(f'невідома властивість .{p}')
    for p in re.findall(r'\{\s*(\w+)\s*:', body):
        if p not in PROPS: errs.append(f'невідома властивість {p}')
    return (not errs, sorted(set(errs)))

def ensure_limit(q):
    q = q.strip().rstrip(';')
    return q if re.search(r'\bLIMIT\s+\d+', q, re.I) else q + f'\nLIMIT {DEFAULT_LIMIT}'

def generate_live(question, model):
    import anthropic                                         # pip install anthropic
    system = (ROOT / 'prompts' / 't2c_system_v1.txt').read_text(encoding='utf-8')
    client = anthropic.Anthropic()                           # ключ з ANTHROPIC_API_KEY
    msg = client.messages.create(model=model, max_tokens=400, temperature=0, system=system,
                                 messages=[{'role': 'user', 'content': question}])
    return ''.join(b.text for b in msg.content if b.type == 'text').strip().strip('`')

# ---------- порівняння результатів ----------
def _norm(v, id2name):
    if v is None: return None
    if isinstance(v, bool): return v
    if isinstance(v, (int, float)): return round(float(v), 2)
    if isinstance(v, (list, tuple)): return tuple(_norm(x, id2name) for x in v)
    s = str(v)
    return id2name.get(s, s)                                 # id і name вважаються тим самим вузлом

def compare(gold_rows, gen_rows, id2name):
    """exact — однакові мультимножини рядків; lenient — кожен рядок еталона міститься в окремому рядку відповіді
    (додаткові стовпці дозволені), кількість рядків однакова."""
    g = [Counter(_norm(x, id2name) for x in r) for r in gold_rows]
    a = [Counter(_norm(x, id2name) for x in r) for r in gen_rows]
    exact = sorted(map(lambda c: sorted(c.items(), key=str), g), key=str) == sorted(map(lambda c: sorted(c.items(), key=str), a), key=str)
    lenient = False
    if len(g) == len(a):
        used = [False] * len(a); lenient = True
        for gr in g:
            for i, ar in enumerate(a):
                if not used[i] and not (gr - ar):
                    used[i] = True; break
            else:
                lenient = False; break
    return exact, lenient

def evaluate(driver, database, live=False, model=None, ro_driver=None):
    import neo4j
    qs = [json.loads(l) for l in open(ROOT / 'tests' / 't2c_questions.jsonl', encoding='utf-8')]
    raw = {r['id']: r for r in map(json.loads, open(ROOT / 'tests' / 't2c_llm_raw.jsonl', encoding='utf-8'))}
    with driver.session(database=database) as s:
        id2name = {r['id']: r['name'] for r in s.run('MATCH (n:Entity) WHERE n.name IS NOT NULL RETURN n.id AS id, n.name AS name')}
    rdrv = ro_driver or driver
    out = []
    for q in qs:
        t0 = time.perf_counter()
        gen = generate_live(q['question'], model) if live else raw[q['id']]['cypher']
        gen_ms = round((time.perf_counter() - t0) * 1000, 1)
        rec = {'id': q['id'], 'question': q['question'], 'generated': gen, 'gold': q['gold'],
               'model': model if live else raw[q['id']]['model'], 'adversarial': q.get('adversarial', False)}
        if gen.strip().startswith('// REFUSED'):
            rec.update(status='refused', correct=bool(q.get('adversarial')), reason='модель відмовилася виконувати запит на зміну даних')
            out.append(rec); continue
        ok, why = guard(gen)
        if not ok:
            rec.update(status='blocked', correct=bool(q.get('adversarial')), reason=why); out.append(rec); continue
        ok, errs = schema_check(gen)
        if not ok:
            rec.update(status='schema_error', correct=False, reason='; '.join(errs)); out.append(rec); continue
        final = ensure_limit(gen); rec['executed'] = final
        try:
            t1 = time.perf_counter()
            with rdrv.session(database=database, default_access_mode=neo4j.READ_ACCESS) as s:
                rows = s.execute_read(lambda tx: [list(r.values()) for r in tx.run(final)])
            rec['exec_ms'] = round((time.perf_counter() - t1) * 1000, 1)
            with driver.session(database=database, default_access_mode=neo4j.READ_ACCESS) as s:
                gold_rows = s.execute_read(lambda tx: [list(r.values()) for r in tx.run(q['gold'])])
        except Exception as e:
            rec.update(status='runtime_error', correct=False, reason=str(e)[:300]); out.append(rec); continue
        exact, lenient = compare(gold_rows, rows, id2name)
        rec.update(status='executed', rows=len(rows), gold_rows=len(gold_rows), exact=exact, correct=lenient,
                   sample=[[str(x) for x in r] for r in rows[:3]], gold_sample=[[str(x) for x in r] for r in gold_rows[:3]],
                   reason='' if lenient else ('порожній результат' if not rows else 'результат відрізняється від еталона'))
        out.append(rec)
    with open(ROOT / 'tests' / 't2c.jsonl', 'w', encoding='utf-8') as f:
        for r in out: f.write(json.dumps(r, ensure_ascii=False, default=str) + '\n')
    return out
