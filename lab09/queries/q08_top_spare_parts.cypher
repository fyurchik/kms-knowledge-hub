// CQ8. Які запчастини використовуються найчастіше і скільки на них витрачено?
// Конструкції: агрегація count/sum, ORDER BY, LIMIT
MATCH (w:MaintenanceWork)-[:USES_PART]->(sp:SparePart)
RETURN sp.name AS part, count(w) AS usedIn, sum(sp.unitCostEUR) AS partsCostEUR
ORDER BY usedIn DESC, part
LIMIT 5;
