// 01 — обмеження цілісності та індекси (ідемпотентно: IF NOT EXISTS)
    CREATE CONSTRAINT entity_id_unique IF NOT EXISTS FOR (n:Entity) REQUIRE n.id IS UNIQUE;
    CREATE CONSTRAINT employee_email_unique IF NOT EXISTS FOR (n:Employee) REQUIRE n.email IS UNIQUE;
    CREATE CONSTRAINT record_number_unique IF NOT EXISTS FOR (n:Record) REQUIRE n.number IS UNIQUE;
    CREATE INDEX event_occurred_at IF NOT EXISTS FOR (n:Event) ON (n.occurredAt);
    CREATE INDEX equipment_health IF NOT EXISTS FOR (n:Equipment) ON (n.stateOfHealth);
    CREATE INDEX measurement_observed_at IF NOT EXISTS FOR (n:Measurement) ON (n.observedAt);
    CREATE TEXT INDEX entity_name_text IF NOT EXISTS FOR (n:Entity) ON (n.name);
    