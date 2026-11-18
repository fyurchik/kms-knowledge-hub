// GDS — аналіз графа (ЛР 9, результат 4). Потрібен плагін Graph Data Science.
// 1. Проєкція всього графа як неорієнтованого (усі мітки, усі типи зв'язків)
CALL gds.graph.drop('kms', false) YIELD graphName;
CALL gds.graph.project('kms', '*', {ALL: {type: '*', orientation: 'UNDIRECTED'}})
YIELD graphName, nodeCount, relationshipCount;
// 2. PageRank: топ-10 найважливіших вузлів
CALL gds.pageRank.stream('kms', {maxIterations: 20, dampingFactor: 0.85, concurrency: 1})
YIELD nodeId, score
WITH gds.util.asNode(nodeId) AS n, score
RETURN n.id AS id, n.name AS name, [l IN labels(n) WHERE l <> 'Entity'][0] AS label, round(score, 3) AS pagerank
ORDER BY pagerank DESC LIMIT 10;
// 3. Louvain: спільноти
CALL gds.louvain.stream('kms', {concurrency: 1})
YIELD nodeId, communityId
WITH communityId, collect(gds.util.asNode(nodeId)) AS members
RETURN communityId, size(members) AS size,
       [m IN members WHERE m:Plant | m.name] AS plants,
       [m IN members | m.id][0..6] AS sample
ORDER BY size DESC LIMIT 10;
// 4. Збереження результатів як властивостей вузлів
CALL gds.pageRank.write('kms', {writeProperty: 'pagerank', maxIterations: 20, dampingFactor: 0.85, concurrency: 1})
YIELD nodePropertiesWritten;
CALL gds.louvain.write('kms', {writeProperty: 'community', concurrency: 1})
YIELD communityCount, modularity;
// 5. Перевірка збереження
MATCH (n:Entity) WHERE n.pagerank IS NOT NULL AND n.community IS NOT NULL
RETURN count(n) AS nodesWithResults, count(DISTINCT n.community) AS communities;
