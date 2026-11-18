// 02 — імпорт вузлів (LOAD CSV + MERGE за унікальним id; повторний запуск не створює дублікатів)

// CSV-файли мають лежати в теці import/ бази Neo4j (див. README)

LOAD CSV WITH HEADERS FROM 'file:///nodes_company.csv' AS row
MERGE (n:Entity {id: row.id})
SET n:Company,
    n.name = CASE WHEN row.name = '' THEN null ELSE row.name END,
    n.taxId = CASE WHEN row.taxId = '' THEN null ELSE row.taxId END;

LOAD CSV WITH HEADERS FROM 'file:///nodes_component.csv' AS row
MERGE (n:Entity {id: row.id})
SET n:Component,
    n.name = CASE WHEN row.name = '' THEN null ELSE row.name END,
    n.kind = CASE WHEN row.kind = '' THEN null ELSE row.kind END
FOREACH (_ IN CASE WHEN row.kind = 'Gearbox' THEN [1] ELSE [] END | SET n:Gearbox)
FOREACH (_ IN CASE WHEN row.kind = 'Generator' THEN [1] ELSE [] END | SET n:Generator)
FOREACH (_ IN CASE WHEN row.kind = 'Rotor' THEN [1] ELSE [] END | SET n:Rotor);

LOAD CSV WITH HEADERS FROM 'file:///nodes_controlrule.csv' AS row
MERGE (n:Entity {id: row.id})
SET n:ControlRule,
    n.name = CASE WHEN row.name = '' THEN null ELSE row.name END,
    n.conditionText = CASE WHEN row.conditionText = '' THEN null ELSE row.conditionText END;

LOAD CSV WITH HEADERS FROM 'file:///nodes_employee.csv' AS row
MERGE (n:Entity {id: row.id})
SET n:Employee,
    n.name = CASE WHEN row.name = '' THEN null ELSE row.name END,
    n.position = CASE WHEN row.position = '' THEN null ELSE row.position END,
    n.email = CASE WHEN row.email = '' THEN null ELSE row.email END;

LOAD CSV WITH HEADERS FROM 'file:///nodes_equipment.csv' AS row
MERGE (n:Entity {id: row.id})
SET n:Equipment,
    n.name = CASE WHEN row.name = '' THEN null ELSE row.name END,
    n.kind = CASE WHEN row.kind = '' THEN null ELSE row.kind END,
    n.model = CASE WHEN row.model = '' THEN null ELSE row.model END,
    n.ratedPowerKW = toFloat(row.ratedPowerKW),
    n.stateOfHealth = toFloat(row.stateOfHealth),
    n.hubHeightM = toFloat(row.hubHeightM),
    n.capacityMWh = toFloat(row.capacityMWh)
FOREACH (_ IN CASE WHEN row.kind = 'Anemometer' THEN [1] ELSE [] END | SET n:Anemometer:Sensor)
FOREACH (_ IN CASE WHEN row.kind = 'BatteryStorage' THEN [1] ELSE [] END | SET n:BatteryStorage)
FOREACH (_ IN CASE WHEN row.kind = 'Inverter' THEN [1] ELSE [] END | SET n:Inverter)
FOREACH (_ IN CASE WHEN row.kind = 'PVArray' THEN [1] ELSE [] END | SET n:PVArray:GeneratingUnit)
FOREACH (_ IN CASE WHEN row.kind = 'Pyranometer' THEN [1] ELSE [] END | SET n:Pyranometer:Sensor)
FOREACH (_ IN CASE WHEN row.kind = 'Substation' THEN [1] ELSE [] END | SET n:Substation)
FOREACH (_ IN CASE WHEN row.kind = 'TemperatureSensor' THEN [1] ELSE [] END | SET n:TemperatureSensor:Sensor)
FOREACH (_ IN CASE WHEN row.kind = 'Transformer' THEN [1] ELSE [] END | SET n:Transformer)
FOREACH (_ IN CASE WHEN row.kind = 'WindTurbine' THEN [1] ELSE [] END | SET n:WindTurbine:GeneratingUnit);

LOAD CSV WITH HEADERS FROM 'file:///nodes_event.csv' AS row
MERGE (n:Entity {id: row.id})
SET n:Event,
    n.name = CASE WHEN row.name = '' THEN null ELSE row.name END,
    n.kind = CASE WHEN row.kind = '' THEN null ELSE row.kind END,
    n.occurredAt = CASE WHEN row.occurredAt = '' THEN null ELSE localdatetime(row.occurredAt) END,
    n.severity = toInteger(row.severity),
    n.durationH = toFloat(row.durationH)
FOREACH (_ IN CASE WHEN row.kind = 'AlarmEvent' THEN [1] ELSE [] END | SET n:AlarmEvent)
FOREACH (_ IN CASE WHEN row.kind = 'CurtailmentEvent' THEN [1] ELSE [] END | SET n:CurtailmentEvent)
FOREACH (_ IN CASE WHEN row.kind = 'FailureEvent' THEN [1] ELSE [] END | SET n:FailureEvent);

LOAD CSV WITH HEADERS FROM 'file:///nodes_forecast.csv' AS row
MERGE (n:Entity {id: row.id})
SET n:Forecast,
    n.name = CASE WHEN row.name = '' THEN null ELSE row.name END,
    n.forecastDate = CASE WHEN row.forecastDate = '' THEN null ELSE date(row.forecastDate) END,
    n.forecastMWh = toFloat(row.forecastMWh);

LOAD CSV WITH HEADERS FROM 'file:///nodes_gridnode.csv' AS row
MERGE (n:Entity {id: row.id})
SET n:GridNode,
    n.name = CASE WHEN row.name = '' THEN null ELSE row.name END,
    n.voltageKV = toInteger(row.voltageKV);

LOAD CSV WITH HEADERS FROM 'file:///nodes_maintenancework.csv' AS row
MERGE (n:Entity {id: row.id})
SET n:MaintenanceWork,
    n.name = CASE WHEN row.name = '' THEN null ELSE row.name END,
    n.kind = CASE WHEN row.kind = '' THEN null ELSE row.kind END,
    n.costEUR = toFloat(row.costEUR),
    n.startedAt = CASE WHEN row.startedAt = '' THEN null ELSE localdatetime(row.startedAt) END
FOREACH (_ IN CASE WHEN row.kind = 'CorrectiveRepair' THEN [1] ELSE [] END | SET n:CorrectiveRepair)
FOREACH (_ IN CASE WHEN row.kind = 'PlannedMaintenance' THEN [1] ELSE [] END | SET n:PlannedMaintenance);

LOAD CSV WITH HEADERS FROM 'file:///nodes_measurement.csv' AS row
MERGE (n:Entity {id: row.id})
SET n:Measurement,
    n.value = toFloat(row.value),
    n.unit = CASE WHEN row.unit = '' THEN null ELSE row.unit END,
    n.observedAt = CASE WHEN row.observedAt = '' THEN null ELSE localdatetime(row.observedAt) END;

LOAD CSV WITH HEADERS FROM 'file:///nodes_plant.csv' AS row
MERGE (n:Entity {id: row.id})
SET n:Plant,
    n.name = CASE WHEN row.name = '' THEN null ELSE row.name END,
    n.kind = CASE WHEN row.kind = '' THEN null ELSE row.kind END,
    n.installedCapacityMW = toFloat(row.installedCapacityMW),
    n.commissioningDate = CASE WHEN row.commissioningDate = '' THEN null ELSE date(row.commissioningDate) END
FOREACH (_ IN CASE WHEN row.kind = 'SolarPlant' THEN [1] ELSE [] END | SET n:SolarPlant)
FOREACH (_ IN CASE WHEN row.kind = 'WindFarm' THEN [1] ELSE [] END | SET n:WindFarm);

LOAD CSV WITH HEADERS FROM 'file:///nodes_record.csv' AS row
MERGE (n:Entity {id: row.id})
SET n:Record,
    n.number = CASE WHEN row.number = '' THEN null ELSE row.number END,
    n.name = CASE WHEN row.name = '' THEN null ELSE row.name END,
    n.date = CASE WHEN row.date = '' THEN null ELSE date(row.date) END;

LOAD CSV WITH HEADERS FROM 'file:///nodes_region.csv' AS row
MERGE (n:Entity {id: row.id})
SET n:Region,
    n.name = CASE WHEN row.name = '' THEN null ELSE row.name END;

LOAD CSV WITH HEADERS FROM 'file:///nodes_sparepart.csv' AS row
MERGE (n:Entity {id: row.id})
SET n:SparePart,
    n.name = CASE WHEN row.name = '' THEN null ELSE row.name END,
    n.unitCostEUR = toFloat(row.unitCostEUR);

LOAD CSV WITH HEADERS FROM 'file:///nodes_weatherdata.csv' AS row
MERGE (n:Entity {id: row.id})
SET n:WeatherData,
    n.name = CASE WHEN row.name = '' THEN null ELSE row.name END,
    n.windSpeedMS = toFloat(row.windSpeedMS),
    n.irradianceWm2 = toFloat(row.irradianceWm2);
