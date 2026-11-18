// CQ1. Яке обладнання встановлено на ВЕС «Карпатська» і яка сумарна потужність за типами?
// Конструкції: шаблон з властивістю, агрегація count/sum, coalesce, ORDER BY
MATCH (e:Equipment)-[:INSTALLED_AT]->(p:Plant {id: 'wf-karpatska'})
RETURN e.kind AS kind, count(e) AS units, sum(coalesce(e.ratedPowerKW, 0)) AS totalKW
ORDER BY totalKW DESC, kind;
