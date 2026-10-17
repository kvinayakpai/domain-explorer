"""Realism checks. These exist because an earlier version of this repo shipped synthetic data that
looked fine in a schema review and was meaningless: every sensor ~N(50, 8), 2.0% anomalies vs 2.0%,
work orders that ended before they started, and failure modes that cannot happen on the asset class."""
from __future__ import annotations

import sqlite3
from datetime import date, timedelta
from pathlib import Path

import numpy as np

from .model import World
from .spec import HIST_START

ISO_PUMP_MODES = {"VIB", "ELP", "ELU", "OHE", "NOI", "PDE", "BRD", "FTS", "STP", "INL", "SER", "ERO"}
PUMP_FORBIDDEN = {"ERO"}


def checks(w: World, out: Path) -> list[tuple[str, bool, str]]:
    res: list[tuple[str, bool, str]] = []

    def add(name: str, ok: bool, detail: str) -> None:
        res.append((name, bool(ok), detail))

    # 1. installations never overlap at a position or for a unit
    bad = 0
    for key in ("pos", "unit"):
        groups: dict[str, list[dict]] = {}
        for i in w.installs:
            groups.setdefault(i[key], []).append(i)
        for lst in groups.values():
            lst.sort(key=lambda i: i["from"])
            for a, b in zip(lst, lst[1:]):
                if a["to"] is None or a["to"] > b["from"]:
                    bad += 1
    add("installations do not overlap (position or unit)", bad == 0, f"{bad} overlaps")
    # 2. every failure happened while its unit was installed at that position
    bad = 0
    for f in w.failures:
        ok = any(i["unit"] == f["unit"] and i["pos"] == f["pos"] and i["from"] <= f["on"] <= (i["to"] or date.max) for i in w.installs)
        bad += not ok
    add("failures happen while the unit is installed at that position", bad == 0, f"{bad} of {len(w.failures)} violate")
    # 3. failure modes are valid for the asset class
    bad = [f for f in w.failures if f["mode"] in PUMP_FORBIDDEN or f["mode"] not in ISO_PUMP_MODES]
    add("failure modes are ISO 14224 modes that can occur on pumps", not bad, f"{len(bad)} invalid")
    # 4. work orders: end not before start; every corrective order points at the unit/position of its notification
    bad = [o for o in w.workorders if o["end"] and o["end"] < o["start"]]
    add("no work order ends before it starts", not bad, f"{len(bad)} violate")
    notes = {n["id"]: n for n in w.notifications}
    bad = [o for o in w.workorders if o.get("notif") and o["start"] < notes[o["notif"]]["on"]]
    add("no work order starts before its notification", not bad, f"{len(bad)} violate")
    # 5. maker chronology for operator units
    bad = 0
    for i in w.installs:
        u = w.units[i["unit"]]
        sh = u.get("shipped")
        if sh and u["maker"] == "org:kestrel" and i["from"] < sh:
            bad += 1
    add("units are installed only after the maker shipped them", bad == 0, f"{bad} violate")
    # 6. genealogy lots were received before the unit was built
    bad = 0
    for g in w.genealogy:
        lot = w.lots.get(g["lot"])
        if lot is None:
            continue
        b = next((x for x in w.builds if x["serial"] == g["serial"]), None)
        if b and lot["received"] > b["built"]:
            bad += 1
    add("component lots arrive before the units they go into", bad == 0, f"{bad} violate")
    # 7. the signals are not Gaussian white noise
    con = sqlite3.connect(out / "historian_pi.sqlite")
    skews, acs = [], []
    for (tid,) in con.execute("SELECT tag_id FROM tags WHERE name LIKE '10P10_A.VIB_DE' OR name LIKE '21P21_A.VIB_DE'").fetchall():
        v = np.array([r[0] for r in con.execute("SELECT mean FROM daily WHERE tag_id=? ORDER BY day", (tid,)).fetchall()])
        run = v > 0.5  # days the pump ran; consecutive running days only
        pairs = [(v[i], v[i + 1]) for i in range(len(v) - 1) if run[i] and run[i + 1]]
        vv = v[run]
        if len(vv) < 100 or len(pairs) < 100:
            continue
        skews.append(float(((vv - vv.mean()) ** 3).mean() / vv.std() ** 3))
        a_, b_ = np.array(pairs).T
        acs.append(float(np.corrcoef(a_, b_)[0, 1]))
    skew, ac1 = float(np.median(skews)), float(np.median(acs))
    add("vibration is right-skewed and persistent, not N(50, 8) noise", skew > 0.2 and ac1 > 0.3, f"skew {skew:.2f}, lag-1 autocorrelation {ac1:.2f}")
    # 8. spread between machines
    means = [r[0] for r in con.execute("SELECT AVG(d.mean) FROM daily d JOIN tags t USING(tag_id) WHERE t.name LIKE '%.VIB_DE' AND d.mean>0.5 AND t.name LIKE '1%' GROUP BY t.tag_id").fetchall()]
    add("machines differ from each other (baselines are not identical)", np.std(means) / np.mean(means) > 0.08, f"coefficient of variation {np.std(means) / np.mean(means):.2f}")
    # 9. there is a real signal before failures: 21 days before vs 150-100 days before
    ratios = []
    for f in w.failures:
        if f["mode"] in ("VIB",) and f["on"] > HIST_START + timedelta(days=200) and f["unit"] in w.units and not f["pos"].startswith("pos:FA"):
            s = next((s for s, v in w.signals.items() if v["pos"] == f["pos"] and v["quantity"] == "vibration_de"), None)
            if s is None:
                continue
            tag = w.signals[s]["tag"]
            q = con.execute("SELECT d.day, d.mean FROM daily d JOIN tags t USING(tag_id) WHERE t.name=? AND d.mean>0.5", (tag,)).fetchall()
            before = [m for dd, m in q if f["on"] - timedelta(days=21) <= date.fromisoformat(dd) < f["on"]]
            base = [m for dd, m in q if f["on"] - timedelta(days=150) <= date.fromisoformat(dd) < f["on"] - timedelta(days=100)]
            if before and base:
                ratios.append(np.mean(before) / np.mean(base))
    add("vibration rises before vibration failures (signal exists)", len(ratios) >= 3 and float(np.median(ratios)) > 1.3,
        f"median ratio {float(np.median(ratios)) if ratios else float('nan'):.2f} over {len(ratios)} failures")
    # 10. timestamps in historians are UTC, SAP is local with separate date and time
    ts = con.execute("SELECT ts FROM raw LIMIT 1").fetchone()[0]
    add("historian timestamps are UTC (Z)", ts.endswith("Z"), ts)
    s = sqlite3.connect(out / "sap_pm.sqlite")
    q = s.execute("SELECT qmdat, mzeit FROM QMEL LIMIT 1").fetchone()
    add("SAP notifications carry local date and time in separate fields", len(q[0]) == 10 and len(q[1]) == 8, str(q))
    # 11. mixed engineering units exist (R3 reports vibration in in/s)
    units = {r[0] for r in con.execute("SELECT DISTINCT engunits FROM tags WHERE name LIKE '%VIB_DE'")}
    add("engineering units are mixed across sites", {"mm/s", "in/s"} <= units, str(sorted(units)))
    # 12. data-quality blemishes exist but are limited
    blank = s.execute("SELECT COUNT(*) FROM EQUI WHERE (sernr IS NULL OR sernr='') AND herst='Kestrel Pump Works'").fetchone()[0]
    kest = s.execute("SELECT COUNT(*) FROM EQUI WHERE herst='Kestrel Pump Works'").fetchone()[0]
    add("a few percent of SAP serial numbers are blank or malformed", 0.01 < (blank / kest) < 0.1, f"{blank} blank of {kest}")
    return res


def report(res: list[tuple[str, bool, str]]) -> str:
    return "\n".join(f"{'PASS' if ok else 'FAIL'}  {n}  [{d}]" for n, ok, d in res)
