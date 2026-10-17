# Factory to Field: plan and status (17 Oct 2026)

Branch `feat/oge-parallel-tracks`. Supersedes the 12-week single-track plan. Refinery and oil-field tracks are built in parallel on one shared core, with the pump maker (Kestrel Pump Works) joining them.

## Status by phase

| Phase | What | Status | Evidence |
|---|---|---|---|
| 0 Stabilise | Object-shaped challenges render, Vitest aliases fixed, `@types/node` added | Done (commit cb3c9e7) | Vitest and typecheck green on the branch |
| 1 Ontology | LinkML modules (core, refinery, oilfield, factory, kpi); generated OWL, closed SHACL, Pydantic, TypeScript, JSON-LD | Done | `ontology.build --check` clean; 11 competency questions as SPARQL (`queries/cq01-cq11`) |
| 2 Digital world | Seeded simulator (seed 42): 3 refineries, 12 ESP wells + 10 gas-lift wells, 2,568 factory build records; rendered into 15 source files with realistic mess (UTC vs local time, typos, blank serials, retired tags, mixed units) | Done | 14 realism checks; `answer_key.json` computed from the world |
| 3 Instance KG | pyoxigraph store, 109,591 triples, 11,508 nodes; identity resolution with methods, confidence, provenance graph, review queue | Done | links recall 0.9995, precision 1.000 (gate 0.95 / 0.98); SHACL conforms; 3 orphan historian tags in review queue |
| 4b System simulators | PI Web API, OPC UA gateway, CMS, SAP PM OData, OSDU, PLM, MES, QMS and production planning as local REST services; read-only agent credential; writes only with a release token and named approver; `HttpSource` and `FileSource` are interchangeable | Done | Same answers over HTTP and from files; 10 of 10 gold cases pass through the simulators; `python -m factory_to_field.demo` runs the whole loop |
| 4 Agents | 7 tool servers (also as MCP), orchestrator with deterministic playbooks, optional model planner, draft store with named-role approval, OT-write refusal, evidence verifier, case viewer | Done | 10 of 10 gold cases, 57 of 57 checks |

Tests: 33 in `factory_to_field/tests` (world 5, KG 9, agents 13, simulators 5 plus the gold run through them); a separate CI job runs ruff, the ontology freshness check, pytest and the gold scorer.

## Gates (as built)

| Gate | Meaning | Status |
|---|---|---|
| G1 | Ontology generates and answers its competency questions | Passed |
| G2 | Simulated world passes realism checks and has an answer key | Passed |
| G3 | Identity resolution recall >= 0.95 at precision >= 0.98, SHACL conforms | Passed (0.9995 / 1.000) |
| G4 | Agents pass the gold cases with every citation verified; OT read-only; drafts only | Passed (10/10) |
| G5 | Pilot readiness: connectors to real systems, human review workflow in production, security review, evaluation on real cases | Open |

## What the gold cases prove

CASE-1042 (refinery bearing alarm), CASE-2077 (ESP motor temperature), CASE-3001 and 3006 (one root cause across both products, containment sizing 38 pumps / 9 customers and 61 seal sections / 4 operators), CASE-3002 (position versus unit), CASE-3003 (as-of question), CASE-3004 (stuck sensor is a false alarm), CASE-3005 (the string now in A-04 is not from the suspect lot), CASE-3007 (a request to write a set-point is refused and turned into an operator request draft), CASE-3008 (an instruction hidden in a notification is flagged and ignored).

## Findings worth knowing

- Kaplan-Meier medians: 780 days for older builds against 290 days for seals built since 1 Aug 2025 (12 strings, 7 failed, 5 running). Running strings are censored; dropping them would overstate the failure.
- Four engineering changes took the expedited route with the qualification test waived (ECO-24-1147, ECO-25-0112, ECO-25-0389, ECO-26-0057). Two put the suspect lots into service; the other two deserve review.
- Factory press-fit force for bearing lot B-24-117 is about 12 percent below other bearing lots.

## Limits to be honest about

- The planner is playbook-based. It generalises across assets of the same type, not across new problem types. The model planner exists and is tested with a scripted client; it has not been evaluated against a live model.
- Reports are checked for citation and number provenance, not for the correctness of every inference.
- Approvals in the case viewer are simulated in the browser. The draft store enforces roles in code; there is no identity provider.
- The world is simulated from my assumptions about plants and pumps. Passing the gold cases shows the machinery works, not that it will on a real plant.

## Remaining work (towards G5)

1. Real connectors: implement the `Source` interface (`agents/sources.py`) against SAP PM OData, PI Web API, OSDU and PLM/MES; the simulators speak the same dialects and stay as the regression target. There are no real systems today, so this is not needed for the demo.
2. Run the model planner against a live model on the 10 gold cases plus new adversarial cases; track pass rate and cost.
3. Review workflow for the identity-resolution queue with real users; measure reviewer time per link.
4. Identity provider for approvers; audit log persisted outside memory.
5. UNS/MQTT replay (`uns_replay.jsonl` exists) feeding live-style alarms into the agent.
6. Extend to the other manufacturing and oil and gas subdomains the explorer lists, using the same ontology modules.
