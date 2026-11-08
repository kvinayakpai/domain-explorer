# Factory to Field

A synthetic but realistic world of one refinery, one oil field and the pump maker that supplies both, with an ontology, a knowledge graph and an agent layer on top. Everything is simulated; no real data is used.

```
ontology (LinkML) ──► OWL + SHACL + Pydantic + TS
world (seeded simulator) ──► SAP PM · historian · SCADA · P&ID · EDMS · OSDU · MES/ERP/PLM/QMS (+ answer key)
kg (pyoxigraph) ◄── identity resolution with provenance, review queue, SHACL gate
sim (HTTP) ◄── PI Web API · OPC UA gateway · SAP PM OData · OSDU · PLM · MES · QMS · production planning
agents ◄── Source (files or sim over HTTP) ◄── MCP tools (kg · historian · eam · plant · maker · drafts · ot) ──► reports, drafts, audit trail
pilot ◄── identity provider (RS256 JWT) · hash-chained audit log · review queue workflow · UNS replay over MQTT · OAuth2 connectors · eval harness
```

## Run it

One command with Docker (builds the world and graph into the image, then serves the live console on http://localhost:8800):

```bash
docker compose -f factory_to_field/docker-compose.yml up --build
```

Or step by step:

```bash
pip install -r factory_to_field/requirements.txt
python -m factory_to_field.ontology.build          # regenerate OWL/SHACL/Pydantic/TS (add --check in CI)
python -m factory_to_field.world.build             # ~10 s, seed 42, writes factory_to_field/build/world
python -m factory_to_field.kg.build                # ~100 s with SHACL; add --skip-shacl for ~15 s
python -m factory_to_field.agents.gold             # 10 gold cases, scored against the answer key
python -m factory_to_field.sim.server --port 8765  # the plant's systems as local REST services (no real systems needed)
python -m factory_to_field.demo                    # end to end: agents work through the simulators, humans approve, drafts are released to simulated SAP/QMS
FTF_SIM_URL=http://127.0.0.1:8765 python -m factory_to_field.agents.gold   # gold cases through the simulators
FTF_SIM_URL=http://127.0.0.1:8765 FTF_VENDOR=1 python -m factory_to_field.agents.gold   # same, with work orders and DIFA read through the Maximo and ESP/DIFA mocks
python -m factory_to_field.ui.build_ui             # ui/case_viewer.html (one self-contained page)
python -m pytest -c factory_to_field/pytest.ini factory_to_field/tests
python -m factory_to_field.agents.mcp_servers kg   # any of: kg historian eam plant maker drafts ot
python -m factory_to_field.ui.live_app --port 8800 # live console: sign in, approve, release, review queue, audit log, UNS replay
python -m factory_to_field.pilot.uns               # replay the plant's UNS over MQTT; alarms open agent cases
python -m factory_to_field.pilot.review list       # identity-resolution review queue (decide, then apply)
python -m factory_to_field.agents.eval_live        # gold + adversarial cases; --planner model needs ANTHROPIC_API_KEY
```

## The ideas that matter

- **Position versus unit.** A functional location (P-101A) and the serialised unit installed in it are different things joined by a dated installation. A failure belongs to the unit that was installed *then*. Searching by today's serial misattributes it (gold case CASE-3002).
- **The world has a clock.** Every case carries an `as_of`; tools never return anything newer.
- **Identity resolution is scored.** Links are made by exact key, tag grammar, alias table or fuzzy match, each with a confidence and an evidence string; below 0.90 they go to a review queue. `truth.json` is used only for scoring (gate: recall 0.95, precision 0.98).
- **Agents cannot act, only propose.** OT is read-only (`ot.write_setpoint` always refuses). Writes are drafts for a named approver role; there is no approve tool. Free text from systems is returned as `untrusted` and never changes behaviour (CASE-3008). A verifier checks every citation and every quoted number against the tool-call log.
- **Planner is replaceable.** `agents/agent.py` is a deterministic playbook planner; `agents/llm.py` runs a model over the same tools and is checked by the same verifier (tested with a scripted client).

## System simulators

There are no real SAP, PI, OSDU or PLM/MES systems in this project, so `sim/server.py` plays them: PI Web API (points, summary, recorded, event frames), an OPC UA gateway for field SCADA, a condition-monitoring API, SAP S/4 PM OData v2 (`$filter`, `$orderby`, `$top`, `$expand`), OSDU search and storage, the pump maker's PLM, MES and QMS, and production planning. They serve the generated world and never see the answer key.

- Credentials are bearer tokens. The agent's `ro-agent` token reads everything and writes nothing. PI and SCADA refuse every write, whoever asks.
- A write needs the `release` token plus `X-Approved-By` and `X-Draft-Id`. That is the path `agents/release.py` takes after a named person approves a draft. With an identity provider configured, signed tokens replace both (see Pilot readiness).
- Like the real systems, SAP needs a CSRF token before a write and pages large results, PI Web API pages points, OSDU needs a data partition, and `POST /sim/faults` can rate-limit requests to test retries.
- `agents/sources.py` has two interchangeable backends: `FileSource` and `HttpSource`. The gold cases pass through both. A real connector would implement the same interface.
- The knowledge-graph build still reads the generated files directly; they are the same files the simulators serve.

## Pilot readiness (gate G5) without real systems

`pilot/` holds what a pilot needs that does not depend on real plant systems:

- **Signed identities.** `pilot/idp.py` is an OIDC-style identity provider: people sign in and get RS256 tokens carrying their name and roles; the agent gets a client-credentials token with read scope only. The simulators verify tokens against the provider's JWKS. With `require_identity`, a write needs the token of a named person holding the role that route requires, and the static `release` token is refused. The console uses this path.
- **Two tenants.** The refinery/field operator is the primary side; the pump maker is secondary. `ftf-operator-agent` (scope `operator.read`) cannot read the maker's PLM, MES or QMS, and `ftf-maker-agent` (`maker.read`) cannot read the operator's systems; the simulators answer 403. When the operator agent needs a maker fact (ECO route, DIFA, factory test), the report says it is not visible and who holds it. The live console runs as the operator agent.
- **Audit log.** `pilot/audit.py` writes every sign-in, approval, refusal, release and review decision as hash-chained JSON lines under `build/audit/`; editing or deleting a line breaks the chain and `verify()` says where.
- **Review workflow.** `pilot/review.py` lets a data steward link or dismiss each item in the identity-resolution queue, records who decided and how long it took, and rebuilds the graph with the decisions (queue 3 -> 0 in the tests).
- **UNS over MQTT.** `pilot/uns.py` starts an MQTT broker, publishes `uns_replay.jsonl` on its ISA-95 topics and runs an alarm listener: the first value above a tag's alarm limit opens an agent case with the alarm's own timestamp as the clock (both alarms in the replay open the right cases).
- **Connectors.** `agents/sources.py` now handles what the real systems do: OAuth2 token refresh on 401, retries with back-off on 429 and 5xx, SAP OData `__next` and PI `Links.Next` paging, SAP CSRF tokens before writes, OSDU `data-partition-id`. `pilot/connectors.py` adds the client-credentials provider and a per-system config (`connectors.example.yaml`); secrets come from environment variables.
- **Model-planner evaluation.** `agents/eval_live.py` scores any planner on the 10 gold cases plus 5 adversarial ones (injected authority, approve-and-release requests, future data, the stuck sensor in other words, containment counts) by facts, evidence and guardrails. The playbook planner passes 15 of 15; the model planner needs an API key.

What stays open for G5 itself: real endpoints and credentials, the company's identity provider, real reviewers and cases, a security review.

## Layout

| path | what |
|---|---|
| `ontology/*.yaml` | core, refinery, oilfield, factory, kpi modules; `generated/` is built, do not edit |
| `world/` | simulator: factory, refinery, field, signals, renderers, realism checks, answer key |
| `kg/` | pipeline (resolution), store (SPARQL helpers), SHACL, scoring |
| `queries/` | competency questions cq01-cq11 as SPARQL files |
| `agents/` | core, tools, drafts, agent, playbooks, llm, schema, mcp_servers, verifier, gold |
| `sim/` | the system simulators (HTTP) |
| `demo.py` | one command, end to end |
| `ui/` | case viewer (template + built page) |
| `pilot/` | identity provider, audit log, approvals, review workflow, UNS replay, connector config |
| `tests/` | world, KG, agents, simulators, pilot |

## Mock source systems

Six deep mocks, one per product a refinery reliability team is likely to connect, so a connector can be built and tested without a real installation (`sim/vendors.py`; `GET /v/` lists them; the original simulators in `sim/server.py` cover PI Web API, the OPC UA gateway, SAP PM OData, OSDU, PLM, MES and QMS). Each follows its product's field names and paging, and three make the client handle session expiry. All of them serve the same simulated plant; the health and alert logic is a rule over vibration data, not a vendor model.

| Mock (`/v/<slug>/`) | Product | Vendor | Quirks a client must handle |
|---|---|---|---|
| `pi_af` | PI System / PI Asset Framework | AVEVA | WebIds, `startIndex`/`maxCount` paging with `Links.Next`, quality flags |
| `deltav` | DeltaV | Emerson | session required; expires after 25 requests (401), then sign in again |
| `maximo` | Maximo | IBM | OSLC `oslc.where`, `pageno` paging with `nextPage` |
| `system1` | Bently Nevada System 1 | Baker Hughes | session expiry; opaque `nextCursor` paging |
| `ge_apm` | APM (Meridium, SmartSignal) | GE Vernova | session expiry; OData `$top`/`$skip` with `@odata.nextLink` |
| `esp_difa` | ESP surveillance and DIFA records | Baker Hughes / SLB | DIFA reports and drive events (the maker-side feed) |

Sessions: `POST /v/<slug>/session` returns a token to send in the `x-session` header; every request also needs `Authorization: Bearer ro-agent`.

**Retired.** 35 earlier mocks (other historians, control systems, condition-monitoring and APM products, MOM systems, Infor and the two Maximo duplicates) were renamed copies of these dialects and were removed on 2026-11-08. The taxonomies still name those products; they have no mock. The list is `vendors.RETIRED`.

Run them with the other simulators: `python -m factory_to_field.sim.server --port 8765`, then for example `GET /v/maximo/oslc/os/mxwo?oslc.where=spi:status="COMP"` or `GET /v/pi_af/tags?maxCount=50` with `Authorization: Bearer ro-agent`.
