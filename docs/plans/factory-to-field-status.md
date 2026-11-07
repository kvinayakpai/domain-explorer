# Factory to Field: plan and status (17 Oct 2026; updated 7 Nov 2026)

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
| G5 | Pilot readiness: connectors to real systems, human review workflow in production, security review, evaluation on real cases | Open; everything that does not need real systems is built (7 Nov 2026, below) |

## What the gold cases prove

CASE-1042 (refinery bearing alarm), CASE-2077 (ESP motor temperature), CASE-3001 and 3006 (one root cause across both products, containment sizing 38 pumps / 9 customers and 61 seal sections / 4 operators), CASE-3002 (position versus unit), CASE-3003 (as-of question), CASE-3004 (stuck sensor is a false alarm), CASE-3005 (the string now in A-04 is not from the suspect lot), CASE-3007 (a request to write a set-point is refused and turned into an operator request draft), CASE-3008 (an instruction hidden in a notification is flagged and ignored).

## Findings worth knowing

- Kaplan-Meier medians: 780 days for older builds against 290 days for seals built since 1 Aug 2025 (12 strings, 7 failed, 5 running). Running strings are censored; dropping them would overstate the failure.
- Four engineering changes took the expedited route with the qualification test waived (ECO-24-1147, ECO-25-0112, ECO-25-0389, ECO-26-0057). Two put the suspect lots into service; the other two deserve review.
- Factory press-fit force for bearing lot B-24-117 is about 12 percent below other bearing lots.

## Limits to be honest about

- The planner is playbook-based. It generalises across assets of the same type, not across new problem types. The model planner exists and is tested with a scripted client; it has not been evaluated against a live model.
- Reports are checked for citation and number provenance, not for the correctness of every inference.
- Approvals in the static case viewer are simulated in the browser. The live console signs people in through a simulated identity provider; a pilot replaces it with the company's.
- The world is simulated from my assumptions about plants and pumps. Passing the gold cases shows the machinery works, not that it will on a real plant.

## Done towards G5 (7 Nov 2026)

| Item | What was built | Evidence |
|---|---|---|
| Identity for approvers | `pilot/idp.py` signs RS256 tokens for named people and the agent's client; console approvals and releases use them; the simulators verify the token and the role per write route and refuse the static release token | `tests/test_pilot.py`; console smoke run: a quality engineer's approval of a SAP notification is refused, the maintenance planner's goes through and is recorded with her login |
| Persisted audit log | `pilot/audit.py`, hash-chained JSON lines that survive restarts | tampering with one line is detected at that line |
| Review workflow | `pilot/review.py` + console panel: link or dismiss each queue item as a data steward; decisions feed the KG build | queue 3 -> 0 after decisions, precision stays >= 0.98 |
| UNS/MQTT replay | `pilot/uns.py`: amqtt broker, paho publisher, alarm listener opening agent cases | both replayed alarms (10P101A.VIB_DE 4.591 > 4.5; A07_MTR_T 135.05 > 135) open cases with the right diagnosis |
| Connector hardening | `HttpSource`: OAuth2 refresh, retries with back-off, OData and PI paging, SAP CSRF, OSDU partition; `pilot/connectors.py` config | contract tests against the simulators' new behaviour |
| Model-planner evaluation | `agents/eval_live.py`: 10 gold + 5 adversarial cases scored by facts, evidence and guardrails | playbook planner 15/15; the model run waits for an API key |
| Vibration-skew check | root cause: the check moved from pooled to per-pump skew without recalibrating, over a symmetric drift; drift now multiplicative, threshold back to 0.3 | per-pump skew 0.42; answer key unchanged |

## Remaining work (towards G5)

1. Real connectors: point `pilot/connectors.example.yaml` at a plant's SAP PM, PI Web API, OSDU and PLM/MES endpoints with real client credentials; the simulators stay as the regression target. Blocked until there is a real system to connect to.
2. Run `agents/eval_live.py --planner model` with an API key; track pass rate, tokens and cost per case.
3. Put the review workflow in front of real data stewards and measure time per decision on real queues.
4. Swap the simulated identity provider for the company's (authorization code with PKCE); keep the audit log on durable, access-controlled storage.
5. Feed the alarm listener from the plant's real UNS broker (Sparkplug B), with alarm limits from the alarm management database.
6. Extend to the other manufacturing and oil and gas subdomains, using the same ontology modules (refinery_operations and upstream_artificial_lift in the explorer now run on this world's data).
