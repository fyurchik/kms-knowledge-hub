// 03 — імпорт зв'язків з властивостями походження (source, confidence, validFrom)

LOAD CSV WITH HEADERS FROM 'file:///rels_affects.csv' AS row
    MATCH (a:Entity {id: row.from})
    MATCH (b:Entity {id: row.to})
    MERGE (a)-[r:AFFECTS]->(b)
    SET r.source = row.source, r.confidence = toFloat(row.confidence), r.validFrom = date(row.validFrom);

LOAD CSV WITH HEADERS FROM 'file:///rels_based_on.csv' AS row
    MATCH (a:Entity {id: row.from})
    MATCH (b:Entity {id: row.to})
    MERGE (a)-[r:BASED_ON]->(b)
    SET r.source = row.source, r.confidence = toFloat(row.confidence), r.validFrom = date(row.validFrom);

LOAD CSV WITH HEADERS FROM 'file:///rels_caused_by.csv' AS row
    MATCH (a:Entity {id: row.from})
    MATCH (b:Entity {id: row.to})
    MERGE (a)-[r:CAUSED_BY]->(b)
    SET r.source = row.source, r.confidence = toFloat(row.confidence), r.validFrom = date(row.validFrom);

LOAD CSV WITH HEADERS FROM 'file:///rels_controls.csv' AS row
    MATCH (a:Entity {id: row.from})
    MATCH (b:Entity {id: row.to})
    MERGE (a)-[r:CONTROLS]->(b)
    SET r.source = row.source, r.confidence = toFloat(row.confidence), r.validFrom = date(row.validFrom);

LOAD CSV WITH HEADERS FROM 'file:///rels_depends_on.csv' AS row
    MATCH (a:Entity {id: row.from})
    MATCH (b:Entity {id: row.to})
    MERGE (a)-[r:DEPENDS_ON]->(b)
    SET r.source = row.source, r.confidence = toFloat(row.confidence), r.validFrom = date(row.validFrom);

LOAD CSV WITH HEADERS FROM 'file:///rels_documented_in.csv' AS row
    MATCH (a:Entity {id: row.from})
    MATCH (b:Entity {id: row.to})
    MERGE (a)-[r:DOCUMENTED_IN]->(b)
    SET r.source = row.source, r.confidence = toFloat(row.confidence), r.validFrom = date(row.validFrom);

LOAD CSV WITH HEADERS FROM 'file:///rels_employed_by.csv' AS row
    MATCH (a:Entity {id: row.from})
    MATCH (b:Entity {id: row.to})
    MERGE (a)-[r:EMPLOYED_BY]->(b)
    SET r.source = row.source, r.confidence = toFloat(row.confidence), r.validFrom = date(row.validFrom);

LOAD CSV WITH HEADERS FROM 'file:///rels_forecast_for.csv' AS row
    MATCH (a:Entity {id: row.from})
    MATCH (b:Entity {id: row.to})
    MERGE (a)-[r:FORECAST_FOR]->(b)
    SET r.source = row.source, r.confidence = toFloat(row.confidence), r.validFrom = date(row.validFrom);

LOAD CSV WITH HEADERS FROM 'file:///rels_has_part.csv' AS row
    MATCH (a:Entity {id: row.from})
    MATCH (b:Entity {id: row.to})
    MERGE (a)-[r:HAS_PART]->(b)
    SET r.source = row.source, r.confidence = toFloat(row.confidence), r.validFrom = date(row.validFrom);

LOAD CSV WITH HEADERS FROM 'file:///rels_installed_at.csv' AS row
    MATCH (a:Entity {id: row.from})
    MATCH (b:Entity {id: row.to})
    MERGE (a)-[r:INSTALLED_AT]->(b)
    SET r.source = row.source, r.confidence = toFloat(row.confidence), r.validFrom = date(row.validFrom);

LOAD CSV WITH HEADERS FROM 'file:///rels_located_in.csv' AS row
    MATCH (a:Entity {id: row.from})
    MATCH (b:Entity {id: row.to})
    MERGE (a)-[r:LOCATED_IN]->(b)
    SET r.source = row.source, r.confidence = toFloat(row.confidence), r.validFrom = date(row.validFrom);

LOAD CSV WITH HEADERS FROM 'file:///rels_measured_by.csv' AS row
    MATCH (a:Entity {id: row.from})
    MATCH (b:Entity {id: row.to})
    MERGE (a)-[r:MEASURED_BY]->(b)
    SET r.source = row.source, r.confidence = toFloat(row.confidence), r.validFrom = date(row.validFrom);

LOAD CSV WITH HEADERS FROM 'file:///rels_observes.csv' AS row
    MATCH (a:Entity {id: row.from})
    MATCH (b:Entity {id: row.to})
    MERGE (a)-[r:OBSERVES]->(b)
    SET r.source = row.source, r.confidence = toFloat(row.confidence), r.validFrom = date(row.validFrom);

LOAD CSV WITH HEADERS FROM 'file:///rels_operated_by.csv' AS row
    MATCH (a:Entity {id: row.from})
    MATCH (b:Entity {id: row.to})
    MERGE (a)-[r:OPERATED_BY]->(b)
    SET r.source = row.source, r.confidence = toFloat(row.confidence), r.validFrom = date(row.validFrom);

LOAD CSV WITH HEADERS FROM 'file:///rels_performed_by.csv' AS row
    MATCH (a:Entity {id: row.from})
    MATCH (b:Entity {id: row.to})
    MERGE (a)-[r:PERFORMED_BY]->(b)
    SET r.source = row.source, r.confidence = toFloat(row.confidence), r.validFrom = date(row.validFrom);

LOAD CSV WITH HEADERS FROM 'file:///rels_targets.csv' AS row
    MATCH (a:Entity {id: row.from})
    MATCH (b:Entity {id: row.to})
    MERGE (a)-[r:TARGETS]->(b)
    SET r.source = row.source, r.confidence = toFloat(row.confidence), r.validFrom = date(row.validFrom);

LOAD CSV WITH HEADERS FROM 'file:///rels_triggered_by.csv' AS row
    MATCH (a:Entity {id: row.from})
    MATCH (b:Entity {id: row.to})
    MERGE (a)-[r:TRIGGERED_BY]->(b)
    SET r.source = row.source, r.confidence = toFloat(row.confidence), r.validFrom = date(row.validFrom);

LOAD CSV WITH HEADERS FROM 'file:///rels_uses_part.csv' AS row
    MATCH (a:Entity {id: row.from})
    MATCH (b:Entity {id: row.to})
    MERGE (a)-[r:USES_PART]->(b)
    SET r.source = row.source, r.confidence = toFloat(row.confidence), r.validFrom = date(row.validFrom);
