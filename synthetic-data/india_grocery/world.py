"""Simulation engine for the India grocery world.

One store, hourly, for eight weeks (four of history, four of story). The store runs a
min/max reorder rule on its own book stock; the book drifts from the shelf through
wrong-size scans, unrecorded damage and theft, misplaced cases and shipping-notice
receiving. Every random number is drawn up front (common random numbers), so the
store-side interventions in ``Scenario`` change outcomes but never the customers.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import date, datetime, time, timedelta

import numpy as np

from . import spec
from .ids import sscc18
from .spec import (
    BY_SKU,
    CASE_KG,
    DAYS,
    DC_SKUS,
    DC_SLOTS,
    DSD_SKUS,
    HERO_SKU,
    OPEN_HOURS,
    PALLET_TARE_KG,
    PRODUCTS,
    param,
)

H = len(OPEN_HOURS)
N_DAYS = len(DAYS)
DAY_INDEX = {d: i for i, d in enumerate(DAYS)}
STORY_FIRST = DAY_INDEX[spec.STORY_START]
FAMILIES: dict[str, list[str]] = {}
for _p in PRODUCTS:
    FAMILIES.setdefault(_p.family, []).append(_p.sku)

STORE_GROUP = {"ordering", "record_error"}
SHELF_GROUP = {"shelf_refill", "misplaced"}
UPSTREAM_GROUP = {"late_truck", "dc_short", "wrong_pallet"}
CAUSE_GROUP = {**dict.fromkeys(STORE_GROUP, "store ordering and stock records"),
               **dict.fromkeys(SHELF_GROUP, "shelf and backroom"),
               **dict.fromkeys(UPSTREAM_GROUP, "upstream supply")}

_STREAMS = ["demand", "units", "restock", "misplace", "find", "damage", "theft", "dc", "truck",
            "count", "arrivals", "basket", "tender", "fresh"]


def _rng(seed: int, name: str) -> np.random.Generator:
    return np.random.default_rng([seed, _STREAMS.index(name) + 1])


DC_CHECKS = ("none", "pick_scan", "check_weigh")
RECEIVING = ("label", "case_scan")


@dataclass(frozen=True)
class Scenario:
    """Interventions in the store and the DC. The defaults are the chain as it runs today."""

    alert_days: int | None = None  # flag N days of sales under 25% of forecast with stock on the books
    backroom_discipline: bool = False  # cases scanned into bins at put-away; refill rounds never skipped
    milk_order_factor: float = 1.0  # multiplies the toned-milk standing order
    # DC: "none" confirms each pick by scanning the slot label; "pick_scan" scans every case's
    # barcode at pick; "check_weigh" weighs every pallet against its shipping notice at dispatch.
    dc_check: str = "none"
    # Store receiving: "label" scans the pallet label and books the shipping notice; "case_scan"
    # scans every case at receipt and books what is actually there.
    receiving: str = "label"
    # Hourly gap detector on the tills' records: once a run of open hours with no sales, while the
    # books show stock, becomes less likely than this under the item's usual sales rate, someone
    # checks the item's shelf and backroom within the next open hour. None: no detector.
    gap_alpha: float | None = None
    # Interventions start with the month-start count on 1 June, so the four weeks of history are
    # identical in every scenario.

    def __post_init__(self) -> None:
        if self.dc_check not in DC_CHECKS or self.receiving not in RECEIVING:
            raise ValueError(f"unknown dc_check {self.dc_check!r} or receiving {self.receiving!r}")

    @property
    def key(self) -> str:
        alert = "off" if self.alert_days is None else f"{self.alert_days}d"
        key = (f"alert-{alert}_backroom-{'on' if self.backroom_discipline else 'off'}"
               f"_milk-{self.milk_order_factor:.2f}")
        if self.dc_check != "none":
            key += f"_dc-{self.dc_check}"
        if self.receiving != "label":
            key += f"_recv-{self.receiving}"
        if self.gap_alpha is not None:
            key += f"_gap-{self.gap_alpha:g}"
        return key


AS_IS = Scenario()


class Draws:
    """Every random number the world needs, drawn once per seed in a fixed order."""

    def __init__(self, seed: int) -> None:
        self.seed = seed
        k = float(param("demand_shape_k"))  # type: ignore[arg-type]
        dow_st = param("dow_staples")
        dow_fr = param("dow_fresh")
        month = param("month_start")
        rd = _rng(seed, "demand")
        self.demand: dict[str, np.ndarray] = {}
        for p in PRODUCTS:
            shock = rd.gamma(k, 1.0 / k, size=N_DAYS)
            shape = np.array(spec.HOURLY[p.profile])
            arr = np.zeros((N_DAYS, H), dtype=np.int64)
            for di, d in enumerate(DAYS):
                if p.profile == "staples":
                    m = p.daily_mean * dow_st[d.weekday()] * month[min((d.day - 1) // 7, 3)]  # type: ignore[index]
                else:
                    m = p.daily_mean * dow_fr[d.weekday()]  # type: ignore[index]
                arr[di] = rd.poisson(shape * m * shock[di])
            self.demand[p.sku] = arr

        # Per-unit uniforms: mis-scan, which size, response when empty, which substitute, which bill.
        ru = _rng(seed, "units")
        self.units: dict[str, list[list[np.ndarray]]] = {}
        for p in PRODUCTS:
            rows = []
            for di in range(N_DAYS):
                rows.append([ru.random((int(self.demand[p.sku][di, hi]) + 30, 5)) for hi in range(H)])
            self.units[p.sku] = rows

        rr = _rng(seed, "restock")
        self.restock = {s: rr.random((N_DAYS, 2)) for s in DC_SKUS}
        rm = _rng(seed, "misplace")
        self.misplace = {s: rm.random(N_DAYS) for s in DC_SKUS}
        rf = _rng(seed, "find")
        self.find = {s: rf.random((N_DAYS, 2)) for s in DC_SKUS}
        rdm = _rng(seed, "damage")
        dmg = param("damage_per_day")
        share = float(param("damage_recorded_share"))  # type: ignore[arg-type]
        self.damage = {s: rdm.poisson(dmg[s], N_DAYS) for s in DC_SKUS}  # type: ignore[index]
        self.damage_recorded = {s: rdm.binomial(self.damage[s], share) for s in DC_SKUS}
        rt = _rng(seed, "theft")
        theft = param("theft_per_day")
        self.theft = {s: rt.poisson(theft.get(s, 0.0), N_DAYS) for s in DC_SKUS}  # type: ignore[union-attr]
        rdc = _rng(seed, "dc")
        self.dc_short = {s: rdc.random(N_DAYS) for s in DC_SKUS}
        rtr = _rng(seed, "truck")
        self.truck_late = rtr.random(N_DAYS)
        self.truck_late_min = rtr.integers(35, 150, N_DAYS)
        self.truck_early_min = rtr.integers(0, 25, N_DAYS)
        rc = _rng(seed, "count")
        self.count_find = {s: rc.random(N_DAYS) for s in BY_SKU}
        rfr = _rng(seed, "fresh")
        lam = float(param("fresh_damage_per_day"))  # type: ignore[arg-type]
        self.fresh_damage = {s: rfr.poisson(lam, N_DAYS) for s in DSD_SKUS}
        self.fresh_damage_recorded = {s: rfr.binomial(self.fresh_damage[s], 0.4) for s in DSD_SKUS}

        # Bills: arrivals per hour, minute within the hour, other merchandise, tender.
        ra = _rng(seed, "arrivals")
        tpd = float(param("transactions_per_day"))  # type: ignore[arg-type]
        mix = (np.array(spec.HOURLY["staples"]) + np.array(spec.HOURLY["fresh"])) / 2
        shock = ra.gamma(30.0, 1 / 30.0, size=N_DAYS)
        self.arrivals = np.zeros((N_DAYS, H), dtype=np.int64)
        for di, d in enumerate(DAYS):
            self.arrivals[di] = np.maximum(1, ra.poisson(mix * tpd * dow_st[d.weekday()] * shock[di]))  # type: ignore[index]
        rb = _rng(seed, "basket")
        rtd = _rng(seed, "tender")
        self.bill_minute: list[list[np.ndarray]] = []
        self.bill_other: list[list[np.ndarray]] = []
        self.bill_tender: list[list[np.ndarray]] = []
        for di in range(N_DAYS):
            self.bill_minute.append([np.sort(rb.integers(0, 60, int(n))) for n in self.arrivals[di]])
            self.bill_other.append([np.round(rb.lognormal(5.85, 0.95, int(n)), 2) for n in self.arrivals[di]])
            self.bill_tender.append([rtd.random(int(n)) for n in self.arrivals[di]])


@dataclass
class Stock:
    shelf: int = 0
    back: int = 0  # findable backroom stock
    lost: int = 0  # physically in the backroom, in the wrong bay (routine rounds may find it)
    lost_story: int = 0  # the scripted misplacement: found only by a thorough count or the story
    book: int = 0  # what the system says is on hand
    upstream_phantom: int = 0  # booked from a shipping notice, never physically received
    batches: list[list[int]] = field(default_factory=list)  # fresh: [use_by_day_index, units]

    def physical(self) -> int:
        return self.shelf + self.back + self.lost + self.lost_story


@dataclass
class World:
    scenario: Scenario
    seed: int
    hourly: dict[str, dict[str, np.ndarray]] = field(default_factory=dict)
    daily: dict[str, dict[str, np.ndarray]] = field(default_factory=dict)
    events: list[dict] = field(default_factory=list)
    orders: list[dict] = field(default_factory=list)
    shipments: list[dict] = field(default_factory=list)
    asn_lines: list[dict] = field(default_factory=list)
    receipts: list[dict] = field(default_factory=list)
    pallets_truth: list[dict] = field(default_factory=list)
    picks: list[dict] = field(default_factory=list)  # DC pick confirmations, one per shipping-notice line
    pallets: list[dict] = field(default_factory=list)  # one per SSCC: weight the notice implies, weight on the scale
    claims: list[dict] = field(default_factory=list)  # receiving discrepancies the store reports to the DC
    dc_adjustments: list[dict] = field(default_factory=list)  # DC stock corrections for the store's lines
    counts: list[dict] = field(default_factory=list)
    audits: list[dict] = field(default_factory=list)
    write_offs: list[dict] = field(default_factory=list)
    forecasts: list[dict] = field(default_factory=list)
    dsd: list[dict] = field(default_factory=list)
    bills: list[dict] = field(default_factory=list)
    bill_lines: list[dict] = field(default_factory=list)
    causes: dict[str, list[list[str]]] = field(default_factory=dict)
    scanned_hourly: dict[str, np.ndarray] = field(default_factory=dict)


def _ts(day: date, hour: int, minute: int = 0) -> str:
    return datetime.combine(day, time(hour, minute)).isoformat(timespec="minutes")


def simulate(scn: Scenario = AS_IS, seed: int = 42, draws: Draws | None = None,
             record_bills: bool = False) -> World:
    dr = draws or Draws(seed)
    w = World(scenario=scn, seed=seed)
    resp = param("oos_response")
    resp_keys = list(resp)  # type: ignore[arg-type]
    resp_cum = np.cumsum([resp[k] for k in resp_keys])  # type: ignore[index]
    mis_rate = float(param("mis_scan_rate"))  # type: ignore[arg-type]
    skip = param("restock_skip")
    reorder = param("reorder")
    z, cover, window = reorder["z"], reorder["cover_days"], int(reorder["window_days"])  # type: ignore[index]
    lead = int(param("lead_time_days"))  # type: ignore[arg-type]
    find_rate = float(param("find_rate_per_round"))  # type: ignore[arg-type]
    misplace_rate = float(param("misplace_rate"))  # type: ignore[arg-type]
    count_find_rate = float(param("count_find_rate"))  # type: ignore[arg-type]
    alert_share = float(param("low_sales_alert"))  # type: ignore[arg-type]
    milk_std = param("milk_standing_order")
    date_picking = float(param("fresh_date_picking"))  # type: ignore[arg-type]
    fresh_factor = float(param("fresh_standing_factor"))  # type: ignore[arg-type]

    hourly = {p.sku: {k: np.zeros((N_DAYS, H)) for k in
                      ("demand_base", "demand", "sold", "lost", "empty", "shelf", "back", "lost_stock", "book",
                       "subs_in", *resp_keys)}
              for p in PRODUCTS}
    for p in PRODUCTS:
        hourly[p.sku]["demand_base"][:] = dr.demand[p.sku]
    daily = {p.sku: {k: np.zeros(N_DAYS) for k in
                     ("demand", "sold", "scanned", "revenue", "lost", "subs_in", "empty_hours",
                      "forecast", "sigma", "reorder_point", "order_up_to", "ordered", "received_book",
                      "received_physical", "book_close", "physical_close", *resp_keys)}
             for p in PRODUCTS}
    causes = {s: [[""] * H for _ in range(N_DAYS)] for s in BY_SKU}
    scanned_hourly = {s: np.zeros((N_DAYS, H)) for s in BY_SKU}
    w.hourly, w.daily, w.causes, w.scanned_hourly = hourly, daily, causes, scanned_hourly

    stock: dict[str, Stock] = {}
    for p in PRODUCTS:
        if p.flow == "DC":
            sh = min(p.shelf_capacity, int(p.daily_mean * 1.2))
            bk = int(p.daily_mean * 1.0)
            stock[p.sku] = Stock(shelf=sh, back=bk, book=sh + bk)
        else:
            first = int(p.daily_mean * 0.15)
            stock[p.sku] = Stock(shelf=first, book=first, batches=[[0, first]])
    pipeline: list[dict] = []  # store orders in transit
    carry: dict[tuple[str, int, int], int] = {}  # delayed customers: (sku, day, hour) -> units
    alert_counts: set[tuple[int, str]] = set()  # (day index, sku) counted at 08:00
    serial = {"sscc": 1000, "order": 0}
    flags = {"misplaced_done": False, "wrong_pallet_done": False}
    freeze_s: dict[str, float] = dict.fromkeys(DC_SKUS, 0.0)  # today's reorder point, for attribution
    # Gap detector state: the expected sales over each item's current run of open hours with no sales,
    # the items already flagged in that run, and the checks booked for later hours.
    gap_limit = -math.log(scn.gap_alpha) if scn.gap_alpha else None
    gap_run: dict[str, float] = dict.fromkeys(DC_SKUS, 0.0)
    gap_flagged: set[str] = set()
    gap_checks: dict[tuple[int, int], list[str]] = {}
    gap_rate: dict[str, dict] = {}

    def event(ts: str, sku: str, kind: str, units: int, planted: bool, detail: str) -> None:
        w.events.append({"ts": ts, "sku": sku, "kind": kind, "units": int(units), "planted": planted,
                         "detail": detail, "scenario": scn.key})

    def do_count(di: int, hour: int, minute: int, skus: list[str], trigger: str, thorough: bool) -> None:
        day = DAYS[di]
        for s in skus:
            st = stock[s]
            found = st.lost if (thorough or dr.count_find[s][di] < count_find_rate) else 0
            found_story = st.lost_story if thorough else 0
            st.back += found + found_story
            st.lost -= found
            st.lost_story -= found_story
            found += found_story
            counted = st.shelf + st.back
            w.counts.append({"count_ts": _ts(day, hour, minute), "sku": s, "book_before": int(st.book),
                             "counted": int(counted), "adjustment": int(counted - st.book),
                             "trigger": trigger, "misplaced_found": int(found), "shelf_before": int(st.shelf)})
            st.book = counted
            st.upstream_phantom = 0

    def refill(s: str) -> None:
        st = stock[s]
        cap = BY_SKU[s].shelf_capacity
        move = min(cap - st.shelf, st.back)
        if move > 0:
            st.shelf += move
            st.back -= move

    def receive(di: int, ship: dict) -> None:
        day = DAYS[di]
        live = di >= STORY_FIRST
        discipline = scn.backroom_discipline and live
        case_scan = scn.receiving == "case_scan" and live
        checked = discipline or case_scan
        method = ("case scan at receipt" if case_scan else "case scan at put-away" if discipline
                  else "pallet label (SSCC) scan against the shipping notice")
        for line in [ln for ln in w.asn_lines if ln["shipment_id"] == ship["shipment_id"]]:
            s_asn, units_asn = line["sku"], line["units"]
            truth = next(t for t in w.pallets_truth if t["sscc"] == line["sscc"] and t["line"] == line["line"])
            s_act, units_act = truth["sku_actual"], truth["units_actual"]
            mismatch = s_act != s_asn
            if mismatch and checked:
                # A case scan shows 1 kg cases on a 5 kg line: book what arrived and report it to the DC.
                book_sku, book_units = s_act, units_act
                if case_scan:
                    event(ship["arrived_ts"], s_asn, "receiving_scan_caught_mismatch", units_asn, True,
                          f"Case scan at receipt found {units_act} units of {s_act} on a line the shipping notice "
                          f"lists as {units_asn} units of {s_asn}; booked what arrived and reported it to the DC.")
                else:
                    event(ship["arrived_ts"], s_asn, "put_away_scan_caught_mismatch", units_asn, True,
                          f"Put-away scan found {s_act} cases on a line booked as {s_asn}; receipt corrected.")
                w.claims.append({"claim_id": f"CLM-{day:%y%m%d}-{line['line']}", "claim_ts": ship["arrived_ts"],
                                 "shipment_id": ship["shipment_id"], "sscc": line["sscc"], "line": line["line"],
                                 "notice_sku": s_asn, "notice_units": int(units_asn), "received_sku": s_act,
                                 "received_units": int(units_act), "found_by": method})
            else:
                book_sku, book_units = s_asn, units_asn
            w.receipts.append({"grn_id": f"GRN-{day:%y%m%d}", "shipment_id": ship["shipment_id"],
                               "sscc": line["sscc"], "line": line["line"], "received_ts": ship["arrived_ts"],
                               "sku_booked": book_sku, "units_booked": int(book_units),
                               "receipt_method": method})
            stock[book_sku].book += book_units
            daily[book_sku]["received_book"][di] += book_units
            daily[s_act]["received_physical"][di] += units_act
            if mismatch and not checked:
                stock[s_asn].upstream_phantom += units_asn
            st = stock[s_act]
            misplace = story_misplace = False
            if not discipline:
                story = (s_act == HERO_SKU and not flags["misplaced_done"] and day >= date(2026, 6, 8))
                if story:
                    flags["misplaced_done"] = True
                    misplace = story_misplace = True
                    event(ship["arrived_ts"], s_act, "misplaced_putaway", units_act, True,
                          "Cases put away behind the rice stack, in the wrong bay.")
                elif dr.misplace[s_act][di] < misplace_rate:
                    misplace = True
                    event(ship["arrived_ts"], s_act, "misplaced_putaway", units_act, False,
                          "Cases put away in the wrong bay.")
            if misplace and story_misplace:
                st.lost_story += units_act
            elif misplace:
                st.lost += units_act
            else:
                st.back += units_act

    for di, day in enumerate(DAYS):
        wd = day.weekday()
        weekend = wd >= 5
        month_week = min((day.day - 1) // 7, 3)
        live = di >= STORY_FIRST
        discipline = scn.backroom_discipline and live
        alert_days = scn.alert_days if live else None
        milk_factor = scn.milk_order_factor if live else 1.0
        if gap_limit and live and not gap_rate:
            gap_rate.update(gap_profiles(scanned_hourly, STORY_FIRST))

        # 05:30 direct store deliveries (fresh).
        for s in DSD_SKUS:
            p = BY_SKU[s]
            if s == "MILK-TONED-500ML":
                base = milk_std["weekend" if weekend else "weekday"]  # type: ignore[index]
                units = round(base * milk_factor)
            else:
                units = round(p.daily_mean * fresh_factor * param("dow_fresh")[wd])  # type: ignore[index]
            use_by = di + (p.shelf_life_days or 1) - 1
            stock[s].batches.append([use_by, units])
            stock[s].shelf += units
            stock[s].book += units
            w.dsd.append({"delivery_ts": _ts(day, 5, 30), "route": "R-07" if p.family in ("milk", "curd") else "R-12",
                          "sku": s, "units": units, "crates": math.ceil(units / p.case_units),
                          "use_by": (day + timedelta(days=(p.shelf_life_days or 1) - 1)).isoformat()})

        # Start-of-month full count, before opening.
        if day == spec.STORY_START:
            do_count(di, 5, 45, list(BY_SKU), "scheduled full count", thorough=False)

        # DC truck. Orders placed last night arrive this morning.
        arriving = [o for o in pipeline if o["arrive_di"] == di]
        ship = None
        late = False
        pending_skus: set[str] = set()
        if arriving:
            late = bool(dr.truck_late[di] < float(param("truck_late_rate")))  # type: ignore[arg-type]
            minute = 6 * 60 + (int(dr.truck_late_min[di]) if late else int(dr.truck_early_min[di]))
            ordered = sorted(arriving, key=lambda o: DC_SKUS.index(o["sku"]))
            dc_check = scn.dc_check if live else "none"
            # The planted mis-pick: on the first truck from 22 June that carries 5 kg atta, the
            # picker takes the cases from the neighbouring 1 kg slot.
            mispick = None
            if not flags["wrong_pallet_done"] and day >= date(2026, 6, 22):
                mispick = next((o for o in ordered if o["sku"] == HERO_SKU), None)
                flags["wrong_pallet_done"] = mispick is not None
            wrong_sku = "ATTA-WW-1KG"

            # Picking: cases per line after any short pick, and the pallet each line goes on.
            plan = []
            cases_on_pallet = 0
            sscc = None
            for line_no, o in enumerate(ordered, start=1):
                s = o["sku"]
                cases = o["cases"]
                short = dr.dc_short[s][di] < float(param("dc_short_rate"))  # type: ignore[arg-type]
                if short:
                    cases = max(1, int(cases * 0.75))
                if sscc is None or cases_on_pallet + cases > 40:
                    serial["sscc"] += 1
                    sscc = sscc18(serial["sscc"])
                    cases_on_pallet = 0
                cases_on_pallet += cases
                picked = wrong_sku if (o is mispick and dc_check != "pick_scan") else s
                plan.append({"o": o, "line": line_no, "cases": cases, "short": short, "sscc": sscc, "picked": picked})

            # Dispatch: the scale compares each pallet with the weight its shipping notice implies.
            weights: dict[str, dict[str, float]] = {}
            for ln in plan:
                wt = weights.setdefault(ln["sscc"], {"notice": PALLET_TARE_KG, "actual": PALLET_TARE_KG, "cases": 0})
                wt["notice"] += ln["cases"] * CASE_KG[ln["o"]["sku"]]
                wt["actual"] += ln["cases"] * CASE_KG[ln["picked"]]
                wt["cases"] += ln["cases"]
            tol = float(param("check_weigh_tolerance"))  # type: ignore[arg-type]
            flagged = {k for k, v in weights.items()
                       if dc_check == "check_weigh" and abs(v["actual"] - v["notice"]) > tol * v["notice"]}
            delay = int(param("check_weigh_repick_minutes")) if flagged else 0  # type: ignore[arg-type]
            minute += delay
            arrived = datetime.combine(day, time(minute // 60, minute % 60))
            dispatched = datetime.combine(day, time(4, 30)) + timedelta(minutes=delay)
            ship = {"shipment_id": f"SHP-{day:%y%m%d}", "from_gln": spec.DC["gln"], "to_gln": spec.STORE["gln"],
                    "dispatched_ts": dispatched.isoformat(timespec="minutes"), "slot_start": _ts(day, 6, 0),
                    "slot_end": _ts(day, 6, 30), "arrived_ts": arrived.isoformat(timespec="minutes"),
                    "vehicle": "TRK-07", "pallets": len(weights), "arrival_minute": minute}
            w.shipments.append(ship)
            for k, v in weights.items():
                weighed = dc_check == "check_weigh"
                w.pallets.append({"sscc": k, "shipment_id": ship["shipment_id"], "cases": int(v["cases"]),
                                  "notice_kg": round(v["notice"], 1),
                                  "scale_kg": round(v["notice"], 1) if weighed else None,
                                  "weight_check": ("flagged, line re-picked, passed on re-weigh" if k in flagged
                                                   else "passed" if weighed else "not weighed")})

            for ln in plan:
                o, line_no, cases, sscc = ln["o"], ln["line"], ln["cases"], ln["sscc"]
                s = o["sku"]
                p = BY_SKU[s]
                pick_ts = (datetime.combine(day, time(3, 0)) + timedelta(minutes=8 * (line_no - 1))).isoformat(
                    timespec="minutes")
                if ln["short"]:
                    event(ship["arrived_ts"], s, "dc_short_ship", (o["cases"] - cases) * p.case_units, False,
                          f"DC shipped {cases} of {o['cases']} cases.")
                actual_sku, actual_units = s, cases * p.case_units
                if o is mispick:
                    wrong_units = cases * BY_SKU[wrong_sku].case_units
                    if dc_check == "pick_scan":
                        event(pick_ts, s, "pick_scan_caught_wrong_item", cases * p.case_units, True,
                              f"Case scan at pick rejected a {wrong_sku} case on the {s} line; the picker took "
                              f"{cases} cases from slot {DC_SLOTS[s]} instead.")
                    elif sscc in flagged:
                        wt = weights[sscc]
                        event((dispatched - timedelta(minutes=delay)).isoformat(timespec="minutes"), s,
                              "check_weigh_caught_wrong_item", cases * p.case_units, True,
                              f"Dispatch scale: pallet {sscc} weighed {wt['actual']:.0f} kg against "
                              f"{wt['notice']:.0f} kg from its shipping notice. The {s} line held {wrong_sku} cases "
                              f"and was re-picked; the truck left {delay} minutes late.")
                    else:
                        actual_sku, actual_units = wrong_sku, wrong_units
                        event(ship["arrived_ts"], s, "wrong_pallet", cases * p.case_units, True,
                              f"Line picked from the adjacent 1 kg slot: {cases} cases of {actual_sku} "
                              f"({actual_units} units) shipped as {cases} cases of {s}.")
                w.picks.append({"pick_ts": pick_ts, "order_id": o["order_id"], "shipment_id": ship["shipment_id"],
                                "line": line_no, "sku": s, "slot": DC_SLOTS[s], "cases_ordered": int(o["cases"]),
                                "cases_confirmed": int(cases),
                                "confirmed_by": "case barcode scan" if dc_check == "pick_scan" else "slot label scan"})
                w.asn_lines.append({"shipment_id": ship["shipment_id"], "sscc": sscc, "line": line_no, "sku": s,
                                    "gtin": p.gtin, "cases": int(cases), "units": int(cases * p.case_units),
                                    "order_id": o["order_id"]})
                w.pallets_truth.append({"sscc": sscc, "line": line_no, "sku_actual": actual_sku,
                                        "units_actual": int(actual_units), "shipment_id": ship["shipment_id"]})
            pipeline = [o for o in pipeline if o["arrive_di"] != di]
            pending_skus = {o["sku"] for o in arriving}
            if minute < 7 * 60:
                receive(di, ship)
                ship = None  # received

        # 08:00 targeted counts flagged by last night's alert.
        todays_alerts = [s for (d_, s) in alert_counts if d_ == di]

        for hi, hour in enumerate(OPEN_HOURS):
            # Refill rounds at 07:00 and 15:00 (before any late delivery this hour).
            if hour in (7, 15):
                rnd = 0 if hour == 7 else 1
                for s in DC_SKUS:
                    st = stock[s]
                    p_skip = skip["with_routine"]  # type: ignore[index]
                    if not discipline:
                        p_skip = skip["weekend" if weekend else "weekday"]  # type: ignore[index]
                        if month_week == 0:
                            p_skip += skip["month_start_extra"]  # type: ignore[index]
                    if dr.restock[s][di, rnd] >= p_skip:
                        refill(s)
                    if st.lost > 0 and dr.find[s][di, rnd] < find_rate:
                        st.back += st.lost
                        event(_ts(day, hour), s, "misplaced_found", st.lost, False, "Found during a refill round.")
                        st.lost = 0
                        refill(s)
            if ship is not None and ship["arrival_minute"] < (hour + 1) * 60:
                receive(di, ship)
                ship = None
                for s in DC_SKUS:
                    refill(s)
            if hour == 8 and todays_alerts:
                do_count(di, 8, 0, todays_alerts, "low-sales alert", thorough=True)
                for s in todays_alerts:
                    refill(s)
                    event(_ts(day, 8), s, "alert_count", 0, False,
                          f"Count after {alert_days} day(s) of low sales with stock on the books.")
            for s in gap_checks.pop((di, hi), []):
                do_count(di, hour, 0, [s], "gap detector", thorough=True)
                refill(s)
                event(_ts(day, hour), s, "gap_check", 0, False,
                      "Shelf and backroom checked after the gap detector flagged no sales with stock on the books.")
                gap_run[s] = 0.0
                gap_flagged.discard(s)
            # Planted store events.
            if day == date(2026, 6, 13) and hour == 10 and stock[HERO_SKU].lost_story > 0:
                st = stock[HERO_SKU]
                event(_ts(day, 10), HERO_SKU, "found_in_backroom", st.lost_story, True,
                      "Staff restacking rice find the missing cases and fill the shelf.")
                st.back += st.lost_story
                st.lost_story = 0
                refill(HERO_SKU)
            if day == date(2026, 6, 26) and hour == 9:
                st = stock[HERO_SKU]
                recently_counted = any(c["sku"] == HERO_SKU and c["count_ts"] >= DAYS[di - 3].isoformat()
                                       for c in w.counts)
                if (daily[HERO_SKU]["scanned"][di - 1] == 0 and st.shelf == 0 and st.book > 0
                        and not recently_counted):
                    event(_ts(day, 9), HERO_SKU, "complaint_count", 0, True,
                          "After customer complaints, the store manager orders a count of the atta bay.")
                    do_count(di, 9, 0, FAMILIES["atta"], "manager request after complaints", thorough=True)
                    for s in FAMILIES["atta"]:
                        refill(s)
            # Shelf audit at 11:00 on audit days.
            if hour == 11 and day.strftime("%a") in param("audit_days") and di >= STORY_FIRST:  # type: ignore[operator]
                for s in BY_SKU:
                    w.audits.append({"audit_ts": _ts(day, 11), "sku": s,
                                     "status": "on shelf" if stock[s].shelf > 0 else "empty"})

            # Customers.
            for p in PRODUCTS:
                s = p.sku
                st = stock[s]
                n = int(dr.demand[s][di, hi]) + carry.pop((s, di, hi), 0)
                u = dr.units[s][di][hi]
                n = min(n, len(u))
                start_empty = st.shelf == 0
                sold = lost = 0
                for i in range(n):
                    ui = u[i]
                    if st.shelf > 0:
                        st.shelf -= 1
                        if p.flow == "DSD":
                            st.batches.sort()
                            pick = -1 if ui[3] < date_picking else 0
                            st.batches[pick][1] -= 1
                            if st.batches[pick][1] == 0:
                                st.batches.pop(pick)
                        scanned = s
                        fam = FAMILIES[p.family]
                        if len(fam) > 1 and ui[0] < mis_rate:
                            others = [x for x in fam if x != s]
                            scanned = others[int(ui[1] * len(others))]
                        stock[scanned].book -= 1
                        scanned_hourly[scanned][di, hi] += 1
                        daily[scanned]["scanned"][di] += 1
                        daily[scanned]["revenue"][di] += BY_SKU[scanned].price
                        sold += 1
                        if record_bills:
                            _bill_line(w, dr, di, hi, ui[4], s, scanned)
                        continue
                    lost += 1
                    r = resp_keys[int(np.searchsorted(resp_cum, ui[2], side="right"))]
                    if r == "other_pack":
                        cands = [x for x in FAMILIES[p.family] if x != s and stock[x].shelf > 0]
                        if not cands:
                            r = "elsewhere"
                        else:
                            sub = cands[int(ui[3] * len(cands))]
                            ss = stock[sub]
                            ss.shelf -= 1
                            if BY_SKU[sub].flow == "DSD":
                                ss.batches.sort()
                                ss.batches[0][1] -= 1
                                if ss.batches[0][1] == 0:
                                    ss.batches.pop(0)
                            ss.book -= 1
                            scanned_hourly[sub][di, hi] += 1
                            daily[sub]["scanned"][di] += 1
                            daily[sub]["revenue"][di] += BY_SKU[sub].price
                            daily[sub]["subs_in"][di] += 1
                            hourly[sub]["subs_in"][di, hi] += 1
                            hourly[sub]["sold"][di, hi] += 1
                            daily[sub]["sold"][di] += 1
                            if record_bills:
                                _bill_line(w, dr, di, hi, ui[4], sub, sub)
                    if r == "delay" and di + 1 < N_DAYS:
                        carry[(s, di + 1, hi)] = carry.get((s, di + 1, hi), 0) + 1
                    daily[s][r][di] += 1
                    hourly[s][r][di, hi] += 1
                hourly[s]["demand"][di, hi] += n
                hourly[s]["sold"][di, hi] += sold
                hourly[s]["lost"][di, hi] += lost
                daily[s]["demand"][di] += n
                daily[s]["sold"][di] += sold
                daily[s]["lost"][di] += lost
                if start_empty:
                    frac = 1.0
                elif lost and n:
                    frac = lost / n
                else:
                    frac = 0.0
                hourly[s]["empty"][di, hi] = frac
                if frac > 0:
                    pending = late and ship is not None and s in pending_skus
                    causes[s][di][hi] = _cause(s, st, freeze_s.get(s, 0.0), pending, di, w)
            for s in BY_SKU:
                st = stock[s]
                hourly[s]["shelf"][di, hi] = st.shelf
                hourly[s]["back"][di, hi] = st.back
                hourly[s]["lost_stock"][di, hi] = st.lost + st.lost_story
                hourly[s]["book"][di, hi] = st.book

            # Gap detector, on what the tills recorded this hour.
            if gap_limit and live:
                for s in DC_SKUS:
                    if scanned_hourly[s][di, hi] > 0 or stock[s].book <= 0:
                        gap_run[s] = 0.0
                        gap_flagged.discard(s)
                        continue
                    gap_run[s] += expected_sales(gap_rate[s], daily[s]["forecast"][di - 1], weekend, hi)
                    if s not in gap_flagged and gap_run[s] > gap_limit:
                        gap_flagged.add(s)
                        # Someone checks within the next open hour: from the hour after next, or 07:00 tomorrow.
                        nxt = (di, hi + 2) if hi + 2 < H else (di + 1, 0)
                        if nxt[0] < N_DAYS:
                            gap_checks.setdefault(nxt, []).append(s)
                        event(_ts(day, hour + 1), s, "gap_flag", 0, False,
                              f"No sales while the books show {stock[s].book}; {gap_run[s]:.1f} sales expected "
                              f"since the last one (chance of none: {math.exp(-gap_run[s]):.4f}).")

        # Close: damage, theft, expiry.
        for s in DC_SKUS:
            st = stock[s]
            n = int(dr.damage[s][di])
            from_back = min(n, st.back)
            from_shelf = min(n - from_back, st.shelf)
            st.back -= from_back
            st.shelf -= from_shelf
            damaged = from_back + from_shelf
            rec = min(int(dr.damage_recorded[s][di]), damaged)
            st.book -= rec
            if rec:
                w.write_offs.append({"date": day.isoformat(), "sku": s, "units": rec, "reason": "damaged"})
            t = int(dr.theft[s][di])
            take = min(t, st.shelf)
            st.shelf -= take
        for s in DSD_SKUS:
            st = stock[s]
            expired = sum(b[1] for b in st.batches if b[0] <= di)
            st.batches = [b for b in st.batches if b[0] > di]
            if expired:
                st.shelf -= expired
                st.book -= expired
                w.write_offs.append({"date": day.isoformat(), "sku": s, "units": int(expired), "reason": "expired"})
            n = min(int(dr.fresh_damage[s][di]), st.shelf)
            rec = min(int(dr.fresh_damage_recorded[s][di]), n)
            left = n
            for b in sorted(st.batches):
                take = min(left, b[1])
                b[1] -= take
                left -= take
            st.batches = [b for b in st.batches if b[1] > 0]
            st.shelf -= n
            st.book -= rec
            if rec:
                w.write_offs.append({"date": day.isoformat(), "sku": s, "units": rec, "reason": "damaged"})

        for s in BY_SKU:
            daily[s]["empty_hours"][di] = hourly[s]["empty"][di].sum()
            daily[s]["book_close"][di] = stock[s].book
            daily[s]["physical_close"][di] = stock[s].physical()

        # 22:00 low-sales alert: sales far below forecast while the books show stock.
        if alert_days and di + 1 < N_DAYS:
            n_days = alert_days
            for s in DC_SKUS:
                f = daily[s]["forecast"][di - 1]
                recent = daily[s]["scanned"][di - n_days + 1:di + 1]
                if f > 0 and bool((recent < alert_share * f).all()) and stock[s].book >= f:
                    alert_counts.add((di + 1, s))
                    event(_ts(day, 22), s, "low_sales_alert", 0, False,
                          f"{n_days} day(s) with sales under {alert_share:.0%} of forecast while the books show "
                          f"{stock[s].book} on hand.")

        # 22:00 forecast and reorder for DC items.
        lo = max(0, di - window + 1)
        orders_today = []
        for s in DC_SKUS:
            p = BY_SKU[s]
            hist = daily[s]["scanned"][lo:di + 1]
            f = float(hist.mean())
            sig = float(hist.std(ddof=0))
            rop = math.ceil(f * lead + z * sig * math.sqrt(lead))
            upto = rop + math.ceil(f * cover)
            on_order = sum(o["units"] for o in pipeline if o["sku"] == s)
            ip = stock[s].book + on_order
            qty = 0
            if ip <= rop:
                qty = math.ceil((upto - ip) / p.case_units) * p.case_units
            freeze_s[s] = rop
            daily[s]["forecast"][di] = f
            daily[s]["sigma"][di] = sig
            daily[s]["reorder_point"][di] = rop
            daily[s]["order_up_to"][di] = upto
            daily[s]["ordered"][di] = qty
            w.forecasts.append({"date": day.isoformat(), "sku": s, "forecast_units_per_day": round(f, 2),
                                "sigma": round(sig, 2), "reorder_point": rop, "order_up_to": upto,
                                "book_on_hand": int(stock[s].book), "on_order": int(on_order),
                                "ordered_units": int(qty), "method": "28-day mean of recorded sales"})
            if qty > 0 and di + lead < N_DAYS:
                orders_today.append(s)
                o = {"order_id": f"SO-{day:%y%m%d}", "sku": s, "units": qty, "cases": qty // p.case_units,
                     "created_ts": _ts(day, 22), "arrive_di": di + lead}
                pipeline.append(o)
                w.orders.append({k: v for k, v in o.items() if k != "arrive_di"} | {"reason": "auto"})

        if day == spec.END:
            do_count(di, 22, 30, list(BY_SKU), "scheduled full count", thorough=False)

    _dc_corrections(w)
    w.daily = daily
    w.hourly = hourly
    return w


def _dc_corrections(w: World) -> None:
    """DC stock corrections after the planted mis-pick.

    The mis-pick leaves the DC's system wrong in both slots: it thinks 16 cases of 5 kg left and
    none of 1 kg. If the store reports the wrong pallet, the DC fixes both slots that morning
    against the claim. If nobody does, each slot is corrected when its own discrepancy surfaces,
    days apart, as an unexplained count variance.
    """
    wrong = next((e for e in w.events if e["kind"] == "wrong_pallet"), None)
    if not wrong:
        return
    ship = next(s for s in w.shipments if s["arrived_ts"] == wrong["ts"])
    line = next(a for a in w.asn_lines if a["shipment_id"] == ship["shipment_id"] and a["sku"] == wrong["sku"])
    took = next(t["sku_actual"] for t in w.pallets_truth if t["sscc"] == line["sscc"] and t["line"] == line["line"])
    cases = line["cases"]
    claim = next((c for c in w.claims if c["shipment_id"] == ship["shipment_id"] and c["line"] == line["line"]), None)
    if claim:
        ts = f"{claim['claim_ts'][:10]}T10:30"
        rows = [(ts, took, -cases, f"receiving claim {claim['claim_id']}"),
                (ts, line["sku"], cases, f"receiving claim {claim['claim_id']}")]
    else:
        when = {e.key: e.when for e in spec.STORY_EVENTS}
        rows = [(when["dc_short_pick"], took, -cases, "short pick: slot count variance"),
                (when["dc_cycle_count"], line["sku"], cases, "cycle count variance")]
        w.events.append({"ts": when["dc_short_pick"], "sku": took, "kind": "dc_short_pick",
                         "units": cases * BY_SKU[took].case_units, "planted": True, "scenario": w.scenario.key,
                         "detail": f"A DC picker finds slot {DC_SLOTS[took]} {cases} cases short of the system; "
                                   f"the slot is counted and adjusted down. Nothing links it to {ship['shipment_id']}."})
        w.events.append({"ts": when["dc_cycle_count"], "sku": line["sku"], "kind": "dc_cycle_count",
                         "units": cases * BY_SKU[line["sku"]].case_units, "planted": True, "scenario": w.scenario.key,
                         "detail": f"The weekly cycle count finds {cases} more cases in slot {DC_SLOTS[line['sku']]} "
                                   f"than the system shows, and adjusts it up."})
    for ts, sku, d_cases, reason in rows:
        w.dc_adjustments.append({"adjusted_ts": ts, "sku": sku, "slot": DC_SLOTS[sku], "cases": int(d_cases),
                                 "units": int(d_cases * BY_SKU[sku].case_units),
                                 "value_at_cost_inr": round(d_cases * BY_SKU[sku].case_units * BY_SKU[sku].cost, 2),
                                 "reason": reason})


def gap_profiles(scanned_hourly: dict[str, np.ndarray], n_days: int) -> dict[str, dict]:
    """Each warehouse item's usual sales pattern, learned from the tills' records of the first n_days.

    The share of a day's sales in each open hour (pooled over the days, lightly smoothed) and how
    much weekdays and weekends sell against the average day. Uses only what the tills recorded.
    """
    weekend = np.array([DAYS[i].weekday() >= 5 for i in range(n_days)])
    out = {}
    for s in DC_SKUS:
        hist = scanned_hourly[s][:n_days]
        prof = (hist.sum(axis=0) + 0.5) / (hist.sum() + 0.5 * H)
        per_day = hist.sum(axis=1)
        mean = float(per_day.mean()) or 1.0
        out[s] = {"profile": prof, "weekday": float(per_day[~weekend].mean()) / mean,
                  "weekend": float(per_day[weekend].mean()) / mean}
    return out


def expected_sales(rate: dict, forecast: float, weekend: bool, hi: int) -> float:
    """Sales the gap detector expects in open hour hi, from last night's forecast and the item's pattern."""
    return float(forecast) * rate["weekend" if weekend else "weekday"] * float(rate["profile"][hi])


def imputed_for_empty_hours(s: str, scanned_hourly: dict[str, np.ndarray], daily: dict, lo: int, di: int) -> np.ndarray:
    """Expected sales for runs of zero-sale hours long enough to mean an empty shelf.

    Uses only what the store's systems can see: hourly scanned sales and the item's usual
    hourly shape, scaled by the median of recent days that had sales. A run of three or
    more zero hours that should have sold at least two units is treated as an empty shelf.
    """
    shape = np.array(spec.HOURLY[BY_SKU[s].profile])
    out = np.zeros(di - lo + 1)
    for j, dd in enumerate(range(lo, di + 1)):
        prev = daily[s]["scanned"][max(0, dd - 28):dd]
        with_sales = prev[prev > 0]
        if not len(with_sales):
            continue
        expect = shape * float(np.median(with_sales))
        row = scanned_hourly[s][dd]
        run: list[int] = []
        for hi in range(H + 1):
            if hi < H and row[hi] == 0:
                run.append(hi)
                continue
            if len(run) >= 3 and expect[run].sum() >= 2:
                out[j] += expect[run].sum()
            run = []
    return out


def _cause(s: str, st: Stock, rop: float, truck_pending: bool, di: int, w: World) -> str:
    if st.back > 0:
        return "shelf_refill"
    if st.lost > 0 or st.lost_story > 0:
        return "misplaced"
    if BY_SKU[s].flow == "DC":
        if truck_pending:
            return "late_truck"
        if st.book > rop:
            if st.upstream_phantom > 0 and st.book - st.upstream_phantom <= rop:
                return "wrong_pallet"
            return "record_error"
        day = DAYS[di]
        if any(e["kind"] == "dc_short_ship" and e["sku"] == s and e["ts"].startswith(day.isoformat())
               for e in w.events):
            return "dc_short"
    return "ordering"


def _bill_line(w: World, dr: Draws, di: int, hi: int, u: float, actual: str, scanned: str) -> None:
    n = int(dr.arrivals[di, hi])
    k = min(n - 1, int(u * n))
    day = DAYS[di]
    bill_id = f"B{day:%y%m%d}-{hi:02d}{k:04d}"
    w.bill_lines.append({"bill_id": bill_id, "sku_scanned": scanned, "sku_actual": actual,
                         "unit_price": BY_SKU[scanned].price})


def build_bills(w: World, dr: Draws) -> tuple[list[dict], list[dict]]:
    """Group recorded lines into bills with their other merchandise and tender."""
    tender_mix = param("tender_mix")
    keys = list(tender_mix)  # type: ignore[arg-type]
    cum = np.cumsum([tender_mix[k] for k in keys])  # type: ignore[index]
    lines_by_bill: dict[str, list[dict]] = {}
    for ln in w.bill_lines:
        lines_by_bill.setdefault(ln["bill_id"], []).append(ln)
    bills: list[dict] = []
    lines: list[dict] = []
    for di, day in enumerate(DAYS):
        for hi, hour in enumerate(OPEN_HOURS):
            n = int(dr.arrivals[di, hi])
            for k in range(n):
                bill_id = f"B{day:%y%m%d}-{hi:02d}{k:04d}"
                group: dict[str, list[dict]] = {}
                for ln in lines_by_bill.get(bill_id, []):
                    group.setdefault(ln["sku_scanned"] + "|" + ln["sku_actual"], []).append(ln)
                amount = float(dr.bill_other[di][hi][k])
                for no, (key, grp) in enumerate(sorted(group.items()), start=1):
                    scanned, actual = key.split("|")
                    qty = len(grp)
                    price = BY_SKU[scanned].price
                    amount += qty * price
                    lines.append({"bill_id": bill_id, "line": no, "gtin_scanned": BY_SKU[scanned].gtin,
                                  "sku_scanned": scanned, "qty": qty, "unit_price": price,
                                  "line_amount": round(qty * price, 2), "sku_actual": actual})
                tender = keys[int(np.searchsorted(cum, dr.bill_tender[di][hi][k], side="right"))]
                bills.append({"bill_id": bill_id, "store_gln": spec.STORE["gln"],
                              "bill_ts": _ts(day, hour, int(dr.bill_minute[di][hi][k])),
                              "tender": tender, "amount_inr": round(amount, 2),
                              "other_merchandise_inr": float(dr.bill_other[di][hi][k])})
    return bills, lines
