"""Fixed facts and parameters for the India grocery world.

Every behavioural parameter carries its provenance: a published source, or "assumption".
Prices are illustrative for June 2026 and are not quotes for any real brand.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta

from .ids import gln13, gtin13

SUBDOMAIN = "india_grocery"

HISTORY_START = date(2026, 5, 4)  # Monday. Four weeks of history seed the forecasts.
STORY_START = date(2026, 6, 1)  # Monday. The month the posts are about.
END = date(2026, 6, 28)  # Sunday, inclusive.
DAYS = [HISTORY_START + timedelta(days=i) for i in range((END - HISTORY_START).days + 1)]
OPEN_HOURS = list(range(7, 22))  # store open 07:00-22:00, fifteen hourly buckets

STORE = {"id": "ST-014", "gln": gln13(14), "name": "Store 014, Jayanagar (fictional)",
         "city": "Bengaluru", "format": "supermarket, about 8,000 sq ft"}
DC = {"id": "DC-BLR-01", "gln": gln13(1), "name": "Bengaluru DC, Hoskote (fictional)"}
DAIRY = {"id": "DAIRY-01", "gln": gln13(901), "name": "Dairy cooperative plant (fictional)",
         "route": "R-07"}
LOCATIONS = [
    {**STORE, "kind": "store"},
    {**DC, "kind": "distribution centre"},
    {**DAIRY, "kind": "dairy plant"},
]


@dataclass(frozen=True)
class Product:
    sku: str
    item_ref: int
    name: str
    category: str
    family: str  # sizes in one family substitute for each other
    pack: str
    price: float  # INR, illustrative
    cost: float  # INR, illustrative
    case_units: int  # units per case (bale or crate)
    flow: str  # "DC": retailer warehouse; "DSD": direct store delivery
    shelf_capacity: int  # units the shelf face holds (DC items)
    daily_mean: float  # store demand, units per day
    profile: str  # hourly shape: "staples" or "fresh"
    shelf_life_days: int | None = None  # sellable days including the delivery day

    @property
    def gtin(self) -> str:
        return gtin13(self.item_ref)


PRODUCTS: list[Product] = [
    Product("ATTA-WW-5KG", 101, "Whole wheat atta 5 kg", "Staples > Atta and flours", "atta",
            "5 kg", 265.0, 228.0, 4, "DC", 30, 26.0, "staples"),
    Product("ATTA-WW-1KG", 102, "Whole wheat atta 1 kg", "Staples > Atta and flours", "atta",
            "1 kg", 58.0, 49.5, 10, "DC", 40, 30.0, "staples"),
    Product("ATTA-WW-10KG", 103, "Whole wheat atta 10 kg", "Staples > Atta and flours", "atta",
            "10 kg", 499.0, 431.0, 2, "DC", 12, 9.0, "staples"),
    Product("RICE-SM-5KG", 111, "Sona masoori rice 5 kg", "Staples > Rice", "rice",
            "5 kg", 349.0, 301.0, 4, "DC", 24, 22.0, "staples"),
    Product("DAL-TOOR-1KG", 121, "Toor dal 1 kg", "Staples > Dals and pulses", "dal",
            "1 kg", 168.0, 146.0, 10, "DC", 24, 18.0, "staples"),
    Product("OIL-SUN-1L", 131, "Sunflower oil 1 L pouch", "Staples > Edible oils", "oil",
            "1 L", 152.0, 134.0, 10, "DC", 30, 28.0, "staples"),
    Product("SUGAR-1KG", 141, "Sugar 1 kg", "Staples > Sugar and salt", "sugar",
            "1 kg", 48.0, 42.0, 10, "DC", 24, 20.0, "staples"),
    Product("MILK-TONED-500ML", 201, "Toned milk 500 ml pouch", "Dairy > Milk", "milk",
            "500 ml", 26.0, 24.7, 24, "DSD", 0, 320.0, "fresh", 2),
    Product("MILK-FC-500ML", 202, "Full cream milk 500 ml pouch", "Dairy > Milk", "milk",
            "500 ml", 34.0, 32.3, 24, "DSD", 0, 110.0, "fresh", 2),
    Product("CURD-500G", 211, "Curd 500 g pouch", "Dairy > Curd", "curd",
            "500 g", 32.0, 29.5, 24, "DSD", 0, 70.0, "fresh", 4),
    Product("BREAD-WHITE-400G", 301, "White bread 400 g", "Bakery > Bread", "bread",
            "400 g", 45.0, 39.0, 12, "DSD", 0, 60.0, "fresh", 4),
]
BY_SKU = {p.sku: p for p in PRODUCTS}
DC_SKUS = [p.sku for p in PRODUCTS if p.flow == "DC"]
DSD_SKUS = [p.sku for p in PRODUCTS if p.flow == "DSD"]
HERO_SKU = "ATTA-WW-5KG"

# Hourly demand shapes over the fifteen open hours (07:00 ... 21:00). Each sums to 1.
HOURLY = {
    "staples": [0.02, 0.03, 0.04, 0.05, 0.06, 0.06, 0.05, 0.05, 0.06, 0.07, 0.09, 0.11, 0.12, 0.11, 0.08],
    "fresh": [0.14, 0.13, 0.10, 0.07, 0.05, 0.04, 0.04, 0.04, 0.05, 0.06, 0.07, 0.08, 0.06, 0.04, 0.03],
}

# (value, provenance). Provenance is shown in the realism report and the blog's notes.
PARAMS: dict[str, tuple[object, str]] = {
    "dow_staples": ([0.90, 0.88, 0.92, 0.95, 1.02, 1.22, 1.18],
                    "assumption: weekend peak in modern-trade grocery"),
    "dow_fresh": ([0.97, 0.96, 0.97, 0.98, 1.00, 1.07, 1.05], "assumption"),
    "month_start": ([1.30, 1.00, 0.93, 0.90],
                    "assumption: monthly stock-up trips are typical of modern trade (ACNielsen, 2008); "
                    "placing them in days 1-7 of the month is our assumption"),
    "demand_shape_k": (15.0, "assumption: daily demand shock, gamma shape 15 (coefficient of variation about 0.26)"),
    "oos_response": ({"other_pack": 0.19, "other_brand": 0.26, "delay": 0.15, "elsewhere": 0.31, "skip": 0.09},
                     "Gruen, Corsten and Bharadwaj (2002), as charted by Penn (SAEA): substitute about 45%, "
                     "switch stores about 31%, delay about 15%, do not buy about 9%. The split of "
                     "substitution between pack size (19%) and brand (26%) is our assumption"),
    "milk_shelf_life_hours": (48, "Amul Taaza pouch milk: 48 hours from packing under refrigeration below 8 degC"),
    "mis_scan_rate": (0.006, "assumption: share of sized items scanned as a different size of the same item"),
    "restock_skip": ({"weekday": 0.05, "weekend": 0.15, "month_start_extra": 0.03, "with_routine": 0.01},
                     "assumption: shelf refill rounds missed on busy shifts; 1% with a fixed refill routine"),
    "misplace_rate": (0.02, "assumption: share of received case groups put away in the wrong backroom bay"),
    "find_rate_per_round": (0.05, "assumption: chance a refill round stumbles on misplaced stock"),
    "damage_per_day": ({"ATTA-WW-5KG": 0.20, "ATTA-WW-10KG": 0.06, "ATTA-WW-1KG": 0.15, "RICE-SM-5KG": 0.10,
                        "DAL-TOOR-1KG": 0.05, "OIL-SUN-1L": 0.10, "SUGAR-1KG": 0.08},
                       "assumption: torn bags and leaking pouches per day"),
    "damage_recorded_share": (0.3, "assumption: share of damaged units written off in the system"),
    "theft_per_day": ({"OIL-SUN-1L": 0.12, "DAL-TOOR-1KG": 0.04},
                      "assumption: unrecorded theft, units per day"),
    "fresh_damage_per_day": (0.3, "assumption: pouches burst or soiled per fresh SKU per day, half recorded"),
    "fresh_date_picking": (0.35, "assumption: share of shoppers who reach past older pouches for the newest date"),
    "dc_short_rate": (0.03, "assumption: share of order lines the DC ships short (75% of cases)"),
    "truck_late_rate": (0.08, "assumption: share of mornings the DC truck misses its 06:00-06:30 slot"),
    "low_sales_alert": (0.25, "assumption: the alert flags a day with sales under 25% of forecast while the books "
                              "show at least a day of stock"),
    "count_find_rate": (0.9, "assumption: share of misplaced stock a full count finds"),
    "lead_time_days": (1, "store order at 22:00, DC truck next morning"),
    "reorder": ({"z": 1.65, "cover_days": 2.0, "window_days": 28},
                "min/max: reorder point = forecast x lead time + 1.65 sigma; order up to two more days of cover"),
    "milk_standing_order": ({"weekday": 315, "weekend": 338},
                            "assumption: store manager's standing order for toned milk, pouches per day"),
    "fresh_standing_factor": (1.02, "assumption: standing orders for other fresh items, as a multiple of mean demand"),
    "transactions_per_day": (1100, "assumption: bills per day at an 8,000 sq ft supermarket"),
    "tender_mix": ({"UPI": 0.62, "card": 0.13, "cash": 0.25}, "assumption"),
    "audit_days": (["Tue", "Fri"], "assumption: third-party shelf audit at 11:00"),
}


def param(name: str) -> object:
    return PARAMS[name][0]


@dataclass(frozen=True)
class StoryEvent:
    key: str
    when: str  # ISO timestamp or date the event is anchored to
    sku: str
    summary: str
    domain: str  # retail, logistics, payments


STORY_EVENTS = [
    StoryEvent("misplaced_putaway", "2026-06-08T06:00", HERO_SKU,
               "The morning delivery of 5 kg atta is put away behind the rice stack, in the wrong bay.",
               "retail"),
    StoryEvent("found_in_backroom", "2026-06-13T10:00", HERO_SKU,
               "Staff restacking rice find the missing cases (only if nobody found them earlier).",
               "retail"),
    StoryEvent("wrong_pallet", "2026-06-22T06:00", HERO_SKU,
               "At the DC, the 5 kg line is picked from the adjacent 1 kg slot. The pallet label and the "
               "shipping notice still say 5 kg, and the store books what the notice says.",
               "logistics"),
    StoryEvent("complaint_count", "2026-06-26T09:00", HERO_SKU,
               "After customer complaints, the store manager orders a count of the atta bay (only if the "
               "5 kg shelf is still frozen).",
               "retail"),
]
