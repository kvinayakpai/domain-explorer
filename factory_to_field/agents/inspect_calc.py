"""Remaining-life arithmetic the agent runs on raw inspection data (plan 4.7c).

Rules are the author's reading of common practice and are NOT confirmed by an inspection engineer; they are stated in
world/gen_fixed.py and restated here so the agent and the key can disagree if either is wrong:
mm/inch conversion; readings count from the component's install date; a rise of more than 0.15 mm is an anomaly (excluded, flagged);
rate = max(last two valid, first to last valid); life = (last - required minimum) / rate; next due = last reading + min(life/2, 10 years).
"""
from __future__ import annotations

from datetime import date, timedelta

TOL_MM, MAX_INTERVAL_Y = 0.15, 10.0


def years(a: date, b: date) -> float:
    return (b - a).days / 365.25


def analyse(data: dict, today: date) -> dict:
    """data = FileSource.inspection(component). Returns the facts the report quotes."""
    comp = data["component"]
    installed = date.fromisoformat(comp["installed"])
    alias = {a["old"]: a["new"] for a in data["aliases"]}
    per: dict[str, list[tuple[date, float, str]]] = {}
    ignored_before_install = 0
    for r in data["readings"]:
        d = date.fromisoformat(r["date"])
        if d < installed:
            ignored_before_install += 1
            continue
        if d > today:
            continue
        mm = float(r["value"]) * 25.4 if r["unit"] == "in" else float(r["value"])
        per.setdefault(alias.get(r["cml"], r["cml"]), []).append((d, mm, r["unit"]))
    best, flagged, single = None, [], []
    converted = sum(1 for pts in per.values() for p in pts if p[2] == "in")
    for cml, pts in per.items():
        pts.sort()
        ok: list[tuple[date, float, str]] = []
        for p in pts:
            if ok and p[1] - ok[-1][1] > TOL_MM:
                flagged.append(cml)
            else:
                ok.append(p)
        if len(ok) < 2:
            single.append(cml)
            continue
        rate = max((ok[-2][1] - ok[-1][1]) / years(ok[-2][0], ok[-1][0]), (ok[0][1] - ok[-1][1]) / years(ok[0][0], ok[-1][0]))
        if rate <= 0:
            continue
        life = (ok[-1][1] - float(comp["required_min_mm"])) / rate
        if best is None or round(life, 2) < best["life_y"]:
            best = {"cml": cml, "rate_mm_y": round(rate, 4), "life_y": round(life, 2), "last": ok[-1][0], "last_mm": round(ok[-1][1], 2)}
    out = {"component": comp["component"], "circuit": comp["circuit"], "required_min_mm": float(comp["required_min_mm"]), "installed": comp["installed"],
           "flagged_remeasure": sorted(set(flagged)), "single_reading_cmls": sorted(single), "readings_before_install_ignored": ignored_before_install,
           "inch_readings_converted": converted, "worst_cml": None, "remaining_life_y": None, "next_due": None, "overdue": None}
    if best:
        due = best["last"] + timedelta(days=int(min(best["life_y"] / 2, MAX_INTERVAL_Y) * 365.25))
        out.update(worst_cml=best["cml"], rate_mm_y=best["rate_mm_y"], remaining_life_y=best["life_y"], last_mm=best["last_mm"],
                   next_due=due.isoformat(), overdue=due < today, below_minimum=best["life_y"] < 0)
    return out
