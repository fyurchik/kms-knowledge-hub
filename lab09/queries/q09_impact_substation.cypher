// CQ9 (аналіз впливу). Що зупиниться, якщо відмовить ПС «Івано-Франківськ»?
// Залежності до глибини 4: ФЕМ → інвертор → трансформатор → підстанція.
// Конструкції: шлях змінної довжини DEPENDS_ON*1..4, WITH, агрегація, CASE з перевіркою мітки
MATCH path = (x:Equipment)-[:DEPENDS_ON*1..4]->(s:Substation {id: 'sub-ivano-frankivsk'})
MATCH (x)-[:INSTALLED_AT]->(p:Plant)
WITH p, x, length(path) AS depth
RETURN p.name AS plant, x.kind AS kind, count(DISTINCT x) AS affectedUnits, max(depth) AS depth,
       sum(CASE WHEN x:GeneratingUnit THEN x.ratedPowerKW ELSE 0 END) AS lostGenerationKW
ORDER BY plant, depth, kind;
