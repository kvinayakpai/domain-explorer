"""Value case for a refinery reliability team (plan 3.3).

usage: python -m factory_to_field.eval.value [--seeds 1 2 3] [--assumptions file.yaml] [--out report.md]

Two kinds of number, kept apart on purpose:
  MEASURED  - taken from running the agent on held-out simulated worlds: did it get the alarm case right against the
              independent answer key, how many tool calls, how many drafts, did every citation verify, what constraints it surfaced.
  ASSUMED   - how long a person takes today and how many alarms a site has. Nobody measured these; they come from
              eval/value_assumptions.yaml and are printed next to every figure derived from them.
The agent under test is the deterministic playbook agent, so wall time says nothing about a model-driven planner.
"""
from __future__ import annotations

import argparse
import tempfile
import time
from pathlib import Path

import yaml

from ..world.build import build

HERE = Path(__file__).resolve().parent
OUT = HERE.parent / "build" / "eval"


def load_assumptions(path: Path | None) -> dict:
    a = yaml.safe_load((HERE / "value_assumptions.yaml").read_text())
    if path:
        a.update(yaml.safe_load(Path(path).read_text()))
    return a


def measure_seed(seed: int) -> dict:
    import json

    from ..agents import gold
    from ..agents.agent import Agent
    from ..agents.sources import make_source
    from ..agents.tools import STORE
    from ..agents.verifier import verify
    from ..kg.build import build_kg
    from ..kg.store import KG
    out: dict = {"seed": seed}
    with tempfile.TemporaryDirectory() as td:
        wd = Path(td) / "world"
        build(wd, seed)
        build_kg(wd, Path(td) / "kg", skip_shacl=True)
        kg = KG(Path(td) / "kg" / "store", read_only=True)
        agent = Agent(kg=kg, world=wd, src=make_source(wd, None))
        key = json.loads((wd / "answer_key.json").read_text())
        for case_id, label in (("CASE-1042", "real_alarm"), ("CASE-3004", "false_alarm")):
            g = next(x for x in gold.GOLD if x.case.id == case_id)
            st = {"drafts_before": len(STORE.items)}
            t = time.time()
            rep, s = agent.run(g.case)
            secs = time.time() - t
            checks = g.checks(rep, s, key, st)
            problems = verify(rep, s)
            out[label] = {"correct": all(checks.values()) and not problems, "seconds": round(secs, 2), "tool_calls": rep.tool_calls,
                          "drafts": len(rep.drafts), "citations_verify": not problems,
                          "constraints_surfaced": [k for k in ("open_work_on_position", "bearing_stock", "next_window", "spare_unit") if rep.answer.get(k) is not None],
                          "false_alarm_called": rep.answer.get("false_alarm") is True, "machinery_action": rep.answer.get("machinery_action")}
    return out


def report(rows: list[dict], A: dict) -> str:
    n = len(rows)
    real = [r["real_alarm"] for r in rows]
    fa = [r["false_alarm"] for r in rows]
    ok_real, ok_fa = sum(x["correct"] for x in real), sum(x["correct"] for x in fa)
    calls = sum(x["tool_calls"] for x in real) / n
    cons = sum(len(x["constraints_surfaced"]) for x in real) / n
    human_real = A["human_minutes_triage_real_alarm"] + A["human_minutes_draft_work_order"]
    agent_real = A["reviewer_minutes_per_agent_draft"]
    human_fa, agent_fa = A["human_minutes_screen_false_alarm"], A["reviewer_minutes_per_agent_draft"]
    m = A["vibration_alarms_per_month"]
    f = A["false_alarm_share"]
    hours_now = (m * (1 - f) * human_real + m * f * human_fa) / 60
    hours_agent = (m * (1 - f) * agent_real + m * f * agent_fa) / 60
    saved = hours_now - hours_agent
    L = [f"# Value case: refinery reliability team ({n} held-out simulated worlds, seeds {', '.join(str(r['seed']) for r in rows)})", "",
         "## Measured on the simulated worlds",
         f"- Real bearing alarm (CASE-1042 pattern): the agent's report matched the independent answer key in **{ok_real} of {n}** worlds, every citation and quoted number verified in {sum(x['citations_verify'] for x in real)} of {n}.",
         f"- Average **{calls:.0f} tool calls** per real alarm; {sum(x['drafts'] for x in real) / n:.0f} drafts proposed (SAP notification, bearing stock transfer, QMS warranty claim); each waits for a named approver.",
         f"- Constraints surfaced per real alarm (open work, bearing stock, next window, spare unit): {cons:.1f} of 4, each checked against the key.",
         f"- False alarm (stuck vibration transmitter, CASE-3004 pattern): called a false alarm and proposed an instrument check rather than a pump repair in **{sum(x['false_alarm_called'] and not x['machinery_action'] for x in fa)} of {n}** worlds; fully correct in {ok_fa} of {n}.",
         "- Limits: the agent is a deterministic playbook planner (its wall time, about "
         f"{sum(x['seconds'] for x in real) / n:.1f} s here, says nothing about a model-driven one). The worlds are simulated, so these show the pipeline and answer key are sound, not that a real plant's data is this clean.", "",
         "## Assumed (NOT measured; edit eval/value_assumptions.yaml or pass --assumptions)"]
    L += [f"- {k}: {v}" for k, v in A.items()]
    L += ["", "## What those assumptions imply (arithmetic only; as good as the assumptions)",
          f"- Per real alarm: {human_real} min by hand today (assumed {A['human_minutes_triage_real_alarm']} triage + {A['human_minutes_draft_work_order']} drafting) against {agent_real} min to review the agent's draft (assumed).",
          f"- Per false alarm: {human_fa} min today (assumed) against {agent_fa} min review (assumed).",
          f"- At {m} alarms a month with {f:.0%} false (both assumed): {hours_now:.0f} engineer hours a month today against {hours_agent:.0f} with agent drafts, about **{saved:.0f} hours a month**, roughly ${saved * A['loaded_cost_per_hour']:,.0f} at the assumed ${A['loaded_cost_per_hour']}/hour.",
          "- The saving is only real if the reviewer really takes the assumed review time and the agent's drafts are right on a real plant. A pilot on one unit's alarm log is how to replace the assumptions with measurements."]
    return "\n".join(L) + "\n"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, nargs="*", default=[1, 2, 3])
    ap.add_argument("--assumptions", type=Path)
    ap.add_argument("--out", type=Path, default=OUT / "value-case.md")
    a = ap.parse_args()
    rows = [measure_seed(s) for s in a.seeds]
    txt = report(rows, load_assumptions(a.assumptions))
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(txt)
    print(txt)


if __name__ == "__main__":
    main()
