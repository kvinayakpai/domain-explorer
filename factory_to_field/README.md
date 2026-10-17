# Factory to Field

A synthetic but realistic world of one refinery, one oil field and the pump maker that supplies both, with an ontology, a knowledge graph and an agent layer on top. Everything is simulated; no real data is used.

```
ontology (LinkML) ──► OWL + SHACL + Pydantic + TS
world (seeded simulator) ──► SAP PM · historian · SCADA · P&ID · EDMS · OSDU · MES/ERP/PLM/QMS (+ answer key)
kg (pyoxigraph) ◄── identity resolution with provenance, review queue, SHACL gate
agents ◄── MCP tools (kg · historian · eam · plant · maker · drafts · ot) ──► reports, drafts, audit trail
```

## Run it

```bash
pip install -r factory_to_field/requirements.txt
python -m factory_to_field.ontology.build          # regenerate OWL/SHACL/Pydantic/TS (add --check in CI)
python -m factory_to_field.world.build             # ~10 s, seed 42, writes factory_to_field/build/world
python -m factory_to_field.kg.build                # ~100 s with SHACL; add --skip-shacl for ~15 s
python -m factory_to_field.agents.gold             # 10 gold cases, scored against the answer key
python -m factory_to_field.ui.build_ui             # ui/case_viewer.html (one self-contained page)
python -m pytest -c factory_to_field/pytest.ini factory_to_field/tests
python -m factory_to_field.agents.mcp_servers kg   # any of: kg historian eam plant maker drafts ot
```

## The ideas that matter

- **Position versus unit.** A functional location (P-101A) and the serialised unit installed in it are different things joined by a dated installation. A failure belongs to the unit that was installed *then*. Searching by today's serial misattributes it (gold case CASE-3002).
- **The world has a clock.** Every case carries an `as_of`; tools never return anything newer.
- **Identity resolution is scored.** Links are made by exact key, tag grammar, alias table or fuzzy match, each with a confidence and an evidence string; below 0.90 they go to a review queue. `truth.json` is used only for scoring (gate: recall 0.95, precision 0.98).
- **Agents cannot act, only propose.** OT is read-only (`ot.write_setpoint` always refuses). Writes are drafts for a named approver role; there is no approve tool. Free text from systems is returned as `untrusted` and never changes behaviour (CASE-3008). A verifier checks every citation and every quoted number against the tool-call log.
- **Planner is replaceable.** `agents/agent.py` is a deterministic playbook planner; `agents/llm.py` runs a model over the same tools and is checked by the same verifier (tested with a scripted client).

## Layout

| path | what |
|---|---|
| `ontology/*.yaml` | core, refinery, oilfield, factory, kpi modules; `generated/` is built, do not edit |
| `world/` | simulator: factory, refinery, field, signals, renderers, realism checks, answer key |
| `kg/` | pipeline (resolution), store (SPARQL helpers), SHACL, scoring |
| `queries/` | competency questions cq01-cq11 as SPARQL files |
| `agents/` | core, tools, drafts, agent, playbooks, llm, schema, mcp_servers, verifier, gold |
| `ui/` | case viewer (template + built page) |
| `tests/` | world, KG, agents |
