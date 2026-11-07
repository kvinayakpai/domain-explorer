"""Refinery operations: rotating-equipment reliability tables for three refineries.

Exported from the Factory to Field simulated world (see ``synthetic-data/ftf_world.py``), not
generated with Faker. The tables follow what a refinery's SAP PM, PI historian and the pump
maker's genealogy records would hold for its API 610 pumps:

    site, functional_location, equipment, installation, failure_event, notification,
    work_order, signal, signal_daily, material_lot, engineering_change, component_genealogy

Positions (functional locations) and physical units (equipment) are separate, with dated
installations between them, so a failure belongs to the unit that failed and the position
where it happened. Failure modes use ISO 14224 codes. All data is synthetic.
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
from ftf_world import daily_frame, history_days, load_world, strip  # noqa: E402

SUBDOMAIN = "refinery_operations"


def _is_refinery(site_id: str | None) -> bool:
    return bool(site_id) and site_id.startswith("site:R")


def generate(seed: int = 42) -> dict[str, pd.DataFrame]:
    w = load_world(seed)

    sites = pd.DataFrame([
        {"site_id": s["id"], "site_name": s["name"], "operator_id": s["operator"], "time_zone": s["tz"]}
        for s in w.sites.values() if s["kind"] == "refinery"
    ])

    positions = {pid: p for pid, p in w.positions.items() if p["kind"] == "pump" and _is_refinery(p["site"])}
    flocs = pd.DataFrame([
        {
            "functional_location_id": pid,
            "floc_code": p["floc"],
            "tag": p["tag"],
            "site_id": p["site"],
            "area": p["area"],
            "process_unit": p["unit_label"],
            "service": p["service"],
            "api_610_type": p["api"],
            "model_required": p["model_req"],
            "rated_flow_m3h": p["rated_m3h"],
            "train_letter": p["letter"],
            "spare_of": p["spare_of"],
            "pid_drawing": p["pid"],
            "pid_revision": p["pid_rev"],
        }
        for pid, p in sorted(positions.items())
    ])

    installs = [i for i in w.installs if i["pos"] in positions]
    unit_ids = sorted({i["unit"] for i in installs})
    equipment = pd.DataFrame([
        {
            "equipment_id": strip(u),
            "equipment_kind": w.units[u]["kind"],
            "model": w.units[u]["model"],
            "maker_id": strip(w.units[u]["maker"]),
            "customer_id": strip(w.units[u]["customer"]),
            "built_on": w.units[u]["built"],
            "shipped_on": w.units[u]["shipped"],
        }
        for u in unit_ids
    ])
    installation = pd.DataFrame([
        {
            "installation_id": i["id"],
            "functional_location_id": i["pos"],
            "equipment_id": strip(i["unit"]),
            "installed_from": i["from"],
            "installed_to": i["to"],
        }
        for i in sorted(installs, key=lambda i: (i["pos"], i["from"]))
    ])

    failures = [f for f in w.failures if f["pos"] in positions]

    def _installation_of(f: dict) -> str | None:
        """The installation of this pump in this position that covers the failure date.

        The world records it only for the scripted failures, so the rest are matched the way an
        analyst would: same unit, same position, installed on the day it failed."""
        if f["inst"]:
            return f["inst"]
        hits = [i for i in installs if i["pos"] == f["pos"] and i["unit"] == f["unit"]
                and i["from"] <= f["on"] and (i["to"] is None or f["on"] <= i["to"])]
        return max(hits, key=lambda i: i["from"])["id"] if hits else None

    failure_event = pd.DataFrame([
        {
            "failure_event_id": f["id"],
            "functional_location_id": f["pos"],
            "equipment_id": strip(f["unit"]),
            "installation_id": _installation_of(f),
            "failed_on": f["on"],
            "iso14224_failure_mode": f["mode"],
            "description": f["desc"],
            "repair_days": f["repair_days"],
            "unit_swapped": bool(f["swapped"]),
        }
        for f in sorted(failures, key=lambda f: f["on"])
    ])

    units_here = set(unit_ids)
    notes = [n for n in w.notifications if n["pos"] in positions or (n["pos"] is None and n["unit"] in units_here)]
    notification = pd.DataFrame([
        {
            "notification_id": n["id"],
            "notification_type": n["type"],
            "priority": n["prio"],
            "status": n["status"],
            "reported_on": n["on"],
            "functional_location_id": n["pos"],
            "equipment_id": strip(n["unit"]),
            "short_text": n["text"],
            "iso14224_failure_mode": n["mode"],
            "failure_event_id": n["fail"],
        }
        for n in sorted(notes, key=lambda n: n["on"])
    ])
    note_ids = set(notification["notification_id"])
    orders = [o for o in w.workorders if o["notif"] in note_ids or o["pos"] in positions]
    work_order = pd.DataFrame([
        {
            "work_order_id": o["id"],
            "order_type": o["type"],
            "notification_id": o["notif"],
            "functional_location_id": o["pos"],
            "equipment_id": strip(o["unit"]),
            "basic_start": o["start"],
            "basic_finish": o["end"],
            "short_text": o["text"],
        }
        for o in sorted(orders, key=lambda o: o["start"])
    ])

    sigs = {sid: s for sid, s in w.signals.items() if _is_refinery(s["site"])}
    signal = pd.DataFrame([
        {
            "signal_id": sid,
            "tag": s["tag"],
            "site_id": s["site"],
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
    signal_daily = daily_frame(w, sorted(sigs), history_days())

    serials = set(equipment["equipment_id"])
    genealogy = [g for g in w.genealogy if g["serial"] in serials]
    component_genealogy = pd.DataFrame([
        {"equipment_id": g["serial"], "component_kind": g["kind"], "lot_id": g["lot"]} for g in genealogy
    ])
    lot_ids = set(component_genealogy["lot_id"])
    material_lot = pd.DataFrame([
        {
            "lot_id": lot["id"],
            "material": lot["material"],
            "supplier_id": strip(lot["supplier"]),
            "received_on": lot["received"],
            "quantity": lot["qty"],
            "engineering_change_id": lot["eco"],
            "purchase_order": lot["po"],
        }
        for lid, lot in sorted(w.lots.items()) if lid in lot_ids
    ])
    engineering_change = pd.DataFrame([
        {
            "engineering_change_id": e["id"],
            "title": e["title"],
            "part": e["part"],
            "approval_route": e["route"],
            "qualification_waived": bool(e["waived"]),
            "approved_on": e["approved"],
            "status": e["status"],
            "supplier_from": strip(e["supplier_from"]),
            "supplier_to": strip(e["supplier_to"]),
        }
        for e in sorted(w.ecos.values(), key=lambda e: e["id"])
    ])

    tables = {
        "site": sites,
        "functional_location": flocs,
        "equipment": equipment,
        "installation": installation,
        "failure_event": failure_event,
        "notification": notification,
        "work_order": work_order,
        "signal": signal,
        "signal_daily": signal_daily,
        "material_lot": material_lot,
        "engineering_change": engineering_change,
        "component_genealogy": component_genealogy,
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
