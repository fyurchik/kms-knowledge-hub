// CQ4. Хто виконував аварійні ремонти, скільки їх було і скільки вони коштували?
// Конструкції: агрегація count/sum, WITH + фільтр після агрегації, ORDER BY
MATCH (w:CorrectiveRepair)-[:PERFORMED_BY]->(emp:Employee)-[:EMPLOYED_BY]->(c:Company)
WITH emp, c, count(w) AS repairs, sum(w.costEUR) AS totalEUR
WHERE repairs >= 1
RETURN emp.name AS employee, c.name AS company, repairs, totalEUR
ORDER BY totalEUR DESC;
