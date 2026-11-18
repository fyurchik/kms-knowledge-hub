// P3. Скільки аварійних ремонтів виконав кожен працівник і на яку суму?
MATCH (w:CorrectiveRepair)-[:PERFORMED_BY]->(p:Employee)
RETURN p.name AS employee, count(w) AS repairs, sum(w.costEUR) AS totalEUR
ORDER BY totalEUR DESC;
