# Knowledge graph

The KG is built from the typed YAML registry under `data/` and serialized two ways:

- `kg/graph.gpickle` — full NetworkX `MultiDiGraph` (gitignored; regenerate via `npm run kg:build` or `python kg/build_graph.py`).
- `kg/graph.json` — compact JSON snapshot with a precomputed force-directed layout. Committed; the explorer-web `/kg` route reads this directly so the demo works without the FastAPI service running.

## Schema

Node kinds:

| kind              | source                              | id format                                |
| ----------------- | ----------------------------------- | ---------------------------------------- |
| `vertical`        | hard-coded list of 16 buckets       | `vertical:<slug>`                        |
| `subdomain`       | `data/taxonomy/<id>.yaml`           | `subdomain:<id>`                         |
| `persona`         | `subdomain.personas[]`              | `persona:<sub>::<slug(name)>`            |
| `decision`        | `subdomain.decisions[]`             | `decision:<id>`                          |
| `kpi`             | subdomain KPIs + KPI registry merge | `kpi:<id>`                               |
| `entity`          | `subdomain.dataModel.entities[]`    | `entity:<sub>::<slug(name)>`             |
| `source` / `source_local` | sources registry / inline source mention | `source:<id>` or `sourceLocal:<sub>::...` |
| `connector` / `connector_local` | connector registry / inline | `connector:<id>` or `connectorLocal:...` |
| `term`            | `data/glossary/glossary.yaml`       | `term:<slug(name)>`                      |

Edge labels: `hasSubdomain`, `hasPersona`, `hasDecision`, `hasKpi`, `hasEntity`, `usesSource`, `usesConnector`, `owns` (persona→decision), `supportsDecision` (kpi→decision), `reachedBy` (source→connector), `termRelatedTo` (term→subdomain or term→kpi).

Counts on the current registry (`npm run kg:build` will reprint these):

```
~2,700 nodes, ~3,000 edges
  vertical          16
  subdomain         110+
  persona           ~350
  decision          ~30
  kpi               ~600
  entity            ~600
  source / *_local  ~600
  connector / *_local ~380
  term              ~80
```

## API

`services/api/app/kg.py` exposes:

- `GET  /kg/stats` — node/edge counts by kind.
- `GET  /kg/snapshot` — the `graph.json` payload.
- `GET  /kg/node/{id}` — the node + its 1-hop neighbourhood.
- `GET  /kg/path?source=...&target=...` — shortest path between two nodes.
- `POST /kg/query` with `{ template, persona_id?, kpi_id?, ... }` — templated traversals: `persona_to_kpis`, `kpi_to_sources`, `subdomain_to_entities`, `vertical_to_subdomains`, `kpi_to_decisions`. These map 1-to-1 to the openCypher templates under `cypher/`.

## Cypher templates

`cypher/` keeps the openCypher contract for when the registry graduates to Neo4j or Memgraph. The templates use `$param` placeholders and stay in sync with the API templates above.

## Ontology

`ontology/domain_explorer.ttl` is the OWL/Turtle expression of the same shape — useful when you want a real RDF triplestore in the loop.
