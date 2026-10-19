"""Temporary diagnostic: compact description of identifier nodes in a built graph (compare CI against a local build)."""
from __future__ import annotations

P = "PREFIX ftf: <https://domain-explorer.dev/ftf#>\n"


def probe(kg) -> str:
    a = kg.sparql(P + "SELECT ?system ?kind (COUNT(*) AS ?n) WHERE { ?x ftf:system ?system ; ftf:kind ?kind } GROUP BY ?system ?kind ORDER BY ?system ?kind")
    b = kg.sparql(P + "SELECT ?p ?o WHERE { <https://domain-explorer.dev/ftf/id/unit/OEM-24-0398> ?p ?o } ORDER BY ?p ?o")
    c = kg.sparql(P + "SELECT ?system ?value WHERE { <https://domain-explorer.dev/ftf/id/unit/OEM-24-0398> ftf:identifiers ?x . ?x ftf:system ?system ; ftf:value ?value } ORDER BY ?system")
    return "ids " + ";".join(f"{r['system']}/{r['kind']}={r['n']}" for r in a) + "\nunit " + ";".join(f"{str(r['p']).split('#')[-1]}={str(r['o'])[:40]}" for r in b) + "\nidv " + ";".join(f"{r['system']}={r['value']}" for r in c)
