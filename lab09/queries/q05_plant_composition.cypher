// CQ5. З чого складається ВЕС «Карпатська» на будь-якому рівні вкладеності (обладнання → вузли)?
// Конструкції: шлях змінної довжини *1..2 з кількома типами зв'язків, count(DISTINCT)
MATCH (p:Plant {id: 'wf-karpatska'})-[:INSTALLED_AT|HAS_PART*1..2]-(x)
WHERE x <> p
RETURN x.kind AS kind, count(DISTINCT x) AS cnt
ORDER BY cnt DESC, kind;
