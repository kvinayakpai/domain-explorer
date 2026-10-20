"""Story numbers and KPI variants computed from the world.

The blog posts cite these numbers; tests pin them so the text and the data cannot drift.
"""
from __future__ import annotations

from datetime import date, datetime, time, timedelta

import numpy as np

from . import spec
from .realism import oos_by_cause
from .spec import BY_SKU, DC_SKUS, HERO_SKU, OPEN_HOURS, param
from .world import CAUSE_GROUP, DAYS, STORY_FIRST, World, imputed_for_empty_hours

H = len(OPEN_HOURS)
JUNE = slice(STORY_FIRST, None)
WEEKS = [(spec.STORY_START + timedelta(days=7 * k), spec.STORY_START + timedelta(days=7 * k + 6)) for k in range(4)]


def _di(d: date) -> int:
    return DAYS.index(d)


def _at(di: int, hi: int, minute: int = 0) -> str:
    base = datetime.combine(DAYS[di], time(OPEN_HOURS[hi], 0)) + timedelta(minutes=minute)
    return base.isoformat(timespec="minutes")


def episodes(w: World, sku: str, first: date = spec.STORY_START, last: date = spec.END) -> list[dict]:
    """Runs of open hours with the shelf empty. Overnight closure does not break a run."""
    e = w.hourly[sku]["empty"]
    flat = [(di, hi) for di in range(_di(first), _di(last) + 1) for hi in range(H)]
    runs: list[list[tuple[int, int]]] = []
    cur: list[tuple[int, int]] = []
    for di, hi in flat:
        if e[di, hi] > 0:
            cur.append((di, hi))
        elif cur:
            runs.append(cur)
            cur = []
    if cur:
        runs.append(cur)
    out = []
    for run in runs:
        (sdi, shi), (edi, ehi) = run[0], run[-1]
        f0, f1 = float(e[sdi, shi]), float(e[edi, ehi])
        start = _at(sdi, shi, 0 if f0 >= 1 else round((1 - f0) * 60))
        end = _at(edi, ehi, 60 if f1 >= 1 else round(f1 * 60))
        sel = tuple(np.array(run).T)
        hw = w.hourly[sku]
        books = hw["book"][sel]
        out.append({
            "sku": sku, "start": start, "end": end,
            "empty_open_hours": round(float(e[sel].sum()), 1),
            "lost_units": int(hw["lost"][sel].sum()),
            "lost_value_inr": round(float(hw["lost"][sel].sum()) * BY_SKU[sku].price, 0),
            "book_on_hand_min": int(books.min()), "book_on_hand_max": int(books.max()),
            "reorder_point": sorted({int(w.daily[sku]["reorder_point"][d]) for d in {sdi - 1, *sel[0]} if d >= 0}),
            "responses": {k: int(hw[k][sel].sum()) for k in param("oos_response")},  # type: ignore[union-attr]
            "causes": sorted({w.causes[sku][di][hi] for di, hi in run}),
        })
    return out


def kpis(w: World, sku: str = HERO_SKU) -> dict:
    """The same month measured four ways, plus the records each persona looks at."""
    d, h = w.daily[sku], w.hourly[sku]
    open_hours = h["empty"][JUNE].size
    in_stock_book = float((h["book"][JUNE] >= 1).mean())
    audits = [a for a in w.audits if a["sku"] == sku]
    audit_osa = sum(a["status"] == "on shelf" for a in audits) / max(1, len(audits))
    hourly_osa = 1 - float(h["empty"][JUNE].sum()) / open_hours
    demand = float(d["demand"][JUNE].sum())
    served = 1 - float(d["lost"][JUNE].sum()) / demand
    # Forecast for day t is the one made at 22:00 the night before.
    fc = d["forecast"][STORY_FIRST - 1:-1]
    rec = d["scanned"][JUNE]
    true = d["demand"][JUNE]
    wmape_rec = float(np.abs(fc - rec).sum() / rec.sum())
    wmape_true = float(np.abs(fc - true).sum() / true.sum())

    def weekly(series: np.ndarray) -> list[int]:
        return [int(series[_di(a):_di(b) + 1].sum()) for a, b in WEEKS]

    family = [s for s in DC_SKUS if BY_SKU[s].family == BY_SKU[sku].family]
    return {
        "osa": {
            "system_in_stock": round(in_stock_book, 3),
            "shelf_audit": round(audit_osa, 3),
            "open_hours_on_shelf": round(hourly_osa, 3),
            "demand_served": round(served, 3),
            "audits": [{"ts": a["audit_ts"], "status": a["status"]} for a in audits],
        },
        "lost_units": int(d["lost"][JUNE].sum()),
        "lost_value_inr": round(float(d["lost"][JUNE].sum()) * BY_SKU[sku].price, 0),
        "empty_open_hours": round(float(d["empty_hours"][JUNE].sum()), 1),
        "forecast": {
            "wmape_vs_recorded_sales": round(wmape_rec, 3),
            "wmape_vs_true_demand": round(wmape_true, 3),
            "start": round(float(d["forecast"][STORY_FIRST - 1]), 1),
            "end": round(float(d["forecast"][-1]), 1),
        },
        "weekly": {
            "weeks": [f"{a:%d %b}-{b:%d %b}" for a, b in WEEKS],
            "true_demand": weekly(d["demand"]),
            "recorded_sales": {s: weekly(w.daily[s]["scanned"]) for s in family},
            "store_orders_units": weekly(d["ordered"]),
        },
    }


def corrected_forecast(w: World, sku: str = HERO_SKU) -> float:
    """What the 28-day forecast would read at month end if empty-shelf hours were filled in."""
    di = len(DAYS) - 1
    lo = di - 27
    rec = w.daily[sku]["scanned"][lo:di + 1]
    return round(float((rec + imputed_for_empty_hours(sku, w.scanned_hourly, w.daily, lo, di)).mean()), 1)


def causes(w: World) -> dict:
    by = oos_by_cause(w, DC_SKUS)
    total = sum(by.values()) or 1.0
    groups: dict[str, float] = {}
    for c, v in by.items():
        groups[CAUSE_GROUP[c]] = groups.get(CAUSE_GROUP[c], 0.0) + v
    return {"hours": {k: round(v, 1) for k, v in sorted(by.items())},
            "groups_share": {k: round(v / total, 3) for k, v in sorted(groups.items())}}


def milk(w: World, sku: str = "MILK-TONED-500ML") -> dict:
    p = BY_SKU[sku]
    delivered = sum(x["units"] for x in w.dsd if x["sku"] == sku and x["delivery_ts"] >= spec.STORY_START.isoformat())
    expired = sum(x["units"] for x in w.write_offs if x["sku"] == sku and x["reason"] == "expired"
                  and x["date"] >= spec.STORY_START.isoformat())
    d = w.daily[sku]
    sold, lost, demand = (float(d[k][JUNE].sum()) for k in ("sold", "lost", "demand"))
    margin = p.price - p.cost
    return {"sku": sku, "delivered": int(delivered), "sold": int(sold), "demand": int(demand), "lost": int(lost),
            "unmet_share": round(lost / demand, 3), "expired": int(expired),
            "waste_share": round(expired / delivered, 3),
            "margin_per_unit_inr": round(margin, 2), "cost_per_unit_inr": p.cost,
            "gross_margin_inr": round(sold * margin, 0), "waste_cost_inr": round(expired * p.cost, 0),
            "net_inr": round(sold * margin - expired * p.cost, 0),
            "empty_open_hours": round(float(d["empty_hours"][JUNE].sum()), 1)}


def _event(w: World, kind: str, sku: str = HERO_SKU) -> dict | None:
    return next((e for e in w.events if e["kind"] == kind and e["sku"] == sku and e["ts"] >= "2026-06"), None)


def retail_story(w: World) -> dict:
    mis = _event(w, "misplaced_putaway")
    found = _event(w, "found_in_backroom") or _event(w, "alert_count")
    eps = episodes(w, HERO_SKU)
    ep1 = next((e for e in eps if mis and e["start"] >= mis["ts"] and (not found or e["start"] < found["ts"])), None)
    k = kpis(w)
    may = slice(0, STORY_FIRST)
    return {
        "misplaced": mis and {"ts": mis["ts"], "units": mis["units"], "cases": mis["units"] // BY_SKU[HERO_SKU].case_units},
        "found": found and {"ts": found["ts"], "kind": found["kind"]},
        "episode": ep1,
        "true_demand_per_day": {"may": round(float(w.hourly[HERO_SKU]["demand_base"][may].sum(axis=1).mean()), 1),
                                "june": round(float(w.hourly[HERO_SKU]["demand_base"][JUNE].sum(axis=1).mean()), 1)},
        "forecast": {"before": round(float(w.daily[HERO_SKU]["forecast"][_di(date(2026, 6, 9))]), 1),
                     "end_recorded_sales": k["forecast"]["end"],
                     "end_corrected": corrected_forecast(w)},
        "kpis": k,
    }


def logistics_story(w: World) -> dict:
    ev = _event(w, "wrong_pallet")
    if not ev:
        return {}
    ship = next(s for s in w.shipments if s["arrived_ts"] == ev["ts"])
    lines = [a for a in w.asn_lines if a["shipment_id"] == ship["shipment_id"]]
    hero = next(a for a in lines if a["sku"] == HERO_SKU)
    truth = next(t for t in w.pallets_truth if t["sscc"] == hero["sscc"] and t["line"] == hero["line"])
    eps = [e for e in episodes(w, HERO_SKU) if e["start"] >= ev["ts"]]
    counts = [c for c in w.counts if c["count_ts"] >= ev["ts"] and c["sku"] in ("ATTA-WW-5KG", "ATTA-WW-1KG")
              and c["trigger"] != "scheduled full count"]
    return {"shipment": ship, "line": hero, "actual": truth, "episode": eps[0] if eps else None,
            "corrections": counts, "lines_on_truck": len(lines)}


def payments_story(w: World) -> dict:
    if not w.bills:
        return {}
    amounts = np.array([b["amount_inr"] for b in w.bills])
    tenders = [b["tender"] for b in w.bills]
    return {"bills": len(w.bills), "median_bill_inr": round(float(np.median(amounts)), 0),
            "share_above_2000": round(float((amounts > 2000).mean()), 3),
            "tender_share": {t: round(tenders.count(t) / len(tenders), 3) for t in sorted(set(tenders))}}


def build(w: World, realism_results: list[tuple[str, bool, str, str]]) -> dict:
    end = [c for c in w.counts if c["count_ts"].startswith(spec.END.isoformat())]
    return {
        "world": {"seed": w.seed, "store": spec.STORE, "dc": spec.DC, "dairy": spec.DAIRY,
                  "history": [spec.HISTORY_START.isoformat(), (spec.STORY_START - timedelta(days=1)).isoformat()],
                  "story": [spec.STORY_START.isoformat(), spec.END.isoformat()], "scenario": w.scenario.key},
        "planted_events": [e for e in w.events if e["planted"]],
        "retail": retail_story(w),
        "logistics": logistics_story(w),
        "payments": payments_story(w),
        "out_of_stock_causes": causes(w),
        "record_accuracy_end_of_june": {"items": len(end), "wrong": sum(c["adjustment"] != 0 for c in end),
                                        "counts": end},
        "milk": milk(w),
        "realism": [{"check": n, "pass": ok, "detail": d, "source": s} for n, ok, d, s in realism_results],
    }
