// 05 — навмисне порушення унікальності: має завершитися помилкою
    // Neo.ClientError.Schema.ConstraintValidationFailed
    CREATE (:Entity:Plant {id: 'wf-karpatska', name: 'Дублікат ВЕС «Карпатська»'});
    