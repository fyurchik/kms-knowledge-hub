// CQ3. Які події з критичністю ≥ 4 сталися з червня 2026 року, на якому обладнанні та станції?
// Конструкції: фільтр за діапазоном дат (індекс event_occurred_at), WHERE, ланцюг з двох зв'язків
MATCH (ev:Event)-[:AFFECTS]->(e:Equipment)-[:INSTALLED_AT]->(p:Plant)
WHERE ev.occurredAt >= localdatetime('2026-06-01T00:00:00') AND ev.severity >= 4
RETURN ev.id AS event, ev.kind AS kind, ev.severity AS severity, e.id AS equipment, p.name AS plant
ORDER BY ev.occurredAt DESC;
