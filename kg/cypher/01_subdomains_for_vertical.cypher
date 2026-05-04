// All subdomains for a given vertical.
MATCH (v:Vertical {id: $vertical})-[:HAS_SUBDOMAIN]->(s:Subdomain)
RETURN s.id AS id, s.name AS name, s.oneLiner AS oneLiner
ORDER BY s.name;
