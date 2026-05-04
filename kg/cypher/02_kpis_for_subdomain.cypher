// All KPIs (with decisions) for a given subdomain.
MATCH (s:Subdomain {id: $subdomain})-[:HAS_KPI]->(k:Kpi)
OPTIONAL MATCH (k)-[:SUPPORTS_DECISION]->(d:Decision)
RETURN k.id AS kpi_id, k.name AS kpi_name, k.formula AS formula,
       k.unit AS unit, collect(d.id) AS decisions
ORDER BY k.name;
