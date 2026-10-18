"""Pump maker (Kestrel Pump Works): lots, engineering changes, builds, genealogy, tests, shipments.

Operator-side generators call build_pump / build_esp_string on demand so that every unit an operator
installs has a real birth certificate at the maker. bulk_production() then fills in everybody else.
"""
from __future__ import annotations

from datetime import date, timedelta

from .model import World
from .spec import (
    ECO_BEARING,
    ECO_BEARING_DATE,
    ECO_ELASTOMER,
    ECO_ELASTOMER_DATE,
    ESP_OPERATORS,
    FACTORY_START,
    LOT_BEARING,
    LOT_BEARING_CUSTOMERS,
    LOT_BEARING_PUMPS,
    LOT_ELASTOMER,
    LOT_ELASTOMER_SECTIONS,
    OEM,
    OPERATOR,
    ORGS,
    PUMP_CUSTOMERS,
    SEAL_CUTOFF,
)

BEARING_PRESS_FIT_KN = 18.5  # original supplier, kN
ALT_PRESS_FIT_FACTOR = 0.88  # alternate supplier sits 12% lower (still above the 14 kN minimum)
PRESS_FIT_MIN_KN = 14.0


def setup_orgs_and_customers(w: World) -> None:
    for oid, (name, kind) in ORGS.items():
        w.orgs[oid] = {"id": oid, "name": name, "kind": kind}
    w.customers["cust:aurelia"] = {"id": "cust:aurelia", "no": "100234", "name": "Aurelia Energy", "org": OPERATOR}
    for i, n in enumerate(PUMP_CUSTOMERS):
        cid = f"cust:p{i + 1:02d}"
        w.customers[cid] = {"id": cid, "no": str(100300 + 7 * i), "name": n, "org": f"org:{cid[5:]}"}
        w.orgs[f"org:{cid[5:]}"] = {"id": f"org:{cid[5:]}", "name": n, "kind": "operator"}
    for i, n in enumerate(ESP_OPERATORS):
        cid = f"cust:e{i + 1:02d}"
        w.customers[cid] = {"id": cid, "no": str(100500 + 11 * i), "name": n, "org": f"org:{cid[5:]}"}
        w.orgs[f"org:{cid[5:]}"] = {"id": f"org:{cid[5:]}", "name": n, "kind": "operator"}


def _serial(w: World, prefix: str, built: date, taken: set[str]) -> str:
    yy = built.year % 100
    while True:
        s = f"{prefix}-{yy:02d}-{int(w.rng.integers(1, 1300)):04d}"
        if s not in taken:
            taken.add(s)
            return s


def new_lot(w: World, lot_id: str, material: str, supplier: str, received: date, qty: int, eco: str | None = None,
            po: str | None = None) -> dict:
    lot = {"id": lot_id, "material": material, "supplier": supplier, "received": received, "qty": qty,
           "eco": eco, "po": po or f"PO-{received.year}-{int(w.rng.integers(10000, 99999))}", "used": 0}
    w.lots[lot_id] = lot
    return lot


def setup_changes_and_lots(w: World) -> None:
    """Engineering changes (PLM) and the lots that exist before any pump is built."""
    # 56 ordinary changes: standard route, qualification done
    topics = [("bearing housing", "casting tolerance"), ("impeller", "balance grade"), ("wear ring", "clearance"),
              ("coupling guard", "material"), ("baseplate", "weld detail"), ("gland plate", "bolt pattern"),
              ("lube oil ring", "dimension"), ("nameplate", "wording"), ("paint spec", "primer"),
              ("shaft sleeve", "coating"), ("motor lead", "gland"), ("check valve", "spring rate")]
    for i in range(56):
        yy = 21 + i * 6 // 56
        no = f"ECO-{yy}-{i * 17 % 900 + 100:04d}"
        if no in w.ecos:
            continue
        part, what = topics[i % len(topics)]
        approved = date(2000 + yy, int(w.rng.integers(1, 13)), int(w.rng.integers(1, 28)))
        w.ecos[no] = {"id": no, "title": f"{part.capitalize()}: {what}", "part": part, "route": "standard",
                      "waived": False, "approved": approved, "supplier_from": None, "supplier_to": None,
                      "status": "released", "summary": f"Change {what} on {part}; qualification completed."}
    # the four expedited, test-waived changes
    w.ecos[ECO_BEARING] = {"id": ECO_BEARING, "title": "Bearing set 650: alternate supplier", "part": "bearing set 650",
                           "route": "expedited", "waived": True, "approved": ECO_BEARING_DATE,
                           "supplier_from": "org:halden", "supplier_to": "org:orlo", "status": "released",
                           "summary": "Alternate bearing supplier during a shortage. Expedited alternate-source route; qualification test waived."}
    w.ecos["ECO-25-0112"] = {"id": "ECO-25-0112", "title": "Mechanical seal face material", "part": "mechanical seal faces",
                             "route": "expedited", "waived": True, "approved": date(2025, 4, 15),
                             "supplier_from": "org:norvik", "supplier_to": "org:norvik", "status": "released",
                             "summary": "Seal face material changed for availability. Expedited route; qualification test waived."}
    w.ecos[ECO_ELASTOMER] = {"id": ECO_ELASTOMER, "title": "Seal elastomer: alternate compound", "part": "elastomer compound",
                             "route": "expedited", "waived": True, "approved": ECO_ELASTOMER_DATE,
                             "supplier_from": "org:veyron", "supplier_to": "org:tanis", "status": "released",
                             "summary": "Alternate elastomer compound during a shortage. Expedited alternate-source route; qualification test waived."}
    w.ecos["ECO-26-0057"] = {"id": "ECO-26-0057", "title": "Motor lead cable insulation", "part": "motor lead cable",
                             "route": "expedited", "waived": True, "approved": date(2026, 2, 9),
                             "supplier_from": "org:norvik", "supplier_to": "org:norvik", "status": "released",
                             "summary": "Cable insulation changed for availability. Expedited route; qualification test waived."}
    # original-supplier lots, quarterly, for each part; the alternates are created on demand
    for m, mat in (("650", "bearing set 650"), ("400", "bearing set 400"), ("150", "bearing set 150"), ("300", "bearing set 300")):
        q = FACTORY_START
        n = 0
        while q < date(2026, 4, 1):
            n += 1
            new_lot(w, f"B-{q.year % 100:02d}-{m}{n:02d}", mat, "org:halden", q, 60)
            q += timedelta(days=75)
    q = FACTORY_START
    n = 0
    while q < date(2026, 4, 1):
        n += 1
        new_lot(w, f"S-{q.year % 100:02d}-{n:03d}", "mechanical seal faces", "org:norvik", q, 200)
        q += timedelta(days=90)
    q = FACTORY_START
    while q < SEAL_CUTOFF:
        new_lot(w, f"E-{q.year % 100:02d}-{(q.month - 1) // 3 + 1}{q.month:02d}", "elastomer compound", "org:veyron", q, 120)
        q += timedelta(days=100)
    new_lot(w, LOT_BEARING, "bearing set 650", "org:orlo", date(2024, 11, 14), LOT_BEARING_PUMPS, ECO_BEARING)
    new_lot(w, LOT_ELASTOMER, "elastomer compound", "org:tanis", date(2025, 8, 4), LOT_ELASTOMER_SECTIONS, ECO_ELASTOMER)


def _lot_for(w: World, material: str, on: date, prefix: str) -> str:
    cands = [l for l in w.lots.values() if l["material"] == material and l["supplier"] in ("org:halden", "org:veyron", "org:norvik")
             and l["received"] <= on]
    return max(cands, key=lambda l: l["received"])["id"]


def build_pump(w: World, serial: str | None, model: str, built: date, customer: str, bearing_lot: str | None = None,
               shipped: date | None = None, taken: set[str] | None = None) -> str:
    taken = taken if taken is not None else w.answer.setdefault("_serials", set())
    serial = serial or _serial(w, "OEM", built, taken)
    taken.add(serial)
    size = model.split("-")[-1]
    blot = bearing_lot or _lot_for(w, f"bearing set {size}", built, "B")
    slot = _lot_for(w, "mechanical seal faces", built, "S")
    w.lots[blot]["used"] += 1
    uid = f"unit:{serial}"
    w.units[uid] = {"id": uid, "serial": serial, "kind": "pump", "model": model, "maker": OEM, "built": built,
                    "customer": customer, "lots": [blot, slot], "parent": None}
    wo = f"WO-{built.year}-{int(w.rng.integers(10000, 99999))}"
    w.builds.append({"serial": serial, "model": model, "built": built, "wo": wo, "line": f"L{int(w.rng.integers(1, 4))}"})
    w.genealogy.append({"serial": serial, "kind": "bearing set", "lot": blot})
    w.genealogy.append({"serial": serial, "kind": "mechanical seal faces", "lot": slot})
    base = BEARING_PRESS_FIT_KN * (ALT_PRESS_FIT_FACTOR if w.lots[blot]["supplier"] == "org:orlo" else 1.0)
    w.tests.append({"serial": serial, "kind": "performance", "value": round(float(w.rng.normal(98.5, 0.8)), 1), "unit": "% of rated head", "passed": True, "on": built + timedelta(days=3)})
    w.tests.append({"serial": serial, "kind": "leak", "value": 0.0, "unit": "drops/min", "passed": True, "on": built + timedelta(days=3)})
    w.tests.append({"serial": serial, "kind": "press_fit_force", "value": round(float(w.rng.normal(base, 0.35)), 2), "unit": "kN", "passed": True, "on": built + timedelta(days=1)})
    ship = shipped or built + timedelta(days=int(w.rng.integers(14, 45)))
    w.shipments.append({"serial": serial, "customer": customer, "shipped": ship,
                        "delivery": f"DN-{ship.year}-{int(w.rng.integers(100000, 999999))}"})
    w.units[uid]["shipped"] = ship
    return serial


def build_esp_string(w: World, string_serial: str | None, built: date, customer: str, elastomer_lot: str | None = None,
                     seal_serial: str | None = None, shipped: date | None = None, string_lot_hint: str | None = None) -> tuple[str, str]:
    taken = w.answer.setdefault("_serials", set())
    string_serial = string_serial or _serial(w, "ES", built, taken)
    taken.add(string_serial)
    seal_serial = seal_serial or _serial(w, "SS", built, taken)
    taken.add(seal_serial)
    elot = elastomer_lot or _lot_for(w, "elastomer compound", built, "E")
    flot = _lot_for(w, "mechanical seal faces", built, "S")
    w.lots[elot]["used"] += 1
    sid, ssid = f"unit:{string_serial}", f"unit:{seal_serial}"
    w.units[sid] = {"id": sid, "serial": string_serial, "kind": "esp_string", "model": "KE-ESP-540", "maker": OEM, "built": built,
                    "customer": customer, "lots": [], "parent": None}
    w.units[ssid] = {"id": ssid, "serial": seal_serial, "kind": "esp_seal", "model": "KE-SEAL-540", "maker": OEM, "built": built,
                     "customer": customer, "lots": [elot, flot], "parent": sid}
    for kind, pre in (("pump", "PM"), ("intake", "IN"), ("motor", "MT"), ("cable", "CB")):
        cs = _serial(w, pre, built, taken)
        w.units[f"unit:{cs}"] = {"id": f"unit:{cs}", "serial": cs, "kind": f"esp_{kind}", "model": f"KE-{pre}-540", "maker": OEM,
                                 "built": built, "customer": customer, "lots": [], "parent": sid}
        w.builds.append({"serial": cs, "model": f"KE-{pre}-540", "built": built, "wo": f"WO-{built.year}-{int(w.rng.integers(10000, 99999))}", "line": "E1"})
    w.builds.append({"serial": string_serial, "model": "KE-ESP-540", "built": built, "wo": f"WO-{built.year}-{int(w.rng.integers(10000, 99999))}", "line": "E1"})
    w.builds.append({"serial": seal_serial, "model": "KE-SEAL-540", "built": built, "wo": f"WO-{built.year}-{int(w.rng.integers(10000, 99999))}", "line": "E1"})
    w.genealogy.append({"serial": seal_serial, "kind": "elastomer compound", "lot": elot})
    w.genealogy.append({"serial": seal_serial, "kind": "mechanical seal faces", "lot": flot})
    for u in w.units.values():
        if u.get("parent") == sid and u["serial"] != seal_serial:
            w.genealogy.append({"serial": u["serial"], "kind": "assembly", "lot": "-"})
    w.tests.append({"serial": string_serial, "kind": "performance", "value": round(float(w.rng.normal(99.0, 0.7)), 1), "unit": "% of rated head", "passed": True, "on": built + timedelta(days=2)})
    w.tests.append({"serial": seal_serial, "kind": "leak", "value": 0.0, "unit": "mL/h", "passed": True, "on": built + timedelta(days=2)})
    ship = shipped or built + timedelta(days=int(w.rng.integers(10, 35)))
    w.shipments.append({"serial": string_serial, "customer": customer, "shipped": ship,
                        "delivery": f"DN-{ship.year}-{int(w.rng.integers(100000, 999999))}"})
    for u in w.units.values():
        if u.get("parent") == sid:
            u["shipped"] = ship
    w.units[sid]["shipped"] = ship
    return string_serial, seal_serial


def bulk_production(w: World) -> None:
    """Everything the maker built for other customers (and the remaining lot-B-24-117 / E-25-031 units)."""
    rng = w.rng
    others = [c for c in w.customers if c.startswith("cust:p")]
    # --- lot B-24-117: 38 pumps, 9 customers; six are Aurelia's planted fleet ---
    placed = sum(1 for u in w.units.values() if LOT_BEARING in u["lots"])
    need = LOT_BEARING_PUMPS - placed
    lot_customers = list(rng.choice(others, size=LOT_BEARING_CUSTOMERS - 1, replace=False))
    counts = {c: need // len(lot_customers) for c in lot_customers}
    for c in lot_customers[: need % len(lot_customers)]:
        counts[c] += 1
    span = (date(2025, 3, 12) - date(2024, 11, 20)).days
    for c, n in counts.items():
        for _ in range(n):
            built = date(2024, 11, 20) + timedelta(days=int(rng.integers(0, span)))
            build_pump(w, None, "KP-BB2-650", built, c, bearing_lot=LOT_BEARING)
    # --- ordinary production for other customers 2021 .. Mar 2026 ---
    models = ["KP-BB2-650", "KP-BB2-400", "KP-OH2-150", "KP-VS6-300"]
    probs = [0.34, 0.2, 0.28, 0.18]
    month = date(2021, 1, 1)
    while month < date(2026, 4, 1):
        for _ in range(int(rng.integers(9, 15))):
            built = month + timedelta(days=int(rng.integers(0, 28)))
            m = str(rng.choice(models, p=probs))
            if m == "KP-BB2-650" and date(2024, 11, 20) <= built <= date(2025, 3, 12):
                m = "KP-OH2-150"  # the window's 650 bearing sets all went into lot B-24-117
            build_pump(w, None, m, built, str(rng.choice(others)))
        month = (month.replace(day=1) + timedelta(days=32)).replace(day=1)
    # --- ESP strings: seal sections with lot E-25-031 for the other three operators, plus ordinary builds ---
    esp_ops = [c for c in w.customers if c.startswith("cust:e")]
    placed_e = sum(1 for u in w.units.values() if LOT_ELASTOMER in u["lots"])
    other_sections = LOT_ELASTOMER_SECTIONS - placed_e
    split = [22, 17, other_sections - 39]
    assert sum(split) == other_sections, (split, other_sections)
    for c, n in zip(esp_ops, split):
        for _ in range(n):
            built = date(2025, 8, 5) + timedelta(days=int(rng.integers(0, 190)))
            build_esp_string(w, None, built, c, elastomer_lot=LOT_ELASTOMER)
    month = date(2022, 1, 1)
    while month < date(2025, 8, 1):
        for _ in range(int(rng.integers(3, 7))):
            built = month + timedelta(days=int(rng.integers(0, 28)))
            build_esp_string(w, None, built, str(rng.choice(esp_ops)))
        month = (month.replace(day=1) + timedelta(days=32)).replace(day=1)
    # an earlier customer claim on two lot pumps that was closed as 'no fault found'
    lot_units = [u for u in w.units.values() if LOT_BEARING in u["lots"] and u["customer"] not in ("cust:aurelia",)]
    c0 = lot_units[0]["customer"]
    pair = [u["serial"] for u in lot_units if u["customer"] == c0][:2]
    w.claims.append({"no": "WC-2026-097", "customer": c0, "opened": date(2026, 7, 29), "status": "closed - no fault found",
                     "narrative": "Customer reports bearing noise on two BB2 pumps after about 14 months. Bearings inspected, within tolerance. No fault found.",
                     "serials": pair})
    w.claims.append({"no": "WC-2025-044", "customer": "cust:p03", "opened": date(2025, 5, 12), "status": "closed - accepted",
                     "narrative": "Impeller wear ring clearance out of tolerance on delivery.", "serials": []})
    w.answer["lot_pumps"] = sorted(u["serial"] for u in w.units.values() if LOT_BEARING in u["lots"])
    w.answer["lot_sections"] = sorted(u["serial"] for u in w.units.values() if LOT_ELASTOMER in u["lots"])
