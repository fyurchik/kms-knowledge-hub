// P1. Скільки обладнання кожного типу встановлено на ВЕС «Карпатська» і яка його потужність?
MATCH (e:Equipment)-[:INSTALLED_AT]->(:Plant {id: 'wf-karpatska'})
RETURN e.kind AS kind, count(e) AS units, sum(coalesce(e.ratedPowerKW, 0)) AS totalKW
ORDER BY totalKW DESC, kind;
