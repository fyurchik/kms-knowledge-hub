// CQ10 (аналіз впливу). Які запчастини і витрати спричинили попереджувальні сигнали,
// що переросли у відмови? Ланцюг глибиною 3: сигнал ← відмова ← ремонт → запчастина.
// Конструкції: шлях фіксованої довжини 3, length(), WITH, агрегація, collect(DISTINCT)
MATCH path = (a:AlarmEvent)<-[:CAUSED_BY]-(f:FailureEvent)<-[:TRIGGERED_BY]-(w:MaintenanceWork)-[:USES_PART]->(sp:SparePart)
WITH sp, length(path) AS depth, count(DISTINCT a) AS alarms, collect(DISTINCT f.id) AS failures
RETURN sp.name AS part, alarms, size(failures) AS failuresCnt, depth
ORDER BY alarms DESC, part;
