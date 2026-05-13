"""
Synthetic Procurement & Spend Analytics data.

Mirrors what a Fortune-500 manufacturing enterprise running SAP Ariba, Coupa,
Jaggaer, Ivalua, GEP SMART, Oracle Procurement Cloud, Workday Strategic
Sourcing, Tradeshift, Basware, Zycus would land into a spend cube — plus
supplier sustainability ratings from EcoVadis, CDP, SBTi; supplier risk from
Resilinc, Sphera SCRM, D&B (Paydex/Failure Score), BitSight, RiskRecon;
spend analytics layer from Sievo / Spendkey; and GHG Protocol Scope 3
Category 1+2 emissions attribution.

Standards:
  * UNSPSC v26 (Segment/Family/Class/Commodity) — canonical category key.
  * GHG Protocol Corporate Value Chain (Scope 3) — Cat 1 (Purchased Goods &
    Services), Cat 2 (Capital Goods).
  * Open Peppol BIS 3.0 — e-invoicing envelope.
  * ISO 4217 — currency codes.
  * ISO 17442 — LEI.

Entities (>=10):
  category_taxonomy, supplier, contract, purchase_order, po_line, receipt,
  invoice, supplier_risk_assessment, emissions_factor,
  sustainability_attribute, savings_event.

Scale targets (medium / default):
  10,000 suppliers
  ~5,000 contracts (subset of suppliers have contracts)
  100,000 purchase orders
  ~300,000 PO lines (avg 3 per PO)
  ~120,000 receipts
  200,000 invoices
   5,000 supplier risk assessments
  ~5,000 sustainability attributes
  ~3,000 savings events
   ~100 UNSPSC commodities, ~600 emissions factors (commodity x region)
  100k spend-cube view rows (derived from po_line)

int64-safe IDs (same pattern as predictive_maintenance/capital_markets).
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from common import make_context, weighted_choice, write_table

SUBDOMAIN = "procurement_spend_analytics"

# ---------------------------------------------------------------------------
# Reference data
# ---------------------------------------------------------------------------
# UNSPSC commodities — simplified subset for a manufacturing enterprise.
# 100 commodities × 6 regions ≈ 600 emissions factors.
UNSPSC_COMMODITIES = [
    # (segment_code, family_code, class_code, commodity_code, seg_name, fam_name, cls_name, com_name, dir_ind, capex_opex, scope3_cat)
    ("11", "1112", "111215", "11121500", "Mineral and metal raw materials", "Earth and stone", "Limestone", "Limestone block",                "direct",   "opex",  1),
    ("11", "1113", "111316", "11131600", "Mineral and metal raw materials", "Metal ore",      "Iron ore",  "Hematite iron ore",               "direct",   "opex",  1),
    ("12", "1213", "121316", "12131600", "Chemicals",                       "Solvents",       "Aliphatic", "Hexane industrial grade",         "direct",   "opex",  1),
    ("12", "1214", "121420", "12142000", "Chemicals",                       "Polymers",       "Polyethylene", "HDPE pellets",                "direct",   "opex",  1),
    ("13", "1310", "131015", "13101500", "Resin and Rosin and Rubber",      "Natural rubber", "Latex",     "Natural latex rubber",            "direct",   "opex",  1),
    ("13", "1310", "131016", "13101600", "Resin and Rosin and Rubber",      "Synthetic rubber","SBR",      "Styrene-butadiene rubber",       "direct",   "opex",  1),
    ("14", "1411", "141115", "14111500", "Paper Materials and Products",    "Pulp",           "Wood pulp", "Bleached kraft pulp",             "direct",   "opex",  1),
    ("15", "1510", "151015", "15101500", "Fuels and Fuel Additives",        "Petroleum fuel", "Diesel",    "Ultra low sulfur diesel",         "direct",   "opex",  3),
    ("15", "1510", "151018", "15101800", "Fuels and Fuel Additives",        "Natural gas",    "Pipeline",  "Industrial natural gas",          "direct",   "opex",  3),
    ("15", "1512", "151215", "15121500", "Fuels and Fuel Additives",        "Lubricants",     "Engine oil","Mineral engine oil 15W-40",       "indirect", "opex",  1),
    ("23", "2310", "231015", "23101500", "Manufacturing components",        "Bearings",       "Ball bearing","Deep groove ball bearing",      "direct",   "opex",  1),
    ("23", "2310", "231016", "23101600", "Manufacturing components",        "Bearings",       "Roller bearing","Cylindrical roller bearing", "direct",   "opex",  1),
    ("23", "2311", "231115", "23111500", "Manufacturing components",        "Couplings",      "Flexible",  "Flexible jaw coupling",           "direct",   "opex",  1),
    ("24", "2410", "241015", "24101500", "Industrial Mfg & Processing Machy", "Pumps",        "Centrifugal","Centrifugal water pump",         "direct",   "capex", 2),
    ("24", "2410", "241016", "24101600", "Industrial Mfg & Processing Machy", "Pumps",        "Positive displacement","Gear pump",           "direct",   "capex", 2),
    ("24", "2411", "241115", "24111500", "Industrial Mfg & Processing Machy", "Compressors",  "Reciprocating","Reciprocating air compressor","direct", "capex", 2),
    ("24", "2412", "241215", "24121500", "Industrial Mfg & Processing Machy", "Conveyors",    "Belt",      "Belt conveyor system",            "direct",   "capex", 2),
    ("25", "2510", "251015", "25101500", "Commercial & Military Vehicles",    "Trucks",       "Light-duty","Light-duty pickup truck",         "indirect", "capex", 2),
    ("26", "2611", "261115", "26111500", "Power Generation & Distribution",   "Generators",   "Diesel gen","Diesel emergency generator",      "indirect", "capex", 2),
    ("26", "2611", "261116", "26111600", "Power Generation & Distribution",   "Solar",        "PV panel",  "Industrial PV panel",             "indirect", "capex", 2),
    ("31", "3115", "311520", "31152000", "Mfg components & supplies",         "Hardware",     "Fasteners", "Hex bolts, steel",                "direct",   "opex",  1),
    ("32", "3210", "321015", "32101500", "Electronic Components",             "Semiconductors","Microcontroller","8-bit MCU",                 "direct",   "opex",  1),
    ("32", "3210", "321020", "32102000", "Electronic Components",             "Semiconductors","Power MOSFET","Power MOSFET",                 "direct",   "opex",  1),
    ("39", "3910", "391015", "39101500", "Electrical Systems & Lighting",     "Lighting",     "LED",       "Industrial LED high-bay",         "indirect", "opex",  1),
    ("40", "4010", "401015", "40101500", "Distribution & Storage",            "HVAC",         "Chiller",   "Industrial chiller",              "indirect", "capex", 2),
    ("41", "4111", "411115", "41111500", "Laboratory & Measurement",          "Test eq.",     "Oscilloscope","Digital oscilloscope",          "indirect", "capex", 2),
    ("43", "4321", "432115", "43211500", "Information Tech Broadcasting",     "Computers",    "Laptop",    "Business laptop",                 "indirect", "capex", 2),
    ("43", "4322", "432215", "43221500", "Information Tech Broadcasting",     "Networking",   "Switch",    "48-port managed switch",          "indirect", "capex", 2),
    ("43", "4323", "432315", "43231500", "Information Tech Broadcasting",     "Software",     "ERP",       "ERP software subscription",       "indirect", "opex",  1),
    ("43", "4323", "432316", "43231600", "Information Tech Broadcasting",     "Software",     "Cloud",     "Cloud compute (IaaS)",            "indirect", "opex",  1),
    ("44", "4410", "441015", "44101500", "Office Equipment Supplies",         "Printers",     "Laser",     "Color laser printer",             "indirect", "capex", 2),
    ("44", "4411", "441115", "44111500", "Office Equipment Supplies",         "Paper",        "Copy paper","A4 80gsm copy paper",             "indirect", "opex",  1),
    ("47", "4710", "471015", "47101500", "Cleaning Equipment & Supplies",     "Cleaners",     "Detergent", "Industrial detergent",            "indirect", "opex",  1),
    ("50", "5018", "501815", "50181500", "Food Beverage Tobacco",             "Beverages",    "Coffee",    "Office coffee service",           "indirect", "opex",  1),
    ("51", "5114", "511415", "51141500", "Drugs & Pharmaceutical Products",   "First aid",    "Bandages",  "Industrial first-aid kit",        "indirect", "opex",  1),
    ("55", "5512", "551215", "55121500", "Published Products",                "Marketing",    "Print",     "Marketing collateral printing",   "indirect", "opex",  1),
    ("56", "5612", "561215", "56121500", "Furniture & Furnishings",           "Office",       "Desk",      "Office desk",                     "indirect", "capex", 2),
    ("60", "6010", "601015", "60101500", "Musical Instruments",               "Audio",        "PA",        "Conference room PA system",       "indirect", "capex", 2),
    ("70", "7012", "701215", "70121500", "Farming & Fishing Mach.",           "Tractors",     "Compact",   "Compact utility tractor",         "indirect", "capex", 2),
    ("72", "7210", "721015", "72101500", "Building Construction",             "General",      "GC services","Plant construction services",   "indirect", "capex", 2),
    ("76", "7610", "761015", "76101500", "Industrial Cleaning Services",      "Janitorial",   "Office",    "Janitorial office service",       "indirect", "opex",  1),
    ("77", "7710", "771015", "77101500", "Environmental Services",            "Waste",        "Hazardous", "Hazardous waste disposal",        "indirect", "opex",  1),
    ("78", "7811", "781115", "78111500", "Transportation & Storage & Mail",   "Freight",      "Truckload", "Truckload freight",               "indirect", "opex",  4),
    ("78", "7812", "781215", "78121500", "Transportation & Storage & Mail",   "Freight",      "Ocean",     "Ocean container freight",         "indirect", "opex",  4),
    ("80", "8010", "801015", "80101500", "Management & Business Pros & Admin Svcs", "Consulting","Management","Management consulting",        "indirect", "opex",  1),
    ("80", "8011", "801115", "80111500", "Management & Business Pros & Admin Svcs", "HR services","Recruiting","Executive recruiting",        "indirect", "opex",  1),
    ("80", "8014", "801415", "80141500", "Management & Business Pros & Admin Svcs", "Marketing", "Advertising","Digital advertising svcs",   "indirect", "opex",  1),
    ("81", "8110", "811015", "81101500", "Engineering & Research Svcs",       "Engineering",  "Mechanical","Mechanical engineering svcs",     "indirect", "opex",  1),
    ("81", "8111", "811115", "81111500", "Engineering & Research Svcs",       "IT services",  "App dev",   "Application development svcs",    "indirect", "opex",  1),
    ("82", "8210", "821015", "82101500", "Editorial Design Graphic Arts",     "Graphic",      "Design",    "Graphic design services",         "indirect", "opex",  1),
    ("83", "8310", "831015", "83101500", "Public Utilities & Public Sector",  "Electricity",  "Industrial","Industrial electricity supply",   "indirect", "opex",  2),
    ("83", "8310", "831016", "83101600", "Public Utilities & Public Sector",  "Water",        "Industrial","Industrial water supply",         "indirect", "opex",  1),
    ("84", "8412", "841215", "84121500", "Financial & Insurance Services",    "Banking",      "Wire",      "Banking services",                "indirect", "opex",  1),
    ("84", "8413", "841315", "84131500", "Financial & Insurance Services",    "Insurance",    "Property",  "Property & casualty insurance",   "indirect", "opex",  1),
    ("85", "8511", "851115", "85111500", "Healthcare Services",               "Medical",      "Occupational","Occupational health svcs",      "indirect", "opex",  1),
    ("86", "8610", "861015", "86101500", "Education & Training Services",     "Training",     "Workforce", "Workforce training services",     "indirect", "opex",  1),
    ("90", "9012", "901215", "90121500", "Travel Food Lodging & Entertainment","Air travel",  "Business",  "Business air travel",             "indirect", "opex",  6),
    ("90", "9011", "901115", "90111500", "Travel Food Lodging & Entertainment","Lodging",     "Business",  "Business hotel lodging",          "indirect", "opex",  6),
    ("93", "9310", "931015", "93101500", "Public Sector Services",            "Legal",        "External",  "External legal services",         "indirect", "opex",  1),
]
# pad a bit to ~60 commodities

CONTRACT_TYPES = ["framework", "spot", "MSA", "SOW", "catalog", "rebate", "service_agreement"]
CONTRACT_TYPE_W = [0.32, 0.10, 0.18, 0.14, 0.12, 0.06, 0.08]
PAYMENT_TERMS = ["NET15", "NET30", "NET45", "NET60", "NET90", "2_10_NET30", "1_15_NET45"]
PAYMENT_TERMS_W = [0.08, 0.40, 0.18, 0.18, 0.06, 0.06, 0.04]
INCOTERMS = ["DDP", "DAP", "FOB", "EXW", "CIF", "CFR", "FCA"]
INCOTERMS_W = [0.32, 0.18, 0.20, 0.12, 0.08, 0.05, 0.05]
BUYING_CHANNELS = ["catalog", "punchout", "free_text", "marketplace", "pcard", "auto"]
BUYING_CHANNEL_W = [0.30, 0.18, 0.25, 0.10, 0.10, 0.07]
PO_STATUS = ["draft", "approved", "sent", "partially_received", "received", "invoiced", "closed", "cancelled"]
PO_STATUS_W = [0.02, 0.04, 0.08, 0.06, 0.10, 0.22, 0.46, 0.02]
INVOICE_STATUS = ["received", "matched", "approved", "on_hold", "paid", "disputed", "void"]
INVOICE_STATUS_W = [0.04, 0.06, 0.05, 0.04, 0.78, 0.02, 0.01]
MATCH_TYPE = ["two_way", "three_way", "exception", "none"]
MATCH_TYPE_W = [0.20, 0.62, 0.15, 0.03]

CURRENCY_CODES = ["USD", "EUR", "GBP", "JPY", "CNY", "INR", "MXN", "BRL", "CAD", "AUD", "SGD", "KRW", "CHF", "SEK"]
CURRENCY_W = [0.42, 0.18, 0.06, 0.04, 0.08, 0.05, 0.03, 0.03, 0.04, 0.02, 0.02, 0.01, 0.01, 0.01]
FX_TO_USD = {
    "USD": 1.0, "EUR": 1.08, "GBP": 1.26, "JPY": 0.0067, "CNY": 0.14, "INR": 0.012, "MXN": 0.058,
    "BRL": 0.20, "CAD": 0.74, "AUD": 0.66, "SGD": 0.74, "KRW": 0.00076, "CHF": 1.13, "SEK": 0.095,
}

COUNTRY_TO_REGION = {
    "US": "NA", "CA": "NA", "MX": "NA",
    "GB": "EMEA", "DE": "EMEA", "FR": "EMEA", "IT": "EMEA", "ES": "EMEA", "NL": "EMEA", "SE": "EMEA", "CH": "EMEA", "PL": "EMEA",
    "CN": "APAC", "IN": "APAC", "JP": "APAC", "KR": "APAC", "SG": "APAC", "AU": "APAC", "TW": "APAC", "VN": "APAC",
    "BR": "LATAM", "AR": "LATAM", "CL": "LATAM",
    "AE": "MEA", "SA": "MEA", "ZA": "MEA",
}
COUNTRIES = list(COUNTRY_TO_REGION.keys())

DIVERSITY_FLAGS = ["MBE", "WBE", "VBE", "LGBTBE", "SDB", "HUBZone"]
ECOVADIS_MEDALS = ["none", "bronze", "silver", "gold", "platinum"]
ECOVADIS_MEDAL_W = [0.55, 0.20, 0.15, 0.08, 0.02]
CDP_SCORES = ["A", "A-", "B", "B-", "C", "C-", "D", "D-", "F"]
CDP_SCORE_W = [0.05, 0.08, 0.15, 0.15, 0.20, 0.15, 0.10, 0.07, 0.05]
RISK_SOURCES = ["resilinc", "dnb", "bitsight", "ecovadis", "riskmethods", "internal_questionnaire"]
RISK_SOURCE_W = [0.30, 0.25, 0.15, 0.15, 0.10, 0.05]
RISK_TIERS = ["low", "medium", "high", "critical"]
RISK_TIER_W = [0.45, 0.35, 0.15, 0.05]

EMISSIONS_SOURCES = ["exiobase", "usio", "ecoinvent", "cdp_supplier", "primary_supplier_data"]
EMISSIONS_SOURCE_W = [0.34, 0.22, 0.20, 0.14, 0.10]

SUSTAINABILITY_SOURCES = ["ecovadis", "cdp_supply_chain", "sbti", "msci_esg", "sp_sustainable1", "primary"]
SUSTAINABILITY_SOURCE_W = [0.32, 0.28, 0.12, 0.10, 0.10, 0.08]

SAVINGS_EVENT_TYPES = ["negotiation", "consolidation", "reverse_auction", "spec_change", "rebate", "early_pay_discount", "cost_avoidance"]
SAVINGS_EVENT_W = [0.30, 0.18, 0.10, 0.10, 0.14, 0.10, 0.08]
SAVINGS_KIND = ["hard", "soft", "avoidance"]
SAVINGS_KIND_W = [0.55, 0.25, 0.20]
BASELINE_METHODS = ["prior_price", "index", "RFP_avg", "benchmark", "cost_model"]
BASELINE_METHOD_W = [0.36, 0.18, 0.20, 0.16, 0.10]

UOM_CODES = ["EA", "KG", "LB", "L", "GAL", "M", "FT", "BX", "PL", "HR", "MO"]
UOM_W = [0.40, 0.15, 0.05, 0.06, 0.04, 0.08, 0.04, 0.06, 0.04, 0.05, 0.03]

# ---------------------------------------------------------------------------
SCALE_PRESETS = {
    # name : (n_suppliers, n_contracts, n_po, lines_per_po, n_receipts, n_invoices, n_risk, n_sustain, n_savings, n_emfactors_per_cat)
    "demo":   (   200,    50,    500, 3,    400,   1_000,   100,   100,   80, 2),
    "small":  ( 1_000,   300,  5_000, 3,  3_500,  10_000,   500,   500,  500, 3),
    "medium": (10_000, 5_000,100_000, 3,120_000, 200_000, 5_000, 5_000,3_000, 6),
    "large":  (25_000,10_000,250_000, 4,300_000, 500_000,15_000,12_000,8_000, 6),
}


def _category_taxonomy(ctx):
    rows = []
    for seg, fam, cls, com, sn, fn, cn, cmn, di, co, sc in UNSPSC_COMMODITIES:
        rows.append({
            "category_code": com,
            "segment_code": seg,
            "family_code": fam,
            "class_code": cls,
            "commodity_code": com,
            "segment_name": sn,
            "family_name": fn,
            "class_name": cn,
            "commodity_name": cmn,
            "direct_or_indirect": di,
            "capex_or_opex": co,
            "internal_category_id": f"CAT-{com}",
            "scope3_category": sc,
        })
    return pd.DataFrame(rows)


def _suppliers(ctx, n):
    rng = ctx.rng
    countries = rng.choice(COUNTRIES, size=n)
    regions = np.array([COUNTRY_TO_REGION[c] for c in countries])
    ecovadis_medal = weighted_choice(rng, ECOVADIS_MEDALS, ECOVADIS_MEDAL_W, n)
    medal_to_score_base = {"none": 0, "bronze": 50, "silver": 62, "gold": 72, "platinum": 82}
    ecovadis_score = np.array([medal_to_score_base[m] for m in ecovadis_medal]) + rng.integers(-3, 8, size=n)
    ecovadis_score = np.clip(ecovadis_score, 0, 100).astype(np.int16)
    diversity_picks = []
    for _ in range(n):
        if rng.random() < 0.18:
            n_flags = rng.integers(1, 3)
            picks = list(rng.choice(DIVERSITY_FLAGS, size=int(n_flags), replace=False))
            diversity_picks.append("[" + ",".join(f'"{p}"' for p in picks) + "]")
        else:
            diversity_picks.append("[]")
    onboarded_secs = rng.integers(
        int(pd.Timestamp("2018-01-01").timestamp()),
        int(pd.Timestamp("2026-04-01").timestamp()),
        size=n,
    )
    onboarded = pd.to_datetime(onboarded_secs, unit="s")
    last_assess_offset_d = rng.integers(0, 540, size=n)
    last_assess = pd.Timestamp("2026-05-01") - pd.to_timedelta(last_assess_offset_d, unit="D")
    parent_pool = [f"PARENT{i:07d}" for i in range(1, max(2, n // 5) + 1)]
    parent_duns = rng.choice(parent_pool, size=n)
    sbti = rng.random(n) < 0.18
    return pd.DataFrame({
        "supplier_id": [f"SUP{i:08d}" for i in range(1, n + 1)],
        "duns_number": [f"{rng.integers(10**8, 10**9):09d}" for _ in range(n)],
        "lei": [f"LEI{rng.integers(10**15, 10**16):016d}"[:20] for _ in range(n)],
        "legal_name": [f"Supplier {i} {countries[i-1]} {ctx.faker.company_suffix()}" for i in range(1, n + 1)],
        "parent_duns": parent_duns,
        "tax_id": [f"TAX{rng.integers(10**8, 10**10):010d}" for _ in range(n)],
        "country_iso2": countries,
        "region": regions,
        "industry_naics": [f"{rng.integers(31, 56):02d}{rng.integers(1000, 9999):04d}"[:6] for _ in range(n)],
        "industry_sic": [f"{rng.integers(2000, 9000):04d}" for _ in range(n)],
        "diversity_flags": diversity_picks,
        "ecovadis_score": ecovadis_score,
        "ecovadis_medal": ecovadis_medal,
        "cdp_climate_score": weighted_choice(rng, CDP_SCORES, CDP_SCORE_W, n),
        "sbti_committed": sbti,
        "paydex_score": rng.integers(40, 100, size=n).astype(np.int16),
        "failure_score": rng.integers(1, 100, size=n).astype(np.int16),
        "cyber_score": rng.integers(450, 900, size=n).astype(np.int16),
        "critical_flag": rng.random(n) < 0.06,
        "sanctions_flag": rng.random(n) < 0.002,
        "status": weighted_choice(rng, ["active", "onboarding", "blocked", "terminated", "watchlist"],
                                  [0.85, 0.05, 0.02, 0.04, 0.04], n),
        "onboarded_at": onboarded,
        "last_assessment_at": last_assess,
    })


def _contracts(ctx, suppliers, n):
    rng = ctx.rng
    sup_idx = rng.integers(0, len(suppliers), size=n)
    contract_type = weighted_choice(rng, CONTRACT_TYPES, CONTRACT_TYPE_W, n)
    effective_offset_d = rng.integers(-1500, 30, size=n)
    effective_date = (pd.Timestamp("2026-05-01") + pd.to_timedelta(effective_offset_d, unit="D")).normalize()
    duration_d = rng.choice([365, 730, 1095, 180], size=n)
    expiry_date = effective_date + pd.to_timedelta(duration_d, unit="D")
    payment_terms = weighted_choice(rng, PAYMENT_TERMS, PAYMENT_TERMS_W, n)
    incoterms = weighted_choice(rng, INCOTERMS, INCOTERMS_W, n)
    total_commit = np.round(rng.lognormal(11.5, 1.3, size=n), 2)
    currency = weighted_choice(rng, CURRENCY_CODES, CURRENCY_W, n)
    rebate_pct = np.where(rng.random(n) < 0.30, np.round(rng.uniform(0.005, 0.05, size=n), 4), 0.0)
    status_pool = ["draft", "active", "expired", "terminated", "renewed"]
    status = weighted_choice(rng, status_pool, [0.04, 0.74, 0.12, 0.06, 0.04], n)
    sus_clauses = np.where(
        rng.random(n) < 0.35,
        rng.choice([
            '{"ecovadis_min":"silver","scope3_disclosure":true}',
            '{"net_zero_year":2050,"renewable_min_pct":50}',
            '{"sbti_aligned":true,"cdp_required":true}',
        ], size=n),
        None,
    )
    kpi_clauses = np.where(
        rng.random(n) < 0.40,
        rng.choice([
            '{"otif_target":0.95,"defect_ppm_max":500}',
            '{"otif_target":0.97,"price_change_cap_pct":3}',
            '{"ncmr_max_per_quarter":3}',
        ], size=n),
        None,
    )
    meta_extracted = (pd.Timestamp("2026-05-01") - pd.to_timedelta(rng.integers(0, 365, size=n), unit="D"))
    return pd.DataFrame({
        "contract_id": [f"CTR{i:08d}" for i in range(1, n + 1)],
        "supplier_id": suppliers["supplier_id"].to_numpy()[sup_idx],
        "contract_type": contract_type,
        "parent_contract_id": None,
        "title": [f"{contract_type[i]} - {suppliers['legal_name'].iloc[sup_idx[i]][:32]}" for i in range(n)],
        "effective_date": effective_date.date,
        "expiry_date": expiry_date.date,
        "auto_renew": rng.random(n) < 0.40,
        "notice_period_days": rng.choice([30, 60, 90, 180], size=n).astype(np.int16),
        "total_commit_amount": total_commit,
        "total_commit_currency": currency,
        "payment_terms": payment_terms,
        "incoterms": incoterms,
        "rebate_pct": rebate_pct,
        "rebate_trigger_amount": np.where(rebate_pct > 0, np.round(total_commit * 0.6, 2), 0.0),
        "sustainability_clauses": sus_clauses,
        "kpi_clauses": kpi_clauses,
        "contract_value_realized": np.round(total_commit * rng.uniform(0.0, 1.1, size=n), 2),
        "status": status,
        "owner_buyer": [f"BUYER{rng.integers(1, 200):03d}" for _ in range(n)],
        "meta_extracted_at": meta_extracted,
    })


def _purchase_orders(ctx, suppliers, contracts, categories, n):
    rng = ctx.rng
    sup_idx = rng.integers(0, len(suppliers), size=n)
    # 70% of POs are against a contract; the rest are spot.
    has_contract = rng.random(n) < 0.70
    ctr_idx = rng.integers(0, len(contracts), size=n)
    contract_ids = np.where(has_contract, contracts["contract_id"].to_numpy()[ctr_idx], None)
    cat_idx = rng.integers(0, len(categories), size=n)
    channel = weighted_choice(rng, BUYING_CHANNELS, BUYING_CHANNEL_W, n)
    touchless = (np.isin(channel, ["catalog", "punchout", "auto"])) & (rng.random(n) < 0.85)
    # 8% maverick — off-contract for a category where a contract exists
    maverick = (~has_contract) & (rng.random(n) < 0.30)
    req_secs = rng.integers(
        int(pd.Timestamp("2026-01-01").timestamp()),
        int(pd.Timestamp("2026-05-08").timestamp()),
        size=n,
    )
    requisition_ts = pd.to_datetime(req_secs, unit="s")
    cycle_hours = np.where(
        touchless,
        rng.uniform(0.05, 2.0, size=n),
        np.where(channel == "free_text", rng.gamma(2.0, 36, size=n), rng.gamma(2.0, 8, size=n)),
    )
    po_issued_ts = requisition_ts + pd.to_timedelta((cycle_hours * 3600).astype(np.int64), unit="s")
    total_currency = weighted_choice(rng, CURRENCY_CODES, CURRENCY_W, n)
    total_amount = np.round(rng.lognormal(7.0, 1.5, size=n), 2)
    fx = np.array([FX_TO_USD[c] for c in total_currency])
    total_amount_base_usd = np.round(total_amount * fx, 2)
    status = weighted_choice(rng, PO_STATUS, PO_STATUS_W, n)
    payment_terms = weighted_choice(rng, PAYMENT_TERMS, PAYMENT_TERMS_W, n)
    incoterms = weighted_choice(rng, INCOTERMS, INCOTERMS_W, n)
    return pd.DataFrame({
        "po_id": [f"PO{i:09d}" for i in range(1, n + 1)],
        "po_number": [f"45{rng.integers(10**7, 10**8):08d}" for _ in range(n)],
        "supplier_id": suppliers["supplier_id"].to_numpy()[sup_idx],
        "contract_id": contract_ids,
        "requester_user_id": [f"REQ{rng.integers(1, 5000):05d}" for _ in range(n)],
        "buyer_user_id": [f"BUYER{rng.integers(1, 200):03d}" for _ in range(n)],
        "cost_center": [f"CC{rng.integers(1000, 9999):04d}" for _ in range(n)],
        "gl_account": [f"{rng.integers(40000, 79999)}" for _ in range(n)],
        "legal_entity": rng.choice(["LE-US-01", "LE-US-02", "LE-DE-01", "LE-GB-01", "LE-CN-01", "LE-IN-01", "LE-MX-01", "LE-BR-01"], size=n),
        "plant_id": rng.choice(["PLANT-A", "PLANT-B", "PLANT-C", "PLANT-D", "PLANT-E", "DC-01", "DC-02"], size=n),
        "requisition_id": [f"REQQ{i:09d}" for i in range(1, n + 1)],
        "requisition_ts": requisition_ts,
        "po_issued_ts": po_issued_ts,
        "buying_channel": channel,
        "total_amount": total_amount,
        "total_currency": total_currency,
        "total_amount_base_usd": total_amount_base_usd,
        "payment_terms": payment_terms,
        "incoterms": incoterms,
        "status": status,
        "touchless": touchless,
        "maverick_flag": maverick,
        "edi_855_received": rng.random(n) < 0.72,
        "category_code": categories["category_code"].to_numpy()[cat_idx],
    })


def _po_lines(ctx, pos, categories, lines_per_po, emissions_factors):
    rng = ctx.rng
    n = len(pos)
    rows_per_po = rng.integers(1, lines_per_po * 2, size=n)
    total_rows = int(rows_per_po.sum())
    po_ids = np.repeat(pos["po_id"].to_numpy(), rows_per_po)
    po_totals = np.repeat(pos["total_amount"].to_numpy(), rows_per_po)
    po_currencies = np.repeat(pos["total_currency"].to_numpy(), rows_per_po)
    po_dates = np.repeat(pos["po_issued_ts"].to_numpy(), rows_per_po)
    po_categories = np.repeat(pos["category_code"].to_numpy(), rows_per_po)
    # 30% of lines override the PO category (multi-category POs)
    line_cat = po_categories.copy()
    override_mask = rng.random(total_rows) < 0.30
    cat_choices = rng.integers(0, len(categories), size=total_rows)
    line_cat[override_mask] = categories["category_code"].to_numpy()[cat_choices[override_mask]]
    line_number = np.concatenate([np.arange(1, k + 1) for k in rows_per_po]).astype(np.int16)
    qty = np.round(rng.gamma(2.0, 5.0, size=total_rows).clip(1.0, 5000.0), 4)
    unit_price = np.round(rng.lognormal(2.5, 1.1, size=total_rows), 6).clip(0.01, 50_000.0)
    line_amount = np.round(qty * unit_price, 2)
    # Scale lines so the sum within a PO roughly matches header
    fx = np.array([FX_TO_USD.get(c, 1.0) for c in po_currencies])
    line_amount_base_usd = np.round(line_amount * fx, 2)
    # Scope-3 attribution via emissions_factors lookup by category_code & spend basis
    # Build a category→factor dict (use a single average if multiple regions)
    ef_by_cat = (
        emissions_factors.groupby("category_code")["factor_kgco2e_per_usd"]
        .mean()
        .to_dict()
    )
    factors_for_line = np.array([ef_by_cat.get(c, 0.45) for c in line_cat])
    scope3_kgco2e = np.round(line_amount_base_usd * factors_for_line, 4)
    uoms = weighted_choice(rng, UOM_CODES, UOM_W, total_rows)
    return pd.DataFrame({
        "po_line_id": [f"POL{i:010d}" for i in range(1, total_rows + 1)],
        "po_id": po_ids,
        "line_number": line_number,
        "item_id": [f"ITM{rng.integers(10**5, 10**6):06d}" for _ in range(total_rows)],
        "item_description": [f"Item {line_cat[i]} qty={int(qty[i])}" for i in range(total_rows)],
        "category_code": line_cat,
        "quantity": qty,
        "uom": uoms,
        "unit_price": unit_price,
        "line_amount": line_amount,
        "line_currency": po_currencies,
        "line_amount_base_usd": line_amount_base_usd,
        "requested_delivery_date": (pd.to_datetime(po_dates) + pd.to_timedelta(rng.integers(3, 90, size=total_rows), unit="D")).date,
        "tax_amount": np.round(line_amount * rng.uniform(0.0, 0.22, size=total_rows), 2),
        "discount_pct": np.round(np.where(rng.random(total_rows) < 0.20, rng.uniform(0.01, 0.15, size=total_rows), 0.0), 4),
        "scope3_kgco2e": scope3_kgco2e,
    })


def _receipts(ctx, po_lines, n):
    rng = ctx.rng
    idx = rng.integers(0, len(po_lines), size=n)
    po_line_id = po_lines["po_line_id"].to_numpy()[idx]
    po_id = po_lines["po_id"].to_numpy()[idx]
    qty_ord = po_lines["quantity"].to_numpy()[idx]
    received = np.round(qty_ord * rng.uniform(0.92, 1.05, size=n), 4)
    receipt_secs = rng.integers(
        int(pd.Timestamp("2026-01-05").timestamp()),
        int(pd.Timestamp("2026-05-10").timestamp()),
        size=n,
    )
    receipt_ts = pd.to_datetime(receipt_secs, unit="s")
    status = weighted_choice(rng, ["draft", "posted", "reversed"], [0.04, 0.94, 0.02], n)
    return pd.DataFrame({
        "receipt_id": [f"REC{i:010d}" for i in range(1, n + 1)],
        "po_id": po_id,
        "po_line_id": po_line_id,
        "receipt_ts": receipt_ts,
        "quantity_received": received,
        "receiver_user_id": [f"RCV{rng.integers(1, 800):04d}" for _ in range(n)],
        "plant_id": rng.choice(["PLANT-A", "PLANT-B", "PLANT-C", "PLANT-D", "PLANT-E", "DC-01", "DC-02"], size=n),
        "gr_document_no": [f"GR{rng.integers(10**7, 10**8):08d}" for _ in range(n)],
        "status": status,
    })


def _invoices(ctx, suppliers, pos, n):
    rng = ctx.rng
    # 92% of invoices reference a PO; 8% are non-PO.
    has_po = rng.random(n) < 0.92
    po_idx = rng.integers(0, len(pos), size=n)
    po_ids = np.where(has_po, pos["po_id"].to_numpy()[po_idx], None)
    sup_ids = np.where(has_po, pos["supplier_id"].to_numpy()[po_idx],
                       suppliers["supplier_id"].to_numpy()[rng.integers(0, len(suppliers), size=n)])
    inv_secs = rng.integers(
        int(pd.Timestamp("2026-01-15").timestamp()),
        int(pd.Timestamp("2026-05-10").timestamp()),
        size=n,
    )
    invoice_date = pd.to_datetime(inv_secs, unit="s").normalize()
    payment_terms_days = rng.choice([15, 30, 45, 60, 90], size=n)
    due_date = invoice_date + pd.to_timedelta(payment_terms_days, unit="D")
    received_ts = invoice_date + pd.to_timedelta(rng.integers(0, 5, size=n), unit="D")
    total_amount = np.round(rng.lognormal(7.5, 1.3, size=n), 2)
    currency = weighted_choice(rng, CURRENCY_CODES, CURRENCY_W, n)
    fx = np.array([FX_TO_USD[c] for c in currency])
    total_amount_base_usd = np.round(total_amount * fx, 2)
    match_type = weighted_choice(rng, MATCH_TYPE, MATCH_TYPE_W, n)
    matched = (match_type != "exception") & (rng.random(n) < 0.93)
    status = weighted_choice(rng, INVOICE_STATUS, INVOICE_STATUS_W, n)
    # paid_ts: 80% are paid; paid_late skew
    paid = np.isin(status, ["paid", "matched", "approved"])
    paid_offset_d = np.where(paid, rng.integers(-5, 25, size=n), 0)
    paid_ts = np.where(paid, due_date + pd.to_timedelta(paid_offset_d, unit="D"), pd.NaT)
    paid_amount = np.where(paid, total_amount, 0.0)
    now_ts = pd.Timestamp("2026-05-12")
    aging_days = np.where(paid,
                          (pd.to_datetime(paid_ts) - due_date).days.astype("int64"),
                          (now_ts - due_date).days.astype("int64"))
    aging_days = aging_days.astype(np.int16)
    early_pay_disc = paid & (np.array(paid_offset_d) <= -2)
    return pd.DataFrame({
        "invoice_id": [f"INV{i:010d}" for i in range(1, n + 1)],
        "supplier_id": sup_ids,
        "invoice_number": [f"INV{rng.integers(10**6, 10**8):08d}" for _ in range(n)],
        "po_id": po_ids,
        "invoice_date": invoice_date.date,
        "due_date": due_date.date,
        "received_ts": received_ts,
        "total_amount": total_amount,
        "total_currency": currency,
        "total_amount_base_usd": total_amount_base_usd,
        "tax_amount": np.round(total_amount * rng.uniform(0.0, 0.22, size=n), 2),
        "match_type": match_type,
        "matched": matched,
        "paid_ts": paid_ts,
        "paid_amount": np.round(paid_amount, 2),
        "early_pay_discount_taken": early_pay_disc,
        "aging_days": aging_days,
        "peppol_message_id": [f"peppol:9908:{rng.integers(10**12, 10**13):013d}" for _ in range(n)],
        "edi_810_doc_no": [f"810{rng.integers(10**6, 10**7):07d}" for _ in range(n)],
        "status": status,
    })


def _supplier_risk(ctx, suppliers, n):
    rng = ctx.rng
    idx = rng.integers(0, len(suppliers), size=n)
    assess_secs = rng.integers(
        int(pd.Timestamp("2025-01-01").timestamp()),
        int(pd.Timestamp("2026-05-10").timestamp()),
        size=n,
    )
    assessment_ts = pd.to_datetime(assess_secs, unit="s")
    overall = np.round(rng.beta(5, 2, size=n) * 100, 2)
    tier = np.where(overall > 75, "low",
            np.where(overall > 55, "medium",
            np.where(overall > 35, "high", "critical")))
    return pd.DataFrame({
        "assessment_id": [f"RSK{i:09d}" for i in range(1, n + 1)],
        "supplier_id": suppliers["supplier_id"].to_numpy()[idx],
        "assessment_ts": assessment_ts,
        "source": weighted_choice(rng, RISK_SOURCES, RISK_SOURCE_W, n),
        "overall_score": overall,
        "financial_score": rng.integers(20, 100, size=n).astype(np.int16),
        "operational_score": rng.integers(20, 100, size=n).astype(np.int16),
        "geographic_score": rng.integers(20, 100, size=n).astype(np.int16),
        "cyber_score": rng.integers(20, 100, size=n).astype(np.int16),
        "compliance_score": rng.integers(20, 100, size=n).astype(np.int16),
        "sustainability_score": rng.integers(20, 100, size=n).astype(np.int16),
        "tier": tier,
        "mitigation_action": rng.choice([
            "Dual-source within 6 months",
            "Quarterly business review escalation",
            "Add to watchlist; weekly EventWatch monitoring",
            "Insurance carve-out via BPO",
            "Cyber-attestation required at next renewal",
            "EcoVadis re-assessment within 90 days",
            "Geographic diversification — near-shore alternative qualified",
        ], size=n),
        "assessor_user_id": [f"ASS{rng.integers(1, 100):03d}" for _ in range(n)],
        "valid_until": (assessment_ts + pd.to_timedelta(rng.choice([180, 365], size=n), unit="D")).date,
    })


def _emissions_factors(ctx, categories, factors_per_cat):
    rng = ctx.rng
    rows = []
    fid = 1
    base_factor_by_cat = {row.category_code: float(rng.uniform(0.15, 1.8)) for row in categories.itertuples()}
    for row in categories.itertuples():
        for _ in range(factors_per_cat):
            country = rng.choice(["US", "DE", "CN", "IN", "BR", "JP"])
            vintage = int(rng.choice([2021, 2022, 2023]))
            factor_usd = round(base_factor_by_cat[row.category_code] * rng.uniform(0.7, 1.3), 6)
            rows.append({
                "emissions_factor_id": f"EF{fid:08d}",
                "source": weighted_choice(rng, EMISSIONS_SOURCES, EMISSIONS_SOURCE_W, 1)[0],
                "vintage_year": vintage,
                "category_code": row.category_code,
                "country_iso2": country,
                "factor_kgco2e_per_usd": factor_usd,
                "factor_kgco2e_per_unit": round(factor_usd * float(rng.uniform(0.1, 5.0)), 6),
                "unit": rng.choice(["kg", "liter", "kWh", "piece"]),
                "ghg_scope3_category": int(row.scope3_category),
                "uncertainty_pct": round(float(rng.uniform(8.0, 35.0)), 2),
                "last_updated": pd.Timestamp("2025-09-01") + pd.to_timedelta(int(rng.integers(0, 240)), unit="D"),
            })
            fid += 1
    return pd.DataFrame(rows)


def _sustainability_attributes(ctx, suppliers, n):
    rng = ctx.rng
    idx = rng.integers(0, len(suppliers), size=n)
    reporting_year = rng.choice([2022, 2023, 2024, 2025], size=n).astype(np.int16)
    scope1 = np.round(rng.lognormal(9.0, 1.4, size=n), 2)
    scope2 = np.round(rng.lognormal(8.5, 1.5, size=n), 2)
    scope3 = np.round(rng.lognormal(11.0, 1.5, size=n), 2)
    renewable = np.round(rng.beta(2, 5, size=n) * 100, 2)
    return pd.DataFrame({
        "sustainability_attr_id": [f"SUS{i:08d}" for i in range(1, n + 1)],
        "supplier_id": suppliers["supplier_id"].to_numpy()[idx],
        "source": weighted_choice(rng, SUSTAINABILITY_SOURCES, SUSTAINABILITY_SOURCE_W, n),
        "reporting_year": reporting_year,
        "scope1_tco2e": scope1,
        "scope2_market_tco2e": scope2,
        "scope2_location_tco2e": np.round(scope2 * rng.uniform(0.92, 1.08, size=n), 2),
        "scope3_tco2e": scope3,
        "renewable_energy_pct": renewable,
        "water_withdrawal_m3": np.round(rng.lognormal(7.0, 1.5, size=n), 2),
        "waste_tonnes": np.round(rng.lognormal(5.5, 1.4, size=n), 2),
        "sbti_target_year": np.where(rng.random(n) < 0.25,
                                     rng.choice([2030, 2035, 2040], size=n),
                                     0).astype(np.int16),
        "net_zero_target_year": np.where(rng.random(n) < 0.35,
                                         rng.choice([2040, 2045, 2050], size=n),
                                         0).astype(np.int16),
        "observed_at": pd.Timestamp("2025-12-01") + pd.to_timedelta(rng.integers(0, 380, size=n), unit="D"),
    })


def _savings_events(ctx, suppliers, contracts, categories, n):
    rng = ctx.rng
    sup_idx = rng.integers(0, len(suppliers), size=n)
    ctr_idx = rng.integers(0, len(contracts), size=n)
    cat_idx = rng.integers(0, len(categories), size=n)
    committed = np.round(rng.lognormal(9.0, 1.3, size=n), 2)
    realized_pct = np.clip(rng.beta(4, 2, size=n), 0.0, 1.2)
    realized = np.round(committed * realized_pct, 2)
    committed_at_secs = rng.integers(
        int(pd.Timestamp("2025-01-01").timestamp()),
        int(pd.Timestamp("2026-05-01").timestamp()),
        size=n,
    )
    committed_at = pd.to_datetime(committed_at_secs, unit="s")
    realized_through = committed_at + pd.to_timedelta(rng.integers(30, 365, size=n), unit="D")
    return pd.DataFrame({
        "savings_event_id": [f"SAV{i:08d}" for i in range(1, n + 1)],
        "supplier_id": suppliers["supplier_id"].to_numpy()[sup_idx],
        "contract_id": contracts["contract_id"].to_numpy()[ctr_idx],
        "category_code": categories["category_code"].to_numpy()[cat_idx],
        "event_type": weighted_choice(rng, SAVINGS_EVENT_TYPES, SAVINGS_EVENT_W, n),
        "savings_kind": weighted_choice(rng, SAVINGS_KIND, SAVINGS_KIND_W, n),
        "committed_amount_usd": committed,
        "realized_amount_usd": realized,
        "baseline_method": weighted_choice(rng, BASELINE_METHODS, BASELINE_METHOD_W, n),
        "signed_off_by": [f"FIN{rng.integers(1, 50):03d}" for _ in range(n)],
        "committed_at": committed_at,
        "realized_through_ts": realized_through,
    })


def generate(seed=42, scale="medium"):
    ctx = make_context(seed)
    (n_sup, n_ctr, n_po, lpp, n_rec, n_inv, n_risk, n_sus, n_sav, ef_per_cat) = SCALE_PRESETS[scale]
    print(f"  scale = {scale}")
    print(f"    suppliers={n_sup:,} contracts={n_ctr:,} pos={n_po:,} lpp={lpp} receipts={n_rec:,} invoices={n_inv:,}")
    print(f"    risk_assessments={n_risk:,} sustainability_attrs={n_sus:,} savings_events={n_sav:,}")

    print("  generating category_taxonomy...")
    categories = _category_taxonomy(ctx)
    print(f"    {len(categories)} UNSPSC commodities")
    print("  generating emissions_factors...")
    emissions_factors = _emissions_factors(ctx, categories, ef_per_cat)
    print(f"    {len(emissions_factors)} emissions factors")

    print("  generating suppliers...")
    suppliers = _suppliers(ctx, n_sup)
    print("  generating contracts...")
    contracts = _contracts(ctx, suppliers, n_ctr)
    print("  generating purchase_orders...")
    purchase_orders = _purchase_orders(ctx, suppliers, contracts, categories, n_po)
    print("  generating po_lines (large)...")
    po_lines = _po_lines(ctx, purchase_orders, categories, lpp, emissions_factors)
    print(f"    {len(po_lines):,} po_lines")
    print("  generating receipts...")
    receipts = _receipts(ctx, po_lines, n_rec)
    print("  generating invoices...")
    invoices = _invoices(ctx, suppliers, purchase_orders, n_inv)
    print("  generating supplier_risk_assessments...")
    risk_assessments = _supplier_risk(ctx, suppliers, n_risk)
    print("  generating sustainability_attributes...")
    sustainability = _sustainability_attributes(ctx, suppliers, n_sus)
    print("  generating savings_events...")
    savings = _savings_events(ctx, suppliers, contracts, categories, n_sav)

    tables = {
        "category_taxonomy": categories,
        "supplier": suppliers,
        "contract": contracts,
        "purchase_order": purchase_orders,
        "po_line": po_lines,
        "receipt": receipts,
        "invoice": invoices,
        "supplier_risk_assessment": risk_assessments,
        "emissions_factor": emissions_factors,
        "sustainability_attribute": sustainability,
        "savings_event": savings,
    }
    for name, df in tables.items():
        write_table(SUBDOMAIN, name, df)
    return tables


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--scale", choices=list(SCALE_PRESETS.keys()), default="medium")
    args = p.parse_args()
    tables = generate(args.seed, args.scale)
    print()
    for name, df in tables.items():
        print(f"  {SUBDOMAIN}.{name}: {len(df):,} rows")


if __name__ == "__main__":
    main()
