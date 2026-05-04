// From a KPI back to the personas that consume the decisions it supports.
MATCH (k:Kpi {id: $kpi})-[:SUPPORTS_DECISION]->(d:Decision)<-[:OWNS_DECISION]-(p:Persona)
RETURN k.name AS kpi, d.statement AS decision, p.title AS persona
ORDER BY persona;
