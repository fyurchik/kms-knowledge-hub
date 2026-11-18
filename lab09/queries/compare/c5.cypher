// P5. Які події з критичністю ≥ 4 сталися і чи складено для них акт?
MATCH (ev:Event) WHERE ev.severity >= 4
OPTIONAL MATCH (ev)-[:DOCUMENTED_IN]->(r:Record)
RETURN ev.id AS ev, ev.severity AS severity, r.number AS record
ORDER BY ev;
