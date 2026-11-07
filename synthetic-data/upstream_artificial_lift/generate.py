"""Upstream production with artificial lift: ESP and gas-lift wells in one field.

Exported from the Factory to Field simulated world (see ``synthetic-data/ftf_world.py``), not
generated with Faker. Field A has 22 producing wells (12 on electrical submersible pumps,
10 on gas lift). The tables follow what an operator's well master data, SCADA historian,
production accounting, SAP PM and the ESP maker's records would hold:

    well, esp_string, esp_component, esp_run, failure_event, difa_report, signal,
    signal_daily, production_daily, workover_rig

Run life belongs to the ESP string, not to the well: a well keeps its history while strings
come and go. Runs still in the hole are censored (state = running), which a run-life
estimate has to respect. DIFA reports follow API RP 11S1. All data is synthetic.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

SYNTH_ROOT = Path(__file__).resolve().parents[1]
if str(SYNTH_ROOT) not in sys.path:
    sys.path.insert(0, str(SYNTH_ROOT))

from common import write_table  # noqa: E402
from ftf_world import as_of, daily_frame, history_days, load_world, strip  # noqa: E402

SUBDOMAIN = "upstream_artificial_lift"
FIELD = "site:FA"


def generate(seed: int = 42) -> dict[str, pd.DataFrame]:
    w = load_world(seed)
    days = history_days()

    wells = {pid: p for pid, p in w.positions.items() if p["kind"] == "well" and p["site"] == FIELD}
    lift_pos = {p["parent"]: p for p in w.positions.values() if p["kind"] == "esp_position" and p["site"] == FIELD}
    well = pd.DataFrame([
        {
            "well_id": p["tag"],
            "functional_location_id": pid,
            "floc_code": p["floc"],
            "field_id": FIELD,
            "pad": p["pad"],
            "lift_method": p["lift"],
            "esp_position_id": lift_pos[pid]["id"] if pid in lift_pos else None,
            "esp_setting_depth_m": lift_pos[pid].get("setting_depth_m") if pid in lift_pos else None,
        }
        for pid, p in sorted(wells.items())
    ])

    run_units = {r["unit"] for r in w.runs}
    strings = [u for u in w.units.values() if u["kind"] == "esp_string" and u["id"] in run_units]
    esp_string = pd.DataFrame([
        {
            "esp_string_id": u["serial"],
            "model": u["model"],
            "maker_id": strip(u["maker"]),
            "built_on": u["built"],
            "shipped_on": u["shipped"],
        }
        for u in sorted(strings, key=lambda u: u["serial"])
    ])
    string_ids = {u["id"] for u in strings}
    components = [u for u in w.units.values() if u.get("parent") in string_ids]
    esp_component = pd.DataFrame([
        {
            "component_id": c["serial"],
            "esp_string_id": strip(c["parent"]),
            "component_kind": c["kind"].removeprefix("esp_"),
            "built_on": c["built"],
            "material_lots": ";".join(c["lots"]),
        }
        for c in sorted(components, key=lambda c: (c["parent"], c["kind"]))
    ])

    today = as_of()
    esp_run = pd.DataFrame([
        {
            "run_id": r["id"],
            "well_id": r["well"],
            "esp_string_id": strip(r["unit"]),
            "run_start": r["start"],
            "run_end": r["end"],
            "run_days": r["days"] if r["end"] is not None else (today - r["start"]).days,
            "run_state": r["state"],
            "censored": r["state"] == "running",
            "pull_reason": r["pull_reason"],
            "seal_built_since_aug_2025": bool(r["new_seal"]),
        }
        for r in sorted(w.runs, key=lambda r: (r["well"], r["start"]))
    ])

    failure_event = pd.DataFrame([
        {
            "failure_event_id": f["id"],
            "functional_location_id": f["pos"],
            "esp_string_id": strip(f["unit"]),
            "failed_on": f["on"],
            "iso14224_failure_mode": f["mode"],
            "description": f["desc"],
            "repair_days": f["repair_days"],
        }
        for f in sorted(w.failures, key=lambda f: f["on"]) if f["pos"].startswith("pos:FA")
    ])

    difa_report = pd.DataFrame([
        {
            "difa_report_id": d["id"],
            "well_id": d["well"],
            "esp_string_id": strip(d["unit"]),
            "reported_on": d["on"],
            "standard": d["standard"],
            "finding": d["finding"],
        }
        for d in sorted(w.difa, key=lambda d: d["on"])
    ])

    sigs = {sid: s for sid, s in w.signals.items() if s["site"] == FIELD}
    signal = pd.DataFrame([
        {
            "signal_id": sid,
            "tag": s["tag"],
            "functional_location_id": s["pos"],
            "quantity": s["quantity"],
            "eng_unit": s["eng_unit"],
            "alarm_high": s["alarm_high"],
            "source_system": s["system"],
            "sample_seconds": s["sample_s"],
            "description": s["desc"],
        }
        for sid, s in sorted(sigs.items())
    ])
    signal_daily = daily_frame(w, sorted(sigs), days)

    prod_frames = []
    for key, arrays in sorted(w.daily.items()):
        if not key.startswith("prod:"):
            continue
        frame = pd.DataFrame({"well_id": key.split(":", 1)[1], "day": days})
        for phase, values in arrays.items():
            frame[f"{phase}_bbl_d" if phase in ("oil", "water") else f"{phase}_rate"] = values.round(2)
        prod_frames.append(frame)
    production_daily = pd.concat(prod_frames, ignore_index=True)

    workover_rig = pd.DataFrame([
        {"rig_id": r["rig"], "field_id": r["site"], "free_from": r["free_from"], "note": r["note"]}
        for r in w.rigs
    ])

    tables = {
        "well": well,
        "esp_string": esp_string,
        "esp_component": esp_component,
        "esp_run": esp_run,
        "failure_event": failure_event,
        "difa_report": difa_report,
        "signal": signal,
        "signal_daily": signal_daily,
        "production_daily": production_daily,
        "workover_rig": workover_rig,
    }
    for name, df in tables.items():
        write_table(SUBDOMAIN, name, df)
    return tables


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--seed", type=int, default=42)
    args = p.parse_args()
    for name, df in generate(args.seed).items():
        print(f"  {SUBDOMAIN}.{name}: {len(df):,} rows")


if __name__ == "__main__":
    main()
