# Factory to Field: improvement plan (living file)

Source: "Oil and gas solution: critical review and improvement plan"
(https://claude.ai/artifact/G9kHxBybGHU4cfPZPvHcpu). This file is the working copy.
**Every session: read this first, do the next unchecked item, tick it, add a log line at the bottom, commit.**

Status key: [x] done, [~] partly, [ ] not started, [-] dropped by decision, [!] blocked on the owner.

## How to run things

    uv venv /tmp/ftfenv --python 3.11 && uv pip install -p /tmp/ftfenv -r factory_to_field/requirements.txt ruff pytest
    . /tmp/ftfenv/bin/activate
    PYTHONPATH=. python -m pytest factory_to_field -q            # 50+ tests
    PYTHONPATH=. python -m factory_to_field.eval.seeds --seeds 42 1 2 3   # seed sweep (about 1 min per seed)
    PYTHONPATH=. python -m factory_to_field.agents.gold              # ten gold cases on seed 42

## Phase 1: honest evaluation (weeks 1-3)  COMPLETE 2026-11-08

- [x] 1.1 Seed sweep harness: `eval/seeds.py` builds a fresh world per seed, resolves, scores links, runs the gold cases. Seed 42 is dev, all others held out.
- [x] 1.2 First sweep found the answer key was partly typed in (DIFA count 5, oil rate 640, notification number 300001480). Key is now computed from the generated world.
- [x] 1.3 `tests/test_heldout_seeds.py` (floor: link recall 0.995, precision 0.99, all ten gold cases); CI runs seeds 1 2 3 via FTF_SEEDS.
- [x] 1.4 Checked the resolver (`kg/pipeline.py`): no seed-specific constants, only per-method confidences. Its real coupling is to the generator's noise *types* (serial edit distance 1, blank serial, legacy codes, tag grammar), which 1.5 must vary. Noise rates are now a preset (`world/spec.py NOISE`, `--noise base|dirty`); dirty is 3x. Result: seed 1 dirty recall 0.9977, precision 1.0, gold 10/10, so rate is not the weak spot.
- [x] 1.5b Diagnosed: not serial damage. The pump's SAP installation row was one of the randomly dropped ones (6% in hostile), so it has no position and no state. The expected fleet lists now exclude units whose install was never recorded. xfail removed; hostile seed 1 passes 25/25.
- [x] 1.5 Held-out world with new noise TYPES (`--noise hostile`): transposed digits, O/I for 0/1, trailing label text, lost separators on serials; lower-case and hyphen tag grammar; 4% of pump notifications keyed to the sister pump; 15% of notifications with the equipment number blank and the unit named only in the long text. Resolver fixes: serial normalisation, transposition-aware edit distance, no phantom unit from a damaged own-family serial, one-edit match against run-life serials, case/separator-insensitive tag grammar, text and unit-installation cross-check for mis-keyed locations, serial extraction from long text. Hostile seed 1: recall 0.9986, precision 0.9994, all gold cases pass. Known residual: about 4 of 2,900 links (transposed serials of units that appear in no second system) cannot be told from a new unit; needs another source or a review rule.
- [x] 1.6 Independent grading: `eval/independent_key.py` re-derives from the rendered files alone: DIFA count, A-07 oil rate, rig date, injection note, A-07 strings and days (8 values), lot exposure and customers for the generated lot cases, monthly failure counts by position, and the two containment lots' pump/section/customer counts. Run on every base-noise seed in the sweep and in test_world. Not independently re-derived (still from the generator): Kaplan-Meier medians, new-string counts, fleet states (planted constants by design), and the hostile-world keys (noise damages the files they would be read from).
- [x] 1.7 `eval/seeds.py` prints and saves held-out mean and worst case (a crashed agent run counts as 10 failed cases). First 8-world base sweep (seeds 11-18): recall mean 0.9993, min 0.9989; precision 1.0; gold 80/80 after the fix below.
- [x] 1.8 About 59 gold cases per world: 10 hand-written plus about 43 generated from each world (12 as-of-unit incl. hand-over days and no-record gaps, 3 OT-write refusals, one lot-exposure case per ESP well, 6 failures-by-position-and-month incl. quiet months, 6 lot exposure and customers for random lots, 4 notification summaries with nothing to flag as negative controls). Seeds 1-6: 314/314. Short of the 30-per-family target only in adversarial variety (3 injection/OT families); more adversarial families belong with Phase 2 if a model planner is ever run.

## Phase 2: prove the agent offline (weeks 3-6)  (no API key: live model runs dropped)

- [-] 2.1 DROPPED (no API key): live model planner runs. Keep the LLMAgent wired and tested with FakeClient; say in the README that no live-model result exists.
- [x] 2.2 Offline baseline: `agents/baseline.py` (NaiveAgent: answers from the current state of each record, same tools and graph, no time logic) and `eval/baseline.py`. Seeds 1-4, generated cases: unit on a past date 16/48 (33%) vs playbook agent 48/48; failures at a position in a month 15/24 (62%) vs 24/24; lot exposure of the string now running 20/46 (44%) vs 46/46. Read with care: the baseline is a strawman I wrote, not a competitor; its 62% on failures is inflated because two of six cases per world ask about months before any history, where 'nothing' is right by luck; the as-of number (right only when the unit has not changed since the date) is the honest measure of what time-aware lookup buys on this data.
- [ ] 2.3 (optional) Wire agent tools to read through the six `/v/<slug>/` mocks, exercising session refresh and vendor paging.
- [-] 2.4 DROPPED (Decision 3): real public data validation.

## Phase 3: build for the refinery reliability team (weeks 4-9)

- [x] 3.1 Buyer chosen: refinery reliability team.
- [ ] 3.2 Split identity and agents: the operator agent is primary and sees only operator systems; the maker view becomes a separate, clearly secondary agent and IdP tenant (containment sizing needs maker data the operator would not hold).
- [ ] 3.3 Value case for a refinery reliability team: time to a reviewed work-order draft per alarm, false alarms screened out, spares/window conflicts caught. Measured on the sweep, not asserted. The human baseline (how long a person takes today) is not measured: use clearly labelled ASSUMPTIONS (owner's instruction 2026-11-08), state them next to every number, and make them parameters so the owner can overwrite them.
- [x] 3.4 Failure mix: ordinary ESP failures are now drawn from a weighted list (12 electrical, 4 pump wear, 2 mechanical, 4 gas/overheating of 22) and their pulls carry that cause instead of a blanket "motor failure". The planted new-seal strings keep the surface label on purpose (that is the story: seal-ingress pulls recorded as motor failure). Result on seeds 42/1/2: electrical 32-44%, 'motor failure' 32% (the story strings), rest spread. Seals are still over-represented by design (7 of 25 failed strings); say so in any write-up.

## Phase 4: pilot depth (weeks 9-14)

- [x] 4.1 Busier world: 16 process upsets on ordinary pumps per world (2-4 days at 2.1-2.8x vibration, no bearing signature, no repair), drawn from their own generator so nothing else shifted. Refinery alarms on seed 42 went from 21 to 30 (33 with field alarms). New gold family: alarm history by tag and window (3 windows with alarms, 3 quiet), re-derived independently from the historian alarm table. Still thin by comparison with a real plant (about 0.03 alarms per pump-month); realism of alarm floods, nuisance alarms and shelving is not modelled.
- [ ] 4.2 Ontology: external mappings (ISO 14224, CFIHOS, OSDU) for the 36 classes.
- [x] 4.3 Mocks cut from 41 to 6 deep ones (pi_af, deltav, maximo, system1, ge_apm, esp_difa): vendor paging (Links.Next, nextCursor, OData nextLink, OSLC), session expiry for deltav/system1/ge_apm; 35 renamed copies deleted and listed in `vendors.RETIRED`. Still no consumer in the agents: they read through the file source and the original simulators (see 2.3, now optional).
- [x] 4.4 Deployable: Dockerfile, docker compose, one-command demo. Done: `Dockerfile`, `docker-compose.yml`, root `.dockerignore`, `live_app --host`. NOT built: no Docker daemon in this sandbox; the same commands and the `--host 0.0.0.0` console were run directly (HTTP 200).
- [x] 4.5 Repo hygiene: dbt duplicate model names fixed by subdomain suffix (`dim_channel_hotel`, `dim_location_dp`, `fct_allocations_cm`, `fct_forecast_accuracy_dp`; no `.sql` name repeats, no dangling `ref()`); 6 duplicate KPI ids removed from `data/kpis/master.yaml` (kept the richer entries, `tpm.kpi.promo_roi` lists both subdomains). Not run: full `dbt parse` (dbt_utils cannot be installed here, hub.getdbt.com blocked), so checked by script.
- [ ] 4.6 Second use case: fixed-equipment integrity (corrosion rates, inspection records, remaining life for vessels and piping). Needs its own ontology slice, world generator, playbooks and gold cases; start with a design note.

## Decisions (answered 2026-11-08)

1. Buyer: **refinery reliability team** (operator side). Pump-maker (OEM) features stay as the secondary, containment story; they are not the lead.
2. API key: **none**. No live model runs. Phase 2 is reduced to offline work (see below).
3. Real public data (Volve, CWRU): **dropped**. Synthetic worlds only; say so plainly in any write-up.
4. Mocks: **deepen 5-6, retire the rest** (delete the renamed copies).
5. Second use case: **fixed-equipment integrity** (corrosion and inspection records for vessels and pipes).

## Findings log (newest first)

- 2026-11-08: With the right graph, hostile seed 1 failed one gold case (CASE-1042 fleet list lost OEM-25-1203). Cause: a dropped SAP installation row, not serial damage; the key was wrong to expect that unit. Fixed (1.5b).
- 2026-11-08: **Correction to the findings below.** The seed sweep's agent runs used the seed-42 knowledge graph for every seed (Agent defaulted to build/kg). So "gold 10/10 on held-out seeds" was seed-42 graph answers scored against other worlds' source files and key; the planted stories are identical across seeds, which hid it. Now: each seed builds its own graph, and Agent/LLMAgent raise if given a non-default world without kg=. Link recall/precision numbers were always per-world and stand. With the right graph: seeds 1-9 all pass 25/25 after two key fixes below.
- 2026-11-08: Generated as-of cases exposed that SAP drops about 2% of installation segments. Refinery pumps have no second source, so the right answer there is "no record" (agent now says so instead of crashing the verifier); ESP strings are recoverable from the run-life file and the agent does recover them.
- 2026-11-08: Hostile serial noise exposed a resolver weakness the base noise never did: damaged own-family serials minted phantom units at confidence 1.0 (67 of about 2,900 links wrong). Fixed except 6 transposition cases.
- 2026-11-07: Seed sweep before the fix: links recall 0.998-0.9995, precision 1.0 on all seeds, but the agent passed 8/10 gold cases on seeds 1-3 (10/10 on seed 42). Causes: answer key held typed-in constants (DIFA count, oil rate, notification number). Fixed in the key and playbook; after the fixes (key computed, DIFA count filtered to the as-of date, CASE-3005 well chosen from the key, injection note number from the world) seeds 42 and 1-7 all score 10/10; link recall 0.9983-0.9998, precision 1.0.

## Session log

- 2026-11-08: PR #13 merged. 4.4 done (Docker, untested build). Next: 3.2 split operator/maker agents and IdP tenants.

- 2026-11-08: 4.5 done (see item). Next: 4.4 Docker one-command demo.

- 2026-11-08 (cont.): 2.2 done (numbers in the item). CI on PR 13: the Python job failed once on a GitHub 504 during setup (not a test failure); re-run could not be triggered from the sandbox (403), so a new push retriggers it.

- 2026-11-08 (Phase 1 complete): 1.5, 1.6, 1.8 closed. Remaining plan: 2.2 (offline naive baseline), 2.3 (optional mock wiring), 3.2-3.4, 4.1, 4.2, 4.4-4.6.

- 2026-11-08 (cont.): owner answered the five decisions (see Decisions). Consequences: Phase 2 is offline-only, real-data validation dropped, buyer is the refinery reliability team, mocks to be cut to 5-6 deep ones, second use case is fixed-equipment integrity. Next: finish Phase 1 leftovers (1.5 free-text, 1.6, 1.8), then 2.2 (naive baseline) and 4.3 (mock cut).

- 2026-11-08 (cont.): 1.5 swapped locations done; 1.8 at about 37 cases/world, all pass on seeds 1-5. Caution: the agent under test is the deterministic playbook agent, so high pass rates here show the data pipeline and key are sound, not that a model planner works; that is Phase 2 and needs the API key (Decision 2).

- 2026-11-08 (cont.): sweep of seeds 11-18 found a crash on seed 13 (bearing-temp tag with no history -> KeyError 'last_max' in the stuck-sensor playbook); the first summary hid it by skipping crashed worlds. Both fixed; seed 13 added to the CI seeds.

- 2026-11-08 (cont.): 1.6 started: independent key agrees with the generator key on seed 42. Note: the old typed oil rate was 640, the files say 637.8 (it passed only through a 6 bbl/d tolerance).

- 2026-11-08: hostile noise first run: precision 0.9896 (67 wrong links, all phantom units from damaged serials), recall 0.9886. After resolver fixes: seeds 42 and 1 hostile recall 0.998, precision 0.999, gold 10/10. Next: close the 6 residual wrong links, add hostile to the CI sweep, then 1.6.

- 2026-11-07 (session 1, cont.): 1.4 done, noise presets added, `--noise dirty` works in the sweep. Next: 1.5 new noise types (e.g. serial transpositions, OCR confusions O/0 and I/1, swapped position tags, free-text-only mentions), then 1.6.

- 2026-11-07 (session 1 of this plan): added `eval/seeds.py`, made key values computed, wrote this file, ticked 1.1-1.3. Next: 1.4 (resolver tuned to seed 42 noise: recall is 0.998+ on every seed so the tuning looks mild, confirm by reading kg/pipeline.py for constants), then 1.5 held-out world config.
