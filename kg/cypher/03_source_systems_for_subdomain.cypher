// Source systems and their connectors for a subdomain.
MATCH (s:Subdomain {id: $subdomain})<-[:LANDS_IN]-(src:SourceSystem)
OPTIONAL MATCH (src)-[:REACHED_BY]->(c:Connector)
RETURN src.vendor AS vendor, src.product AS product, src.category AS category,
       collect({type: c.type, protocol: c.protocol, auth: c.auth}) AS connectors
ORDER BY vendor;
