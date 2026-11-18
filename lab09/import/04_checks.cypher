// 04 — перевірки після імпорту
    MATCH (n) RETURN count(n) AS nodes;
    MATCH ()-[r]->() RETURN count(r) AS relationships;
    MATCH (n) UNWIND labels(n) AS label RETURN label, count(*) AS cnt ORDER BY cnt DESC;
    MATCH ()-[r]->() RETURN type(r) AS type, count(*) AS cnt ORDER BY cnt DESC;
    SHOW CONSTRAINTS YIELD name, type, labelsOrTypes, properties;
    SHOW INDEXES YIELD name, type, labelsOrTypes, properties, state;
    