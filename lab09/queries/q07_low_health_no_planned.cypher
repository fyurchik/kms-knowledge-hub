// CQ7. Яке обладнання має технічний стан нижче 80 % і чи заплановано для нього ТО?
// Конструкції: фільтр за індексованою властивістю, OPTIONAL MATCH, WITH + count, CASE
MATCH (e:Equipment)-[:INSTALLED_AT]->(p:Plant)
WHERE e.stateOfHealth < 80
OPTIONAL MATCH (w:PlannedMaintenance)-[:TARGETS]->(e)
WITH e, p, count(w) AS planned
RETURN e.id AS equipment, e.kind AS kind, e.stateOfHealth AS health, p.name AS plant,
       CASE WHEN planned = 0 THEN 'немає ТО' ELSE 'ТО заплановано' END AS status
ORDER BY health, equipment;
