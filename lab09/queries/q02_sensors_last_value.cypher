// CQ2. Які датчики контролюють турбіни ВЕС «Карпатська» і яке їхнє останнє вимірювання?
// Конструкції: OPTIONAL MATCH, WITH + ORDER BY + collect()[0] (останнє значення), LIMIT
MATCH (t:WindTurbine)-[:INSTALLED_AT]->(:Plant {id: 'wf-karpatska'})
OPTIONAL MATCH (s:Sensor)-[:OBSERVES]->(t)
OPTIONAL MATCH (m:Measurement)-[:MEASURED_BY]->(s)
WITH t, s, m ORDER BY m.observedAt DESC
WITH t, s, collect(m)[0] AS last
RETURN t.id AS turbine, s.id AS sensor, last.value AS lastValue, last.unit AS unit
ORDER BY lastValue DESC, turbine
LIMIT 5;
