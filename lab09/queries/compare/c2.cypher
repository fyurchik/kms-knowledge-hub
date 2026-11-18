// P2. Яке обладнання має технічний стан нижче 80 %?
MATCH (e:Equipment) WHERE e.stateOfHealth < 80
RETURN e.id AS e, e.stateOfHealth AS health
ORDER BY health, e;
