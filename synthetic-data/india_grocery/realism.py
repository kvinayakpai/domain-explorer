"""Realism checks for the India grocery world.

Each check returns (name, passed, detail, source). "Published" checks compare the world
with a study; "logic" checks catch impossible records; "assumption" checks confirm the
generator honours a stated assumption.
"""
from __future__ import annotations

from datetime import date, datetime

import numpy as np

from . import spec
from .ids import is_valid
from .spec import BY_SKU, DC_SKUS, PRODUCTS, param
from .world import CAUSE_GROUP, DAYS, STORY_FIRST, Draws, Scenario, World, simulate

Check = tuple[str, bool, str, str]

FMI_2002 = ("FMI, GMA and CIES (2002), worldwide out-of-stock study: average 8.3%; about 47% from store "
            "ordering and forecasting, 25% from shelf management")
DR_2008 = "DeHoratius and Raman (2008), Management Science 54(4): 65% of 370,000 records inaccurate"
GS1 = "GS1 General Specifications: prefixes 20-29 are restricted circulation numbers"


def oos_by_cause(w: World, skus: list[str]) -> dict[str, float]:
    out: dict[str, float] = {}
    for s in skus:
        for di in range(STORY_FIRST, len(DAYS)):
            for hi, frac in enumerate(w.hourly[s]["empty"][di]):
                if frac > 0:
                    cause = w.causes[s][di][hi]
                    out[cause] = out.get(cause, 0.0) + float(frac)
    return out


def checks(w: World, dr: Draws) -> list[Check]:
    res: list[Check] = []

    def add(name: str, ok: bool, detail: str, source: str) -> None:
        res.append((name, bool(ok), detail, source))

    june = slice(STORY_FIRST, None)
    hours = (len(DAYS) - STORY_FIRST) * len(spec.OPEN_HOURS)

    # 1. Out-of-stock rate.
    empty = sum(float(w.daily[s]["empty_hours"][june].sum()) for s in DC_SKUS)
    rate = empty / (hours * len(DC_SKUS))
    add("Warehouse-supplied items are off the shelf 3-14% of open hours", 0.03 <= rate <= 0.14,
        f"{rate:.1%} of open hours across {len(DC_SKUS)} items in June", FMI_2002)

    # 2. Where out-of-stocks start.
    by_cause = oos_by_cause(w, DC_SKUS)
    total = sum(by_cause.values()) or 1.0
    groups: dict[str, float] = {}
    for c, v in by_cause.items():
        groups[CAUSE_GROUP[c]] = groups.get(CAUSE_GROUP[c], 0.0) + v
    in_store = (groups.get("shelf and backroom", 0.0) + groups.get("store ordering and stock records", 0.0)) / total
    add("Most out-of-stock hours start in the store (at least 60%)", in_store >= 0.60,
        f"{in_store:.0%} in the store; " + ", ".join(f"{k} {v / total:.0%}" for k, v in sorted(groups.items())),
        FMI_2002 + "; McKinnon, Mendes and Nabateh (2007): 70-90% from shelf replenishment")

    # 3. Inventory record accuracy at the month-end count.
    end = [c for c in w.counts if c["count_ts"].startswith(spec.END.isoformat())]
    wrong = [c for c in end if c["adjustment"] != 0]
    share = len(wrong) / max(1, len(end))
    add("Most item records are wrong at the month-end count (40-85%)", 0.40 <= share <= 0.85,
        f"{len(wrong)} of {len(end)} items differ: " + ", ".join(f"{c['sku']} {c['adjustment']:+d}" for c in wrong),
        DR_2008)

    # 4. Shopper responses to an empty shelf.
    resp = param("oos_response")
    keys = list(resp)  # type: ignore[arg-type]
    counts = {k: sum(float(w.daily[s][k].sum()) for s in BY_SKU) for k in keys}
    n = sum(counts.values())
    worst = max(abs(counts[k] / n - resp[k]) for k in keys) if n else 1.0  # type: ignore[index]
    add("Shoppers facing an empty shelf respond in the studied proportions (within 7 points)",
        n >= 200 and worst <= 0.07,
        f"{n:.0f} empty-shelf encounters; " + ", ".join(f"{k} {counts[k] / n:.0%}" for k in keys),
        str(spec.PARAMS["oos_response"][1]))

    # 5. Sales never exceed what customers wanted.
    bad = 0
    for s in BY_SKU:
        d = w.daily[s]
        bad += int(np.sum(d["sold"] - d["subs_in"] > d["demand"] + 1e-9))
    add("Sales of an item never exceed its own demand (plus substitutes)", bad == 0, f"{bad} item-days violate",
        "logic")

    # 6. Milk shelf life.
    milk = [x for x in w.dsd if BY_SKU[x["sku"]].family == "milk"]
    span = {(date.fromisoformat(x["use_by"]) - datetime.fromisoformat(x["delivery_ts"]).date()).days for x in milk}
    add("Pouch milk is sellable on the delivery day and the next (48 hours from packing)", span == {1},
        f"use-by minus delivery date: {sorted(span)} day(s) over {len(milk)} deliveries",
        str(spec.PARAMS["milk_shelf_life_hours"][1]))

    # 7. Receipts match shipping-notice pallets and follow dispatch.
    asn = {(a["sscc"], a["line"]): a for a in w.asn_lines}
    ships = {s["shipment_id"]: s for s in w.shipments}
    bad = [r for r in w.receipts if (r["sscc"], r["line"]) not in asn
           or r["received_ts"] < ships[r["shipment_id"]]["dispatched_ts"]]
    add("Every goods receipt matches a shipping-notice pallet and comes after dispatch", not bad,
        f"{len(bad)} of {len(w.receipts)} receipt lines violate", "logic")

    # 8. Morning deliveries.
    on_time = [s for s in w.shipments if s["arrival_minute"] <= 6 * 60 + 30]
    share = len(on_time) / max(1, len(w.shipments))
    add("The DC truck makes its 06:00-06:30 slot on most mornings (85%+)", share >= 0.85,
        f"{len(on_time)} of {len(w.shipments)} deliveries in the slot", str(spec.PARAMS["truck_late_rate"][1]))

    # 9. Identifiers.
    codes = [p.gtin for p in PRODUCTS] + [loc["gln"] for loc in spec.LOCATIONS] + [a["sscc"] for a in w.asn_lines]
    bad_codes = [c for c in codes if not is_valid(c)]
    restricted = all((c[:2] if len(c) == 13 else c[1:3]) == "29" for c in codes)
    add("GTINs, GLNs and SSCCs carry valid check digits under the restricted prefix 29",
        not bad_codes and restricted, f"{len(codes)} identifiers, {len(bad_codes)} invalid", GS1)

    # 10. Overdispersed demand.
    over = [p.sku for p in PRODUCTS if p.profile == "staples"
            and np.var(w.daily[p.sku]["demand"]) > np.mean(w.daily[p.sku]["demand"])]
    staples = [p.sku for p in PRODUCTS if p.profile == "staples"]
    add("Daily demand is noisier than a Poisson process (variance above mean)", len(over) == len(staples),
        f"{len(over)} of {len(staples)} staples overdispersed", str(spec.PARAMS["demand_shape_k"][1]))

    # 11. Weekends and month starts.
    base = {s: w.hourly[s]["demand_base"].sum(axis=1) for s in staples}
    wk = np.array([d.weekday() >= 5 for d in DAYS])
    first = np.array([d.day <= 7 for d in DAYS])
    late = np.array([d.day >= 22 for d in DAYS])
    weekend_lift = np.mean([base[s][wk].mean() / base[s][~wk].mean() for s in staples])
    month_lift = np.mean([base[s][first].mean() / base[s][late].mean() for s in staples])
    add("Staples sell more at weekends and in the first week of the month", weekend_lift > 1.10 and month_lift > 1.15,
        f"weekend x{weekend_lift:.2f}, first week vs last x{month_lift:.2f}",
        str(spec.PARAMS["dow_staples"][1]) + "; " + str(spec.PARAMS["month_start"][1]))

    # 12. Milk waste and gaps.
    s = "MILK-TONED-500ML"
    delivered = sum(x["units"] for x in w.dsd if x["sku"] == s and x["delivery_ts"] >= spec.STORY_START.isoformat())
    expired = sum(x["units"] for x in w.write_offs if x["sku"] == s and x["reason"] == "expired"
                  and x["date"] >= spec.STORY_START.isoformat())
    lost = float(w.daily[s]["lost"][june].sum())
    demand = float(w.daily[s]["demand"][june].sum())
    add("Toned milk waste stays between 1% and 8% and gaps under 5% at the usual standing order",
        0.01 <= expired / delivered <= 0.08 and lost / demand < 0.05,
        f"waste {expired / delivered:.1%}, demand unmet {lost / demand:.1%}", "assumption")

    # 13. Bills.
    if w.bills:
        amounts = np.array([b["amount_inr"] for b in w.bills])
        upi = np.mean([b["tender"] == "UPI" for b in w.bills])
        big = float(np.mean(amounts > 2000))
        add("UPI is the main tender and some bills cross the Rs 2,000 merchant-fee threshold",
            0.55 <= upi <= 0.70 and 0.02 <= big <= 0.20,
            f"UPI {upi:.0%} of {len(w.bills):,} bills; {big:.1%} above Rs 2,000; median Rs {np.median(amounts):,.0f}",
            str(spec.PARAMS["tender_mix"][1]))

    # 14. Same customers and same history in every scenario.
    other = simulate(Scenario(alert_days=1, backroom_discipline=True), w.seed, dr)
    same_customers = all(np.array_equal(w.hourly[s]["demand_base"], other.hourly[s]["demand_base"]) for s in BY_SKU)
    same_history = all(np.array_equal(w.daily[s]["scanned"][:STORY_FIRST], other.daily[s]["scanned"][:STORY_FIRST])
                       for s in BY_SKU)
    add("Every scenario faces the same customers and the same four weeks of history",
        same_customers and same_history, f"customers identical: {same_customers}; history identical: {same_history}",
        "logic: common random numbers")
    return res


def report(res: list[Check]) -> str:
    lines = [f"India grocery world: {sum(r[1] for r in res)} of {len(res)} realism checks pass", ""]
    for name, ok, detail, source in res:
        lines.append(f"[{'PASS' if ok else 'FAIL'}] {name}")
        lines.append(f"       {detail}")
        lines.append(f"       source: {source}")
    return "\n".join(lines)
