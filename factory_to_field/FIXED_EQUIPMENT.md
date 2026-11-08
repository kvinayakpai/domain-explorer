# Second use case: fixed-equipment integrity (design note)

Status: design only (plan 4.6). Nothing here is built. Standards details are from working knowledge (API 510/570/571/580/581, API 653) and need review by an inspection engineer before anyone relies on them.

## Why this one
Chosen by the owner on 2026-11-08 as the second use case for the refinery reliability team. It reuses the idea the whole project hangs on, in a harder form: history belongs to a measurement *location* on a *component*, and components get replaced, so a naive search by today's equipment number mixes old and new metal.

## The question the agent answers
"What is the remaining life of line 10-P-101-SUCTION-A at its worst thickness location, when must it next be inspected, and has anything changed since the last readings?"

Core arithmetic (to be checked by the inspection engineer, then fixed in the independent key, not in the agent):
- corrosion rate (short-term) = (previous thickness - latest thickness) / years between readings; long-term uses first reading or baseline after the last repair or replacement
- remaining life = (latest thickness - required minimum thickness) / governing corrosion rate
- next inspection due = the smaller of half the remaining life and the code maximum interval

## Ontology slice (new module `fixed_equipment.yaml`, ~8 classes)
- `Circuit` (corrosion loop: same service, same damage mechanisms) - groups components
- `PressureComponent` (vessel shell, head, pipe spool, fitting): a serialised physical thing, like PhysicalEquipment; has material, design and minimum required thickness
- `ThicknessLocation` (condition monitoring location, CML): a position on a component; history stays with the location unless the component is replaced
- `ThicknessReading`: value, unit (mm or inch), date, method (UT, RT), gauge id, inspector
- `DamageMechanism`: thinning, cracking, etc., attached to a circuit (API 571 vocabulary)
- `InspectionPlan`/`InspectionRecord`: planned and done, with next due date
- `Repair`/`Replacement`: resets the baseline for the locations it touches
- `FitnessForServiceAssessment` (optional, later)
Reuses `Installation`, `Document`, `Notification`, `Case`, `Draft` and the identity-resolution machinery unchanged.

## World generator additions (`world/gen_fixed.py`)
- ~6 circuits, ~40 components, ~250 CMLs, 6 to 12 readings per CML over 12 years, drawn from per-circuit corrosion rates with noise
- Source files, with the same kind of mess as today's: an inspection database export (readings keyed by CML id), SAP PM inspection plans keyed by equipment number, an EDMS inspection-report index, P&ID line numbers in free text
- Planted traps (each with an answer key computed from the world, never typed in):
  1. a replaced spool: readings before and after belong to different metal; the corrosion rate must not span the replacement
  2. a thickness that goes up (gauge or location error): must not produce a negative rate; the agent flags it and asks for a re-measure
  3. mixed units (inch vs mm) across two inspection campaigns
  4. a CML relabelled after a re-survey (alias table, like the tag renames)
  5. a circuit with a single reading: remaining life cannot be computed, and the agent must say so
  6. an inspection overdue on the date of the case, as-of honoured
  7. prompt injection in an inspection report's free text; and the same OT/process-write refusal as today
- Held-out seeds and noise presets work as for the pump world; the independent key re-derives rates and due dates straight from the rendered files

## Playbooks and tools
- `inspect.history(cml)`, `inspect.rate(cml, basis)`, `inspect.remaining_life(component)`, `inspect.next_due(circuit)`, reusing `kg.unit_at(position, as_of)`-style as-of lookups for component replacements
- Playbooks: remaining life at the worst CML; overdue inspections in a circuit; "did the repair reset the baseline"; anomaly check on a reading
- Drafts only: an inspection work order and a request to re-measure, for a named inspection engineer role; no writes to any system

## Gold cases (target ~25 per world, like today)
Mix of: one per trap above; remaining life per circuit (generated from the key); overdue list as of a date; the OT-write refusal; unit-conversion case; a negative control where nothing is wrong.

## Effort and order
1. Ontology module and SHACL shapes (small). 2. Generator with traps and the independent key (the largest piece; the key must come first). 3. Resolver rules for CML aliases. 4. Tools and playbooks. 5. Gold, held-out seeds, hostile noise. Reuse of the pump-world machinery should keep this to a fraction of the first build, but the generator and key are real work.

## Honest limits
Simulated data only; the agent is the deterministic planner; formulae and intervals above must be confirmed by an inspection engineer; this is decision support for a qualified person, never an integrity sign-off.
