"""Constants for the synthetic world. Everything here is invented; standards are named for alignment only."""
from __future__ import annotations

from datetime import UTC, date, datetime

SEED = 42
TODAY = date(2026, 10, 17)
NOW = datetime(2026, 10, 17, 6, 0, tzinfo=UTC)  # newest sample in any historian
HIST_START = date(2024, 1, 1)  # operating history held in the historians
FACTORY_START = date(2016, 1, 1)

OPERATOR = "org:aurelia"
OEM = "org:kestrel"

ORGS = {
    "org:aurelia": ("Aurelia Energy", "operator"),
    "org:kestrel": ("Kestrel Pump Works", "oem"),
    "org:halden": ("Halden Bearing Co.", "supplier"),
    "org:orlo": ("Orlo Precision Bearings", "supplier"),
    "org:veyron": ("Veyron Polymers", "supplier"),
    "org:tanis": ("Tanis Compounds", "supplier"),
    "org:norvik": ("Norvik Seals", "supplier"),
    "org:brandvik": ("Brandvik Pumps", "oem"),
    "org:tolliver": ("Tolliver Flow", "oem"),
}
# the other pump customers (each also an operator of something)
PUMP_CUSTOMERS = ["Brenmark Refining", "Caldor Petrochemicals", "Dunmore Energy", "Eastgate Midstream",
                  "Fenwick Chemicals", "Garrow Oil & Gas", "Halvorsen Terminals", "Ironvale Fertilisers",
                  "Juniper Bay Power", "Kellan Pipeline", "Lowry Gas Processing", "Marlow Utilities",
                  "Northfield Sugar", "Oakridge Paper"]
ESP_OPERATORS = ["Ridgeline Petroleum", "Saltmarsh Resources", "Tern Creek Oil"]

# sites: id -> (name, kind, tz, areas {area_no: (floc_prefix, label, services)})
REFINERIES = {
    "R1": ("Refinery R1", "America/Chicago", {"10": ("CDU1", 8), "21": ("HTU1", 8), "33": ("UTL1", 6)}),
    "R2": ("Refinery R2", "America/Chicago", {"30": ("CDU2", 8), "41": ("FCC2", 6)}),
    "R3": ("Refinery R3", "America/Chicago", {"50": ("ALK3", 6), "61": ("RFM3", 4)}),
}
FIELD = ("FA", "Field A", "America/Chicago")

PUMP_MODELS = {
    # model -> (api_type, rated_m3h, bearing material, seal)
    "KP-BB2-650": ("BB2", 650.0),
    "KP-BB2-400": ("BB2", 400.0),
    "KP-OH2-150": ("OH2", 150.0),
    "KP-VS6-300": ("VS6", 300.0),
}
# vibration alarm and trip, mm/s RMS (ISO 10816 / 20816 style zones for these machines)
VIB_ALARM = 4.5
VIB_TRIP = 7.1
MTR_T_ALARM = 135.0
MTR_T_DESIGN = 150.0

# the planted stories ----------------------------------------------------------------------
LOT_BEARING = "B-24-117"
ECO_BEARING = "ECO-24-1147"
LOT_ELASTOMER = "E-25-031"
ECO_ELASTOMER = "ECO-25-0389"
ECO_BEARING_DATE = date(2024, 11, 4)
ECO_ELASTOMER_DATE = date(2025, 7, 21)
LOT_BEARING_PUMPS = 38
LOT_BEARING_CUSTOMERS = 9
LOT_ELASTOMER_SECTIONS = 61
LOT_ELASTOMER_OPERATORS = 4

# the six process pumps: serial -> (model, built, shipped, position, installed, note)
FLEET = {
    "OEM-24-0398": ("KP-BB2-650", date(2024, 11, 22), date(2024, 12, 20), "R1:21-P-215A", date(2025, 2, 15)),
    "OEM-24-0412": ("KP-BB2-650", date(2024, 12, 3), date(2025, 1, 10), "R1:10-P-101A", date(2025, 6, 1)),
    "OEM-24-0455": ("KP-BB2-650", date(2024, 12, 17), date(2025, 1, 24), "R2:30-P-301A", date(2025, 4, 3)),
    "OEM-25-1150": ("KP-BB2-650", date(2025, 1, 14), date(2025, 2, 21), "R2:30-P-301B", date(2025, 4, 3)),
    "OEM-25-1187": ("KP-BB2-650", date(2025, 2, 11), date(2025, 3, 14), "R1:10-P-101A", date(2026, 3, 10)),
    "OEM-25-1203": ("KP-BB2-650", date(2025, 3, 10), date(2025, 4, 7), "R1:21-P-215B", date(2025, 5, 20)),
}
# P-101B history: OEM-21-0090 until 2 May 2026, then OEM-24-0412 (overhauled)
P101_FAIL_VIB = date(2026, 3, 8)
P101_SWAP = date(2026, 3, 10)
P101B_SWAP = date(2026, 5, 2)
P101_ELP = date(2026, 9, 21)
P301A_FAIL = date(2026, 7, 14)

# Field A: 12 ESP wells, run lives (days) taken from the published demo
OLD_LIVES = [512, 590, 640, 655, 688, 720, 745, 760, 778, 782, 790, 810, 845, 870, 910, 960, 1020, 1105]
NEW_FAILED = [196, 214, 251, 268, 290, 344, 377]
NEW_RUNNING = [205, 231, 276, 305, 330]
A07_OLD = "ES-23-0117"
A07_NEW = "ES-25-0233"
A07_NEW_SEAL = "SS-25-0811"
A07_OLD_SEAL = "SS-23-0478"
A07_OLD_START = date(2024, 2, 20)
A07_OLD_FAIL = date(2026, 1, 8)
A07_NEW_START = date(2026, 1, 14)
SEAL_CUTOFF = date(2025, 8, 1)  # seal sections built since this date carry the alternate elastomer
