# Factory to Field: improvement plan (living file)

Source: "Oil and gas solution: critical review and improvement plan"
(https://claude.ai/artifact/G9kHxBybGHU4cfPZPvHcpu). This file is the working copy.
**Every session: read this first, do the next unchecked item, tick it, add a log line at the bottom, commit.**

Status key: [x] done, [~] partly, [ ] not started, [!] blocked on the owner (see Decisions).

## How to run things

    uv venv /tmp/ftfenv --python 3.11 && uv pip install -p /tmp/ftfenv -r factory_to_field/requirements.txt ruff pytest
    . /tmp/ftfenv/bin/activate
    PYTHONPATH=. python -m pytest factory_to_field -q            # 50+ tests
    PYTHONPATH=. python -m factory_to_field.eval.seeds --seeds 42 1 2 3   # seed sweep (about 1 min per seed)
    PYTHONPATH=. python -m factory_to_field.agents.gold              # ten gold cases on seed 42

## Phase 1: honest evaluation (weeks 1-3)

- [x] 1.1 Seed sweep harness: `eval/seeds.py` builds a fresh world per seed, resolves, scores links, runs the gold cases. Seed 42 is dev, all others held out.
- [x] 1.2 First sweep found the answer key was partly typed in (DIFA count 5, oil rate 640, notification number 300001480). Key is now computed from the generated world.
- [x] 1.3 `tests/test_heldout_seeds.py` (floor: link recall 0.995, precision 0.99, all ten gold cases); CI runs seeds 1 2 3 via FTF_SEEDS.
- [x] 1.4 Checked the resolver (`kg/pipeline.py`): no seed-specific constants, only per-method confidences. Its real coupling is to the generator's noise *types* (serial edit distance 1, blank serial, legacy codes, tag grammar), which 1.5 must vary. Noise rates are now a preset (`world/spec.py NOISE`, `--noise base|dirty`); dirty is 3x. Result: seed 1 dirty recall 0.9977, precision 1.0, gold 10/10, so rate is not the weak spot.
- [x] 1.5b Diagnosed: not serial damage. The pump's SAP installation row was one of the randomly dropped ones (6% in hostile), so it has no position and no state. The expected fleet lists now exclude units whose install was never recorded. xfail removed; hostile seed 1 passes 25/25.
- [~] 1.5 Held-out world (new noise TYPES, not rates; rates done in 1.4). Done: `--noise hostile` adds transposed digits, O/I for 0/1, trailing REV text, lost separators on serials. Resolver fixes: norm_serial handles those, lev counts a swap as one edit, a malformed own-family serial no longer mints a phantom unit. Residual: a transposed serial matching a run-life serial is now fixed (edit distance 1 to a serial in another system); 4 of about 2,900 links remain wrong on hostile seed 1: transposed serials of units that appear in no second system, which cannot be told from a genuinely new unit. Needs a second source (e.g. the ERP shipment list) or a rule that sends unmatched own-family serials to review. Also still to vary: swapped position tags, free-text-only mentions, a different tag grammar. Original scope: a second generator config (different names, tag patterns, ID formats, noise rates) that no code was tuned on. Score once, report as is.
- [~] 1.6 Independent grading: `eval/independent_key.py` re-derives 8 key values (DIFA count, oil rate, rig date, injection note, A-07 current/previous string, days) from the rendered files only; test_world and every swept seed assert agreement. Still to cover: lot exposure counts, fleet states, Kaplan-Meier medians, containment sizing.
- [x] 1.7 `eval/seeds.py` prints and saves held-out mean and worst case (a crashed agent run counts as 10 failed cases). First 8-world base sweep (seeds 11-18): recall mean 0.9993, min 0.9989; precision 1.0; gold 80/80 after the fix below.
- [~] 1.8 More cases: 25 now (10 hand-written + 15 generated per world: 12 as-of-unit cases incl. hand-over days and "no record" gaps, 3 OT-write refusals at different set-points). Target 30+ gold and 15 adversarial: still to template position_vs_unit (any month), lot_suspicion for every ESP well, containment per lot, alarm triage on other pumps, more injection variants.

## Phase 2: prove the agent (weeks 3-6)  [!] needs an API key and budget (Decision 2)

- [ ] 2.1 Run the model planner (not FakeClient) on the gold set; report pass rate, tool calls, cost, refusals.
- [ ] 2.2 Baselines: playbook-only vs model planner vs a plain RAG baseline on the same cases.
- [ ] 2.3 Wire agent tools to read through the `/v/<slug>/` mocks, with per-mock faults (timeouts, paging, 401 refresh, stale data).
- [ ] 2.4 Real public data: attach Volve (production) and CWRU (bearing) files; run one case on each. [!] Decision 3 (hosts were unreachable from the sandbox; owner uploads files).

## Phase 3: choose the buyer and the company line (weeks 4-9)  [!] Decision 1

- [ ] 3.1 Pick the buyer (recommended: pump maker's fleet-quality team).
- [ ] 3.2 Split identity and agents: operator-side and maker-side get separate agents and separate IdP tenants.
- [ ] 3.3 Value case: hours saved per case, escapes caught, containment sizing time. Measured on the sweep, not asserted.
- [ ] 3.4 Fix failure mix in the generator to match field data (ESP: electrical about 60%, seals about 22%; vary pull reasons).

## Phase 4: pilot depth (weeks 9-14)

- [ ] 4.1 Make the world busier (more alarms, more positions) so false-alarm handling is exercised.
- [ ] 4.2 Ontology: external mappings (ISO 14224, CFIHOS, OSDU) for the 36 classes.
- [ ] 4.3 Deepen 5-6 mocks (real auth flows, rate limits, paging quirks); label or retire the 22 renamed copies. [!] Decision 4
- [ ] 4.4 Deployable: Dockerfile, docker compose, one-command demo.
- [ ] 4.5 Repo hygiene: fix the `dim_channel` clash and the 6 duplicate KPI ids in the explorer.
- [ ] 4.6 Second use case. [!] Decision 5 (production deferment or fixed-equipment integrity).

## Decisions waiting on the owner

1. Who is the product for? (recommended: pump maker's fleet-quality team)
2. API key and monthly budget for live model runs (owner earlier said no key in the blog context; confirm for this work).
3. Upload Volve and CWRU files, or drop real-data validation.
4. Which 5-6 mocks to deepen; confirm labelling or retiring the rest.
5. Next use case after pump reliability.

## Findings log (newest first)

- 2026-11-08: With the right graph, hostile seed 1 failed one gold case (CASE-1042 fleet list lost OEM-25-1203). Cause: a dropped SAP installation row, not serial damage; the key was wrong to expect that unit. Fixed (1.5b).
- 2026-11-08: **Correction to the findings below.** The seed sweep's agent runs used the seed-42 knowledge graph for every seed (Agent defaulted to build/kg). So "gold 10/10 on held-out seeds" was seed-42 graph answers scored against other worlds' source files and key; the planted stories are identical across seeds, which hid it. Now: each seed builds its own graph, and Agent/LLMAgent raise if given a non-default world without kg=. Link recall/precision numbers were always per-world and stand. With the right graph: seeds 1-9 all pass 25/25 after two key fixes below.
- 2026-11-08: Generated as-of cases exposed that SAP drops about 2% of installation segments. Refinery pumps have no second source, so the right answer there is "no record" (agent now says so instead of crashing the verifier); ESP strings are recoverable from the run-life file and the agent does recover them.
- 2026-11-08: Hostile serial noise exposed a resolver weakness the base noise never did: damaged own-family serials minted phantom units at confidence 1.0 (67 of about 2,900 links wrong). Fixed except 6 transposition cases.
- 2026-11-07: Seed sweep before the fix: links recall 0.998-0.9995, precision 1.0 on all seeds, but the agent passed 8/10 gold cases on seeds 1-3 (10/10 on seed 42). Causes: answer key held typed-in constants (DIFA count, oil rate, notification number). Fixed in the key and playbook; after the fixes (key computed, DIFA count filtered to the as-of date, CASE-3005 well chosen from the key, injection note number from the world) seeds 42 and 1-7 all score 10/10; link recall 0.9983-0.9998, precision 1.0.

## Session log

- 2026-11-08 (cont.): sweep of seeds 11-18 found a crash on seed 13 (bearing-temp tag with no history -> KeyError 'last_max' in the stuck-sensor playbook); the first summary hid it by skipping crashed worlds. Both fixed; seed 13 added to the CI seeds.

- 2026-11-08 (cont.): 1.6 started: independent key agrees with the generator key on seed 42. Note: the old typed oil rate was 640, the files say 637.8 (it passed only through a 6 bbl/d tolerance).

- 2026-11-08: hostile noise first run: precision 0.9896 (67 wrong links, all phantom units from damaged serials), recall 0.9886. After resolver fixes: seeds 42 and 1 hostile recall 0.998, precision 0.999, gold 10/10. Next: close the 6 residual wrong links, add hostile to the CI sweep, then 1.6.

- 2026-11-07 (session 1, cont.): 1.4 done, noise presets added, `--noise dirty` works in the sweep. Next: 1.5 new noise types (e.g. serial transpositions, OCR confusions O/0 and I/1, swapped position tags, free-text-only mentions), then 1.6.

- 2026-11-07 (session 1 of this plan): added `eval/seeds.py`, made key values computed, wrote this file, ticked 1.1-1.3. Next: 1.4 (resolver tuned to seed 42 noise: recall is 0.998+ on every seed so the tuning looks mild, confirm by reading kg/pipeline.py for constants), then 1.5 held-out world config.
