// P4 (вплив). Яке обладнання транзитивно залежить від ПС «Івано-Франківськ»?
MATCH (x:Equipment)-[:DEPENDS_ON*]->(:Substation {id: 'sub-ivano-frankivsk'}),
      (x)-[:INSTALLED_AT]->(p:Plant)
RETURN p.name AS plantName, x.kind AS kind, count(DISTINCT x) AS affected
ORDER BY plantName, kind;
