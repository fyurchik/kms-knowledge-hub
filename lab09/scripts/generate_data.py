# -*- coding: utf-8 -*-
"""Генерація даних для графової бази знань (ЛР 9).

Основа — онтологія та індивіди ЛР 6–8 (простір res:, ВЕС «Карпатська», турбіни K-01…,
відмова ev-0001 тощо). Набір розширено до розміру, потрібного для ЛР 9
(≥ 100 вузлів, ≥ 200 зв'язків). Розширена частина — СИНТЕТИЧНА, генерується
детерміновано (seed = 42); у звіті це задекларовано.

Вихід: data/nodes_<label>.csv, data/rels_<TYPE>.csv, data/graph.ttl (RDF-версія
тих самих даних для порівняння зі SPARQL).
"""
import csv, random, pathlib, datetime as dt

SEED = 42
random.seed(SEED)
OUT = pathlib.Path(__file__).resolve().parent.parent / 'data'
OUT.mkdir(exist_ok=True)

nodes = {}   # label -> list[dict]
rels = {}    # TYPE  -> list[dict]
SRC_ONTO, SRC_SCADA, SRC_CMMS, SRC_HR = 'onto-lab06', 'scada', 'cmms', 'hr-register'

def node(label, **p):
    nodes.setdefault(label, []).append(p); return p['id']
def rel(t, a, b, source, confidence=1.0, valid_from='2026-01-01'):
    rels.setdefault(t, []).append({'from': a, 'to': b, 'source': source,
                                   'confidence': confidence, 'validFrom': valid_from})

# ---------------- регіони, компанії, мережа ----------------
REG = [('region-lviv', 'Львівська область'), ('region-ivano-frankivsk', 'Івано-Франківська область'),
       ('region-zakarpattia', 'Закарпатська область')]
for i, n in REG: node('Region', id=i, name=n)
CO = [('co-zakhid-vde', 'ТОВ «Захід ВДЕ»', '41234567'), ('co-halych-solar', 'ТОВ «Галич Солар»', '42345678'),
      ('co-karpaty-energy', 'ТОВ «Карпати Енерджі»', '43456789')]
for i, n, t in CO: node('Company', id=i, name=n, taxId=t)
node('GridNode', id='grid-west', name='Вузол енергосистеми «Захід»', voltageKV=330)

# ---------------- станції ----------------
PLANTS = [  # id, назва, тип, регіон, компанія, МВт, дата, кількість одиниць
 ('wf-karpatska', 'ВЕС «Карпатська»', 'WindFarm', 'region-lviv', 'co-zakhid-vde', 52.8, '2021-06-15', 8),
 ('wf-sambir', 'ВЕС «Самбірська»', 'WindFarm', 'region-lviv', 'co-zakhid-vde', 25.2, '2023-09-01', 6),
 ('wf-uzhok', 'ВЕС «Ужоцька»', 'WindFarm', 'region-zakarpattia', 'co-karpaty-energy', 25.2, '2024-04-10', 6),
 ('sp-halych', 'СЕС «Галич-1»', 'SolarPlant', 'region-ivano-frankivsk', 'co-halych-solar', 12.0, '2020-05-20', 4),
 ('sp-kolomyia', 'СЕС «Коломия»', 'SolarPlant', 'region-ivano-frankivsk', 'co-halych-solar', 9.6, '2022-07-01', 4),
 ('sp-mukachevo', 'СЕС «Мукачево»', 'SolarPlant', 'region-zakarpattia', 'co-karpaty-energy', 8.0, '2023-05-12', 4),
]
PREF = {'wf-karpatska': 'K', 'wf-sambir': 'S', 'wf-uzhok': 'U', 'sp-halych': 'H', 'sp-kolomyia': 'KL', 'sp-mukachevo': 'M'}
SUB = {'region-lviv': 'sub-lviv', 'region-ivano-frankivsk': 'sub-ivano-frankivsk', 'region-zakarpattia': 'sub-zakarpattia'}
for reg, sid in SUB.items():
    sname = {'sub-lviv': 'ПС «Львів-Західна»', 'sub-ivano-frankivsk': 'ПС «Івано-Франківськ»', 'sub-zakarpattia': 'ПС «Мукачево»'}[sid]
    node('Equipment', id=sid, name=sname, kind='Substation',
         model='ПС 110/35 кВ', ratedPowerKW=80000.0, stateOfHealth=float(random.randint(85, 99)))
    rel('DEPENDS_ON', sid, 'grid-west', SRC_ONTO)

equipment_by_plant = {}
turbines, pv_arrays, inverters, bess = [], [], [], []
for pid, name, kind, reg, co, mw, date, n in PLANTS:
    node('Plant', id=pid, name=name, kind=kind, installedCapacityMW=mw, commissioningDate=date)
    rel('LOCATED_IN', pid, reg, SRC_ONTO); rel('OPERATED_BY', pid, co, SRC_ONTO)
    tr = f'tr-{pid.split("-",1)[1]}'
    node('Equipment', id=tr, name=f'Трансформатор {name}', kind='Transformer', model='ТДН-63000/110',
         ratedPowerKW=63000.0, stateOfHealth=float(random.randint(82, 99)))
    rel('INSTALLED_AT', tr, pid, SRC_ONTO); rel('DEPENDS_ON', tr, SUB[reg], SRC_ONTO)
    equipment_by_plant[pid] = [tr]
    pref = PREF[pid]
    if kind == 'WindFarm':
        model, kw = ('Siemens Gamesa SG 6.6-170', 6600.0) if pid == 'wf-karpatska' else ('Vestas V136-4.2', 4200.0)
        for k in range(1, n + 1):
            tid = f'wt-{pref.lower()}{k:02d}'
            soh = 74.0 if tid == 'wt-k02' else float(random.choice([random.randint(70, 79)] + [random.randint(80, 99)] * 6))
            node('Equipment', id=tid, name=f'ВЕУ {pref}-{k:02d}', kind='WindTurbine', model=model,
                 ratedPowerKW=kw, stateOfHealth=soh, hubHeightM=115.0 if kw > 5000 else 112.0)
            rel('INSTALLED_AT', tid, pid, SRC_ONTO); rel('DEPENDS_ON', tid, tr, SRC_ONTO)
            for cname, ckind in [('rotor', 'Ротор'), ('gearbox', 'Редуктор'), ('generator', 'Генератор')]:
                cid = f'{cname}-{pref.lower()}{k:02d}'
                node('Component', id=cid, name=f'{ckind} {pref}-{k:02d}', kind=cname.title())
                rel('HAS_PART', tid, cid, SRC_ONTO)
            turbines.append((tid, pid)); equipment_by_plant[pid].append(tid)
        sid = f'anm-{pref.lower()}01'
        node('Equipment', id=sid, name=f'Анемометр ANM-{pref}01', kind='Anemometer', model='Thies First Class')
        rel('INSTALLED_AT', sid, pid, SRC_ONTO); rel('OBSERVES', sid, f'wt-{pref.lower()}01', SRC_SCADA)
    else:
        for k in range(1, n + 1):
            inv = f'inv-{pref.lower()}{k:02d}'; pv = f'pv-{pref.lower()}{k:02d}'
            node('Equipment', id=inv, name=f'Інвертор {pref}-{k:02d}', kind='Inverter', model='Huawei SUN2000-330KTL',
                 ratedPowerKW=300.0, stateOfHealth=62.0 if inv == 'inv-h02' else float(random.randint(78, 99)))
            node('Equipment', id=pv, name=f'ФЕМ {pref}-{k:02d}', kind='PVArray', model='LONGi Hi-MO 5',
                 ratedPowerKW=round(mw * 1000 / n, 1), stateOfHealth=float(random.randint(85, 98)))
            for e in (inv, pv): rel('INSTALLED_AT', e, pid, SRC_ONTO)
            rel('DEPENDS_ON', pv, inv, SRC_ONTO); rel('DEPENDS_ON', inv, tr, SRC_ONTO)
            inverters.append((inv, pid)); pv_arrays.append((pv, pid)); equipment_by_plant[pid] += [inv, pv]
        sid = f'pyr-{pref.lower()}01'
        node('Equipment', id=sid, name=f'Піранометр PYR-{pref}01', kind='Pyranometer', model='Kipp & Zonen SMP10')
        rel('INSTALLED_AT', sid, pid, SRC_ONTO); rel('OBSERVES', sid, f'pv-{pref.lower()}01', SRC_SCADA)

for pid, kw, cap in [('wf-karpatska', 2500.0, 5.0), ('sp-kolomyia', 1000.0, 2.0)]:
    bid = f'bess-{PREF[pid].lower()}01'
    node('Equipment', id=bid, name=f'Накопичувач {bid.upper()}', kind='BatteryStorage', model='Tesla Megapack 2',
         ratedPowerKW=kw, capacityMWh=cap, stateOfHealth=float(random.randint(88, 97)))
    rel('INSTALLED_AT', bid, pid, SRC_ONTO); rel('DEPENDS_ON', bid, f'tr-{pid.split("-",1)[1]}', SRC_ONTO)
    bess.append((bid, pid))

# ---------------- датчики температури та вимірювання ----------------
temp_sensors = []
for tid, pid in turbines:
    s = 'tmp-' + tid.split('-')[1]
    node('Equipment', id=s, name=f'Термодатчик TMP-{tid.split("-")[1].upper()}', kind='TemperatureSensor', model='PT100')
    rel('INSTALLED_AT', s, pid, SRC_ONTO); rel('OBSERVES', s, tid, SRC_SCADA); temp_sensors.append((s, tid))
start = dt.datetime(2026, 11, 9, 6, 0)
mcount = 0
def measurement(sensor, value, unit, ts):
    global mcount
    mcount += 1; mid = f'm-{mcount:04d}'
    node('Measurement', id=mid, value=value, unit=unit, observedAt=ts.isoformat())
    rel('MEASURED_BY', mid, sensor, SRC_SCADA, valid_from=ts.date().isoformat())
for s, tid in temp_sensors:
    for h in (0, 6):
        v = 88.5 if (tid == 'wt-k02' and h == 6) else round(random.uniform(48, 79), 1)
        measurement(s, v, '°C', start + dt.timedelta(hours=h))
for pid, name, kind, *_ in PLANTS:
    pref = PREF[pid].lower()
    s = f'anm-{pref}01' if kind == 'WindFarm' else f'pyr-{pref}01'
    for h in (0, 6):
        v = round(random.uniform(6, 27), 1) if kind == 'WindFarm' else float(random.randint(150, 650))
        measurement(s, v, 'м/с' if kind == 'WindFarm' else 'Вт/м²', start + dt.timedelta(hours=h))

# ---------------- персонал, запчастини ----------------
EMP = [('emp-kovalchuk', 'Олег Ковальчук', 'інженер з ТО', 'co-zakhid-vde'),
       ('emp-melnyk', 'Ірина Мельник', 'оператор диспетчерського пункту', 'co-zakhid-vde'),
       ('emp-hnatiuk', 'Василь Гнатюк', 'технік ВЕУ', 'co-zakhid-vde'),
       ('emp-savchuk', 'Марія Савчук', 'інженер-аналітик', 'co-zakhid-vde'),
       ('emp-boiko', 'Андрій Бойко', 'технік СЕС', 'co-halych-solar'),
       ('emp-tkach', 'Наталія Ткач', 'інженер СЕС', 'co-halych-solar'),
       ('emp-kravets', 'Петро Кравець', 'електромонтер', 'co-halych-solar'),
       ('emp-popovych', 'Іван Попович', 'технік ВЕУ', 'co-karpaty-energy'),
       ('emp-fedak', 'Олена Федак', 'інженер з ТО', 'co-karpaty-energy'),
       ('emp-lukach', 'Михайло Лукач', 'електромонтер', 'co-karpaty-energy'),
       ('emp-bilyk', 'Софія Білик', 'диспетчер', 'co-karpaty-energy'),
       ('emp-danyliuk', 'Роман Данилюк', 'начальник служби ТО', 'co-zakhid-vde')]
for i, n, pos, co in EMP:
    node('Employee', id=i, name=n, position=pos, email=f'{i.split("-")[1]}@{co.split("-",1)[1]}.ua')
    rel('EMPLOYED_BY', i, co, SRC_HR)
PARTS = [('part-oil', 'Мастило редукторне 20 л', 180.0), ('part-bearing', 'Підшипник вихідного вала', 2400.0),
         ('part-filter', 'Фільтр мастила', 95.0), ('part-fan', 'Вентилятор охолодження', 650.0),
         ('part-brush', 'Щітки генератора', 120.0), ('part-igbt', 'IGBT-модуль інвертора', 1450.0),
         ('part-fuse', 'Запобіжник DC 1500 В', 60.0), ('part-cable', 'Кабель DC 6 мм², 50 м', 210.0),
         ('part-pitch', 'Привід кута атаки', 3100.0), ('part-sensor', 'Датчик температури PT100', 75.0)]
for i, n, c in PARTS: node('SparePart', id=i, name=n, unitCostEUR=c)
EMP_BY_CO = {}
for i, _, _, co in EMP: EMP_BY_CO.setdefault(co, []).append(i)
CO_OF_PLANT = {p[0]: p[4] for p in PLANTS}
PLANT_OF = {}
for pid, eqs in equipment_by_plant.items():
    for e in eqs: PLANT_OF[e] = pid
for b, p in bess: PLANT_OF[b] = p

# ---------------- події, ремонти, акти ----------------
ev, mw, rec = 0, 0, 0
def event(kind, label, target, ts, sev, dur, src=SRC_SCADA):
    global ev
    ev += 1; eid = f'ev-{ev:04d}'
    node('Event', id=eid, name=label, kind=kind, occurredAt=ts.isoformat(), severity=sev, durationH=dur)
    rel('AFFECTS', eid, target, src, valid_from=ts.date().isoformat()); return eid
def record(eid, ts):
    global rec
    rec += 1; rid = f'rec-{rec:04d}'
    node('Record', id=rid, number=f'АПС-2026-{846 + rec:04d}', name=f'Акт АПС-2026-{846 + rec:04d}', date=ts.date().isoformat())
    rel('DOCUMENTED_IN', eid, rid, SRC_CMMS, valid_from=ts.date().isoformat()); return rid
def work(kind, label, target, who, cost, ts, trig=None, parts=()):
    global mw
    mw += 1; wid = f'mw-{mw:04d}'
    node('MaintenanceWork', id=wid, name=label, kind=kind, costEUR=cost, startedAt=ts.isoformat())
    rel('TARGETS', wid, target, SRC_CMMS, valid_from=ts.date().isoformat())
    rel('PERFORMED_BY', wid, who, SRC_CMMS, valid_from=ts.date().isoformat())
    if trig: rel('TRIGGERED_BY', wid, trig, SRC_CMMS, valid_from=ts.date().isoformat())
    for p in parts: rel('USES_PART', wid, p, SRC_CMMS, valid_from=ts.date().isoformat())
    return wid

# ключовий сценарій з ЛР 6–8: перегрів редуктора K-02
t0 = dt.datetime(2026, 11, 9, 11, 30)
f1 = event('FailureEvent', 'Перегрів редуктора K-02', 'wt-k02', t0 + dt.timedelta(minutes=2), 4, 14.0)
a1 = event('AlarmEvent', 'Перевищення температури редуктора K-02', 'wt-k02', t0, 3, 0.5)
rel('CAUSED_BY', f1, a1, SRC_SCADA, confidence=0.9, valid_from='2026-11-09')
record(f1, t0)
work('CorrectiveRepair', 'Ремонт редуктора K-02', 'wt-k02', 'emp-kovalchuk', 8400.0, t0 + dt.timedelta(hours=3),
     trig=f1, parts=('part-oil', 'part-bearing', 'part-filter'))
f2 = event('FailureEvent', 'Відмова інвертора H-02', 'inv-h02', dt.datetime(2026, 11, 7, 10, 15), 3, 6.0)
record(f2, dt.datetime(2026, 11, 7, 10, 15))
work('CorrectiveRepair', 'Заміна модуля інвертора H-02', 'inv-h02', 'emp-boiko', 3650.0,
     dt.datetime(2026, 11, 7, 13, 0), trig=f2, parts=('part-igbt', 'part-fuse'))

FAIL_TPL = [('Перегрів генератора', ('part-brush', 'part-fan'), 'WindTurbine'),
            ('Знос підшипника редуктора', ('part-bearing', 'part-oil'), 'WindTurbine'),
            ('Несправність приводу кута атаки', ('part-pitch',), 'WindTurbine'),
            ('Відмова датчика температури', ('part-sensor',), 'WindTurbine'),
            ('Відмова IGBT-модуля', ('part-igbt',), 'Inverter'),
            ('Перегорання запобіжника DC', ('part-fuse', 'part-cable'), 'Inverter')]
pool_wt = [t for t, _ in turbines if t != 'wt-k02']
pool_inv = [i for i, _ in inverters if i != 'inv-h02']
for k in range(10):           # 10 ланцюжків «сигнал → відмова → ремонт»
    title, parts, tgt_kind = FAIL_TPL[k % len(FAIL_TPL)]
    target = random.choice(pool_wt if tgt_kind == 'WindTurbine' else pool_inv)
    ts = dt.datetime(2026, random.randint(1, 10), random.randint(1, 28), random.randint(6, 18), 0)
    alarm = event('AlarmEvent', f'Попередження: {title.lower()} ({target})', target, ts, random.randint(2, 3), round(random.uniform(0.2, 1.0), 1))
    fail = event('FailureEvent', f'{title} ({target})', target, ts + dt.timedelta(minutes=random.randint(5, 90)),
                 random.randint(3, 5), round(random.uniform(2, 36), 1))
    rel('CAUSED_BY', fail, alarm, SRC_SCADA, confidence=round(random.uniform(0.6, 0.95), 2), valid_from=ts.date().isoformat())
    if k % 2 == 0: record(fail, ts)
    who = random.choice(EMP_BY_CO[CO_OF_PLANT[PLANT_OF[target]]])
    cost = round(sum(dict((p[0], p[2]) for p in PARTS)[p] for p in parts) + random.randint(4, 30) * 50, 0)
    work('CorrectiveRepair', f'Усунення: {title.lower()} ({target})', target, who, cost,
         ts + dt.timedelta(hours=random.randint(2, 30)), trig=fail, parts=parts)
for k in range(5):            # обмеження генерації
    tgt = random.choice([t for t, _ in turbines])
    event('CurtailmentEvent', f'Обмеження генерації ({tgt})', tgt,
          dt.datetime(2026, random.randint(3, 10), random.randint(1, 28), 13, 0), 2, float(random.randint(1, 5)))
for k in range(16):           # планове ТО
    tgt = random.choice([t for t, _ in turbines] + [p for p, _ in pv_arrays] + [i for i, _ in inverters])
    who = random.choice(EMP_BY_CO[CO_OF_PLANT[PLANT_OF[tgt]]])
    parts = random.choice([(), ('part-oil', 'part-filter'), ('part-filter',), ('part-cable',)])
    work('PlannedMaintenance', f'Планове ТО ({tgt})', tgt, who, float(random.randint(4, 30) * 50),
         dt.datetime(2026, random.randint(1, 12), random.randint(1, 28), 9, 0), parts=parts)

# ---------------- прогнози, метеодані, правила ----------------
for pid, name, kind, *_ in PLANTS:
    wd = f'wd-{pid}-20261111'; fc = f'fc-{pid}-20261111'
    node('WeatherData', id=wd, name=f'Метеопрогноз {name} 11.11.2026',
         windSpeedMS=round(random.uniform(5, 12), 1) if kind == 'WindFarm' else None,
         irradianceWm2=None if kind == 'WindFarm' else float(random.randint(120, 350)))
    node('Forecast', id=fc, name=f'Прогноз {name} 11.11.2026', forecastDate='2026-11-11',
         forecastMWh=round(random.uniform(0.25, 0.45) * 24 * dict((p[0], p[5]) for p in PLANTS)[pid], 1))
    rel('FORECAST_FOR', fc, pid, 'forecast-model'); rel('BASED_ON', fc, wd, 'forecast-model', confidence=0.85)
RULES = [('rule-storm-stop', 'Зупинка при штормовому вітрі', 'швидкість вітру > 25 м/с протягом 10 с', [t for t, _ in turbines]),
         ('rule-overheat', 'Зниження потужності при перегріві', 'температура редуктора > 85 °C', [t for t, _ in turbines if t.startswith('wt-k')]),
         ('rule-cheap-charge', 'Заряджання за низької ціни', 'ціна РДН < 50 EUR/МВт·год і SoC < 90 %', [b for b, _ in bess]),
         ('rule-inverter-derate', 'Обмеження інвертора при перегріві', 'температура IGBT > 70 °C', [i for i, _ in inverters])]
for rid, n, cond, targets in RULES:
    node('ControlRule', id=rid, name=n, conditionText=cond)
    for t in targets: rel('CONTROLS', rid, t, 'dispatch-regulation')

# ---------------- запис CSV ----------------
for f in OUT.glob('*.csv'): f.unlink()
for label, rows in nodes.items():
    keys = []
    for r in rows:
        for k in r:
            if k not in keys: keys.append(k)
    with open(OUT / f'nodes_{label.lower()}.csv', 'w', newline='', encoding='utf-8') as fh:
        w = csv.DictWriter(fh, fieldnames=keys, lineterminator='\n'); w.writeheader()
        for r in rows: w.writerow({k: ('' if r.get(k) is None else r.get(k)) for k in keys})
for t, rows in rels.items():
    with open(OUT / f'rels_{t.lower()}.csv', 'w', newline='', encoding='utf-8') as fh:
        w = csv.DictWriter(fh, fieldnames=['from', 'to', 'source', 'confidence', 'validFrom'], lineterminator='\n'); w.writeheader()
        for r in rows: w.writerow(r)

nn = sum(len(v) for v in nodes.values()); rr = sum(len(v) for v in rels.values())
print(f'вузлів: {nn}, зв\'язків: {rr}, міток: {len(nodes)}, типів зв\'язків: {len(rels)}')
for k, v in sorted(nodes.items()): print(f'  :{k:16} {len(v)}')
for k, v in sorted(rels.items()): print(f'  [{k:14}] {len(v)}')
