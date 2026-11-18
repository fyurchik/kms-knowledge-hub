// CQ6. Як пов'язані відмова редуктора K-02 і підстанція «Львів-Західна» (найкоротший шлях)?
// Конструкції: shortestPath, неорієнтований шлях змінної довжини, nodes()/relationships()
MATCH (a:Event {id: 'ev-0001'}), (b:Substation {id: 'sub-lviv'})
MATCH path = shortestPath((a)-[*..6]-(b))
RETURN [n IN nodes(path) | n.id] AS chain, [r IN relationships(path) | type(r)] AS rels, length(path) AS hops;
