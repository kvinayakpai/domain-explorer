"""
Synthetic Payments data.

Entities (10): mcc_codes, customers, accounts, merchants, payment_instructions,
payments, settlements, chargebacks, disputes, fraud_alerts.

Schema is held stable by the dbt staging models under
``modeling/dbt/models/payments/staging/`` -- column names below must match
``stg_payments__*.sql`` or downstream marts will break.

Run:
    python synthetic-data/payments/generate.py --seed 42
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

# Allow `python synthetic-data/payments/generate.py` direct invocation.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from common import (
    GenContext,
    country_codes,
    currency_codes,
    daterange_minutes,
    lognormal_amounts,
    make_context,
    weighted_choice,
    write_table,
)

SUBDOMAIN = "payments"


# Curated subset of common ISO 18245 Merchant Category Codes used both as the
# canonical mcc_codes reference table and as the FK pool for merchants. The
# table is then padded with deterministic synthetic codes to reach ~300 rows.
_CURATED_MCCS: list[tuple[str, str, str]] = [
    ("4111", "Local Commuter Transport", "Travel"),
    ("4121", "Taxicabs and Limousines", "Travel"),
    ("4131", "Bus Lines", "Travel"),
    ("4214", "Motor Freight Carriers", "Travel"),
    ("4411", "Cruise Lines", "Travel"),
    ("4511", "Airlines, Air Carriers", "Travel"),
    ("4582", "Airports, Flying Fields", "Travel"),
    ("4722", "Travel Agencies", "Travel"),
    ("4784", "Tolls, Bridge Fees", "Travel"),
    ("4789", "Transportation Services", "Travel"),
    ("4812", "Telecom Equipment", "Telecom"),
    ("4814", "Telecom Services", "Telecom"),
    ("4815", "Monthly Telephone Charges", "Telecom"),
    ("4816", "Computer Network Services", "Telecom"),
    ("4821", "Telegraph Services", "Telecom"),
    ("4829", "Wires, Money Orders", "Financial"),
    ("4899", "Cable, Satellite, Pay TV", "Telecom"),
    ("4900", "Utilities - Electric, Gas, Water", "Utilities"),
    ("5013", "Motor Vehicle Supplies", "Retail"),
    ("5021", "Office and Commercial Furniture", "Retail"),
    ("5039", "Construction Materials", "Retail"),
    ("5044", "Office, Photographic Equipment", "Retail"),
    ("5045", "Computers, Peripherals, Software", "Retail"),
    ("5065", "Electrical Parts and Equipment", "Retail"),
    ("5072", "Hardware Equipment and Supplies", "Retail"),
    ("5074", "Plumbing and Heating Equipment", "Retail"),
    ("5085", "Industrial Supplies", "Retail"),
    ("5111", "Stationery, Office Supplies", "Retail"),
    ("5122", "Drugs, Druggists Sundries", "Healthcare"),
    ("5131", "Piece Goods, Notions", "Retail"),
    ("5137", "Mens and Womens Uniforms", "Retail"),
    ("5139", "Commercial Footwear", "Retail"),
    ("5169", "Chemicals and Allied Products", "Retail"),
    ("5172", "Petroleum Products", "Travel"),
    ("5192", "Books, Periodicals, Newspapers", "Retail"),
    ("5193", "Florists Supplies, Nursery Stock", "Retail"),
    ("5198", "Paints, Varnishes, Supplies", "Retail"),
    ("5199", "Nondurable Goods", "Retail"),
    ("5200", "Home Supply Warehouse Stores", "Retail"),
    ("5211", "Lumber, Building Materials", "Retail"),
    ("5231", "Glass, Paint, Wallpaper", "Retail"),
    ("5251", "Hardware Stores", "Retail"),
    ("5261", "Nurseries, Lawn and Garden", "Retail"),
    ("5271", "Mobile Home Dealers", "Retail"),
    ("5300", "Wholesale Clubs", "Retail"),
    ("5309", "Duty Free Stores", "Retail"),
    ("5310", "Discount Stores", "Retail"),
    ("5311", "Department Stores", "Retail"),
    ("5331", "Variety Stores", "Retail"),
    ("5399", "Misc General Merchandise", "Retail"),
    ("5411", "Grocery Stores, Supermarkets", "Food"),
    ("5422", "Freezer Meat Provisioners", "Food"),
    ("5441", "Candy, Nut, Confectionery", "Food"),
    ("5451", "Dairy Products Stores", "Food"),
    ("5462", "Bakeries", "Food"),
    ("5499", "Misc Food Stores", "Food"),
    ("5511", "Car and Truck Dealers", "Travel"),
    ("5521", "Used Car Dealers", "Travel"),
    ("5531", "Auto and Home Supply Stores", "Travel"),
    ("5532", "Automotive Tire Stores", "Travel"),
    ("5533", "Automotive Parts and Accessories", "Travel"),
    ("5541", "Service Stations", "Travel"),
    ("5542", "Automated Fuel Dispensers", "Travel"),
    ("5551", "Boat Dealers", "Travel"),
    ("5561", "Motorcycle Shops and Dealers", "Travel"),
    ("5571", "Recreational Vehicle Dealers", "Travel"),
    ("5592", "Motor Home Dealers", "Travel"),
    ("5598", "Snowmobile Dealers", "Travel"),
    ("5599", "Misc Auto Dealers", "Travel"),
    ("5611", "Mens and Boys Clothing Stores", "Retail"),
    ("5621", "Womens Ready-To-Wear Stores", "Retail"),
    ("5631", "Womens Accessory Stores", "Retail"),
    ("5641", "Childrens and Infants Wear", "Retail"),
    ("5651", "Family Clothing Stores", "Retail"),
    ("5655", "Sports and Riding Apparel", "Retail"),
    ("5661", "Shoe Stores", "Retail"),
    ("5681", "Furriers and Fur Shops", "Retail"),
    ("5691", "Mens and Womens Clothing", "Retail"),
    ("5697", "Tailors, Seamstress, Alterations", "Services"),
    ("5698", "Wig and Toupee Stores", "Retail"),
    ("5699", "Misc Apparel and Accessory Shops", "Retail"),
    ("5712", "Furniture, Home Furnishings", "Retail"),
    ("5713", "Floor Covering Stores", "Retail"),
    ("5714", "Drapery, Window Coverings", "Retail"),
    ("5718", "Fireplace, Fireplace Accessories", "Retail"),
    ("5719", "Misc Home Furnishing Specialty", "Retail"),
    ("5722", "Household Appliance Stores", "Retail"),
    ("5732", "Electronics Stores", "Retail"),
    ("5733", "Music Stores - Instruments", "Retail"),
    ("5734", "Computer Software Stores", "Retail"),
    ("5735", "Record Shops", "Retail"),
    ("5811", "Caterers", "Food"),
    ("5812", "Eating Places and Restaurants", "Food"),
    ("5813", "Drinking Places, Bars, Lounges", "Food"),
    ("5814", "Fast Food Restaurants", "Food"),
    ("5912", "Drug Stores, Pharmacies", "Healthcare"),
    ("5921", "Package Stores - Beer, Wine", "Food"),
    ("5931", "Used Merchandise and Secondhand", "Retail"),
    ("5932", "Antique Shops", "Retail"),
    ("5933", "Pawn Shops", "Retail"),
    ("5935", "Wrecking and Salvage Yards", "Services"),
    ("5937", "Antique Reproductions", "Retail"),
    ("5940", "Bicycle Shops", "Retail"),
    ("5941", "Sporting Goods Stores", "Retail"),
    ("5942", "Book Stores", "Retail"),
    ("5943", "Stationery, Office, School Supply", "Retail"),
    ("5944", "Jewelry Stores", "Retail"),
    ("5945", "Hobby, Toy, Game Shops", "Retail"),
    ("5946", "Camera and Photographic Stores", "Retail"),
    ("5947", "Gift, Card, Novelty, Souvenir", "Retail"),
    ("5948", "Luggage and Leather Goods", "Retail"),
    ("5949", "Sewing, Needlework, Fabric", "Retail"),
    ("5950", "Glassware, Crystal Stores", "Retail"),
    ("5960", "Direct Marketing - Insurance", "Financial"),
    ("5962", "Direct Marketing - Travel", "Travel"),
    ("5963", "Door-To-Door Sales", "Retail"),
    ("5964", "Direct Marketing - Catalog", "Retail"),
    ("5965", "Direct Marketing - Combined", "Retail"),
    ("5966", "Direct Marketing - Outbound Tele", "Retail"),
    ("5967", "Direct Marketing - Inbound Tele", "Retail"),
    ("5968", "Direct Marketing - Subscription", "Retail"),
    ("5969", "Direct Marketing - Other", "Retail"),
    ("5970", "Artists Supply and Craft Shops", "Retail"),
    ("5971", "Art Dealers and Galleries", "Retail"),
    ("5972", "Stamp and Coin Stores", "Retail"),
    ("5973", "Religious Goods Stores", "Retail"),
    ("5975", "Hearing Aids - Sales and Service", "Healthcare"),
    ("5976", "Orthopedic Goods", "Healthcare"),
    ("5977", "Cosmetic Stores", "Retail"),
    ("5978", "Typewriter Stores", "Retail"),
    ("5983", "Fuel Dealers", "Travel"),
    ("5992", "Florists", "Retail"),
    ("5993", "Cigar Stores and Stands", "Retail"),
    ("5994", "News Dealers, Newsstands", "Retail"),
    ("5995", "Pet Shops, Pet Food", "Retail"),
    ("5996", "Swimming Pools - Sales", "Retail"),
    ("5997", "Electric Razor Stores", "Retail"),
    ("5998", "Tent and Awning Shops", "Retail"),
    ("5999", "Misc Specialty Retail", "Retail"),
    ("6010", "Financial Inst - Manual Cash", "Financial"),
    ("6011", "Financial Inst - ATM", "Financial"),
    ("6012", "Financial Inst - Merchandise", "Financial"),
    ("6051", "Foreign Currency, Money Orders", "Financial"),
    ("6211", "Securities - Brokers/Dealers", "Financial"),
    ("6300", "Insurance Sales", "Financial"),
    ("6513", "Real Estate Agents", "Financial"),
    ("7011", "Lodging - Hotels, Motels, Resorts", "Travel"),
    ("7012", "Timeshares", "Travel"),
    ("7032", "Sporting and Recreational Camps", "Travel"),
    ("7033", "Trailer Parks and Campgrounds", "Travel"),
    ("7210", "Laundry, Cleaning Services", "Services"),
    ("7211", "Laundries - Family", "Services"),
    ("7216", "Dry Cleaners", "Services"),
    ("7217", "Carpet Upholstery Cleaning", "Services"),
    ("7221", "Photographic Studios", "Services"),
    ("7230", "Beauty and Barber Shops", "Services"),
    ("7251", "Shoe Repair, Hat Cleaning", "Services"),
    ("7261", "Funeral Services", "Services"),
    ("7273", "Dating Services", "Services"),
    ("7276", "Tax Preparation Services", "Services"),
    ("7277", "Counseling Services", "Services"),
    ("7278", "Buying/Shopping Services", "Services"),
    ("7296", "Costume Rental", "Services"),
    ("7297", "Massage Parlors", "Services"),
    ("7298", "Health and Beauty Spas", "Services"),
    ("7299", "Other Personal Services", "Services"),
    ("7311", "Advertising Services", "Services"),
    ("7321", "Consumer Credit Reporting", "Financial"),
    ("7333", "Commercial Photography", "Services"),
    ("7338", "Quick Copy, Reproduction", "Services"),
    ("7339", "Stenographic, Secretarial", "Services"),
    ("7342", "Exterminating Services", "Services"),
    ("7349", "Cleaning, Maintenance Services", "Services"),
    ("7361", "Employment Agencies", "Services"),
    ("7372", "Computer Programming, Data Proc", "Services"),
    ("7375", "Information Retrieval Services", "Services"),
    ("7379", "Computer Maintenance, Repair", "Services"),
    ("7392", "Management, Consulting Services", "Services"),
    ("7393", "Detective Agencies", "Services"),
    ("7394", "Equipment Rental, Leasing", "Services"),
    ("7395", "Photofinishing Labs", "Services"),
    ("7399", "Business Services", "Services"),
    ("7512", "Auto Rental Agencies", "Travel"),
    ("7513", "Truck Rentals", "Travel"),
    ("7519", "Motor Home and RV Rentals", "Travel"),
    ("7523", "Parking Lots, Garages", "Travel"),
    ("7531", "Auto Body Repair Shops", "Services"),
    ("7534", "Tire Retreading and Repair", "Services"),
    ("7535", "Auto Paint Shops", "Services"),
    ("7538", "Auto Service Shops", "Services"),
    ("7542", "Car Washes", "Services"),
    ("7549", "Towing Services", "Services"),
    ("7622", "Radio Repair Shops", "Services"),
    ("7623", "A/C, Refrigeration Repair", "Services"),
    ("7629", "Electrical Appliance Repair", "Services"),
    ("7631", "Watch, Clock, Jewelry Repair", "Services"),
    ("7641", "Furniture Reupholstery and Repair", "Services"),
    ("7692", "Welding Repair", "Services"),
    ("7699", "Misc Repair Shops", "Services"),
    ("7829", "Motion Picture and Video Production", "Entertainment"),
    ("7832", "Motion Picture Theaters", "Entertainment"),
    ("7841", "Video Rental Stores", "Entertainment"),
    ("7911", "Dance Halls, Studios, Schools", "Entertainment"),
    ("7922", "Theatrical Producers, Tickets", "Entertainment"),
    ("7929", "Bands, Orchestras, Entertainers", "Entertainment"),
    ("7932", "Billiard, Pool Establishments", "Entertainment"),
    ("7933", "Bowling Alleys", "Entertainment"),
    ("7941", "Athletic Fields, Sports Clubs", "Entertainment"),
    ("7991", "Tourist Attractions, Exhibits", "Entertainment"),
    ("7992", "Public Golf Courses", "Entertainment"),
    ("7993", "Video Amusement Game Supplies", "Entertainment"),
    ("7994", "Video Game Arcades", "Entertainment"),
    ("7995", "Betting, Casino Gaming", "Entertainment"),
    ("7996", "Amusement Parks, Carnivals", "Entertainment"),
    ("7997", "Membership Clubs", "Entertainment"),
    ("7998", "Aquariums, Zoos", "Entertainment"),
    ("7999", "Recreation Services", "Entertainment"),
    ("8011", "Doctors", "Healthcare"),
    ("8021", "Dentists, Orthodontists", "Healthcare"),
    ("8031", "Osteopaths", "Healthcare"),
    ("8041", "Chiropractors", "Healthcare"),
    ("8042", "Optometrists", "Healthcare"),
    ("8043", "Opticians", "Healthcare"),
    ("8049", "Podiatrists", "Healthcare"),
    ("8050", "Nursing and Personal Care", "Healthcare"),
    ("8062", "Hospitals", "Healthcare"),
    ("8071", "Medical and Dental Labs", "Healthcare"),
    ("8099", "Medical Services", "Healthcare"),
    ("8111", "Legal Services, Attorneys", "Services"),
    ("8211", "Elementary, Secondary Schools", "Education"),
    ("8220", "Colleges, Universities", "Education"),
    ("8241", "Correspondence Schools", "Education"),
    ("8244", "Business and Secretarial Schools", "Education"),
    ("8249", "Vocational, Trade Schools", "Education"),
    ("8299", "Educational Services", "Education"),
    ("8351", "Child Care Services", "Services"),
    ("8398", "Charitable and Social Service Orgs", "Services"),
    ("8641", "Civic, Social, Fraternal Assn", "Services"),
    ("8651", "Political Organizations", "Services"),
    ("8661", "Religious Organizations", "Services"),
    ("8675", "Automobile Associations", "Services"),
    ("8699", "Membership Organizations", "Services"),
    ("8911", "Architectural, Engineering", "Services"),
    ("8931", "Accounting, Auditing, Bookkeeping", "Services"),
    ("8999", "Professional Services", "Services"),
    ("9211", "Court Costs, Alimony", "Government"),
    ("9222", "Fines", "Government"),
    ("9223", "Bail and Bond Payments", "Government"),
    ("9311", "Tax Payments", "Government"),
    ("9399", "Government Services", "Government"),
    ("9402", "Postal Services", "Government"),
    ("9405", "U.S. Federal Government Agencies", "Government"),
    ("9700", "Automated Referral Services", "Services"),
    ("9751", "U.K. VAT Tax Payments", "Government"),
    ("9752", "U.K. Specific Supply Services", "Government"),
    ("9950", "Intra-Company Purchases", "Financial"),
]


def _mcc_codes(ctx: GenContext, n_target: int = 300) -> pd.DataFrame:
    """ISO 18245 reference table (~300 rows). Curated codes plus deterministic
    synthetic filler so the table reaches ``n_target`` rows."""
    rng = ctx.rng
    seen: set[str] = set()
    rows: list[tuple[str, str, str]] = []
    for mcc, desc, cat in _CURATED_MCCS:
        if mcc in seen:
            continue
        seen.add(mcc)
        rows.append((mcc, desc, cat))

    fillers_needed = max(0, n_target - len(rows))
    if fillers_needed:
        candidates = rng.choice(np.arange(1000, 10_000), size=fillers_needed * 3, replace=False)
        synth_categories = ["Other", "Retail", "Services", "Financial", "Travel"]
        cat_pick = rng.choice(synth_categories, size=fillers_needed * 3)
        added = 0
        for code, cat in zip(candidates, cat_pick, strict=False):
            if added >= fillers_needed:
                break
            mcc = f"{int(code):04d}"
            if mcc in seen:
                continue
            seen.add(mcc)
            rows.append((mcc, f"Reserved/Other Category {mcc}", str(cat)))
            added += 1

    return pd.DataFrame(rows, columns=["mcc", "description", "category"])


def _customers(ctx: GenContext, n: int = 10_000) -> pd.DataFrame:
    rng = ctx.rng
    f = ctx.faker
    countries = np.array(country_codes())
    return pd.DataFrame(
        {
            "customer_id": [f"CUS{i:08d}" for i in range(1, n + 1)],
            "full_name": [f.name() for _ in range(n)],
            "email": [f.unique.email() for _ in range(n)],
            "country": rng.choice(countries, size=n),
            "kyc_status": weighted_choice(
                rng, ["verified", "pending", "rejected"], [0.88, 0.10, 0.02], n
            ),
            "risk_segment": weighted_choice(
                rng, ["low", "medium", "high"], [0.70, 0.25, 0.05], n
            ),
            "signup_date": pd.to_datetime(
                rng.integers(
                    int(pd.Timestamp("2018-01-01").timestamp()),
                    int(pd.Timestamp("2025-12-31").timestamp()),
                    size=n,
                ),
                unit="s",
            ).date,
        }
    )


def _accounts(ctx: GenContext, customers: pd.DataFrame, mult: float = 1.4) -> pd.DataFrame:
    rng = ctx.rng
    n = int(len(customers) * mult)
    cust_ids = rng.choice(customers["customer_id"].to_numpy(), size=n)
    return pd.DataFrame(
        {
            "account_id": [f"ACC{i:09d}" for i in range(1, n + 1)],
            "customer_id": cust_ids,
            "account_type": weighted_choice(
                rng,
                ["checking", "savings", "credit_card", "wallet"],
                [0.45, 0.20, 0.25, 0.10],
                n,
            ),
            "currency": weighted_choice(
                rng,
                currency_codes(),
                [0.40, 0.20, 0.15, 0.05, 0.05, 0.05, 0.03, 0.03, 0.02, 0.02],
                n,
            ),
            "open_date": pd.to_datetime(
                rng.integers(
                    int(pd.Timestamp("2018-01-01").timestamp()),
                    int(pd.Timestamp("2026-01-01").timestamp()),
                    size=n,
                ),
                unit="s",
            ).date,
            "status": weighted_choice(rng, ["active", "frozen", "closed"], [0.92, 0.04, 0.04], n),
        }
    )


def _merchants(ctx: GenContext, mcc_codes: pd.DataFrame, n: int = 10_000) -> pd.DataFrame:
    """Merchant master. ``mcc`` is an FK into mcc_codes."""
    rng = ctx.rng
    f = ctx.faker
    common_mccs = mcc_codes[mcc_codes["category"].isin(
        ["Retail", "Food", "Travel", "Services", "Healthcare", "Telecom", "Entertainment"]
    )]
    pool = (
        common_mccs["mcc"].to_numpy()
        if len(common_mccs) >= 30
        else mcc_codes["mcc"].to_numpy()
    )
    chosen_mcc = rng.choice(pool, size=n)
    desc_lookup = dict(zip(mcc_codes["mcc"].to_numpy(), mcc_codes["description"].to_numpy(), strict=True))
    cat_lookup = dict(zip(mcc_codes["mcc"].to_numpy(), mcc_codes["category"].to_numpy(), strict=True))
    return pd.DataFrame(
        {
            "merchant_id": [f"MER{i:08d}" for i in range(1, n + 1)],
            "merchant_name": [f.company() for _ in range(n)],
            "mcc": chosen_mcc,
            "description": [desc_lookup[m] for m in chosen_mcc],
            "category": [cat_lookup[m] for m in chosen_mcc],
            "country": rng.choice(country_codes(), size=n),
        }
    )


def _payment_instructions(
    ctx: GenContext, accounts: pd.DataFrame, n: int = 12_000
) -> pd.DataFrame:
    rng = ctx.rng
    src = rng.choice(accounts["account_id"].to_numpy(), size=n)
    dst = rng.choice(accounts["account_id"].to_numpy(), size=n)
    return pd.DataFrame(
        {
            "instruction_id": [f"PIN{i:09d}" for i in range(1, n + 1)],
            "source_account_id": src,
            "dest_account_id": dst,
            "rail": weighted_choice(
                rng, ["card", "ach", "wire", "rtp", "sepa"], [0.55, 0.25, 0.05, 0.10, 0.05], n
            ),
            "amount": lognormal_amounts(rng, n, mean=4.0, sigma=1.1),
            "currency": weighted_choice(
                rng,
                ["USD", "EUR", "GBP", "JPY", "AUD", "CAD", "CHF", "INR", "SGD", "BRL"],
                [0.60, 0.20, 0.10, 0.025, 0.02, 0.02, 0.01, 0.01, 0.01, 0.005],
                n,
            ),
            "created_at": daterange_minutes(
                rng, n, pd.Timestamp("2024-01-01"), pd.Timestamp("2026-04-30")
            ),
            "status": weighted_choice(
                rng, ["pending", "submitted", "completed", "rejected"], [0.05, 0.10, 0.80, 0.05], n
            ),
        }
    )


def _payments(
    ctx: GenContext,
    instructions: pd.DataFrame,
    merchants: pd.DataFrame,
    n: int = 200_000,
) -> pd.DataFrame:
    rng = ctx.rng
    inst_completed = instructions[instructions["status"].isin(["completed", "submitted"])]
    inst_ids = rng.choice(inst_completed["instruction_id"].to_numpy(), size=n)
    auth_ts = daterange_minutes(rng, n, pd.Timestamp("2024-01-01"), pd.Timestamp("2026-04-30"))

    # Bimodal settlement latency: most clear in <1h, ~7% take 24-96h. Tuned so
    # p95 settlement latency lands near 29h.
    fast = rng.normal(0.4, 0.25, size=n).clip(0.05, 12)
    slow = rng.normal(36, 12, size=n).clip(2, 96)
    pick_slow = rng.random(n) < 0.07
    latency_h = np.where(pick_slow, slow, fast)
    settlement_ts = auth_ts + pd.to_timedelta(latency_h, unit="h")

    rail = weighted_choice(
        rng, ["card", "ach", "wire", "rtp", "sepa"], [0.55, 0.25, 0.05, 0.10, 0.05], n
    )
    auth_failed = rng.random(n) < 0.06
    merchant_idx = rng.integers(0, len(merchants), size=n)
    merch_arr = merchants["merchant_id"].to_numpy()[merchant_idx]
    mcc_arr = merchants["mcc"].to_numpy()[merchant_idx]

    return pd.DataFrame(
        {
            "payment_id": [f"PAY{i:010d}" for i in range(1, n + 1)],
            "instruction_id": inst_ids,
            "rail": rail,
            "merchant_id": merch_arr,
            "mcc": mcc_arr,
            "amount": lognormal_amounts(rng, n, mean=3.8, sigma=1.0),
            "currency": weighted_choice(
                rng,
                ["USD", "EUR", "GBP", "JPY", "AUD", "CAD", "CHF", "INR", "SGD", "BRL"],
                [0.60, 0.20, 0.10, 0.025, 0.02, 0.02, 0.01, 0.01, 0.01, 0.005],
                n,
            ),
            "auth_ts": auth_ts,
            "settlement_ts": settlement_ts,
            "auth_status": np.where(auth_failed, "declined", "approved"),
            "is_stp": np.where(auth_failed, False, rng.random(n) < 0.92),
            "interchange_amount": np.round(rng.uniform(0.05, 1.8, size=n), 2),
            "country": rng.choice(country_codes(), size=n),
        }
    )


def _settlements(ctx: GenContext, payments: pd.DataFrame) -> pd.DataFrame:
    rng = ctx.rng
    approved = payments[payments["auth_status"] == "approved"].copy()
    n = len(approved)
    return pd.DataFrame(
        {
            "settlement_id": [f"STL{i:010d}" for i in range(1, n + 1)],
            "payment_id": approved["payment_id"].to_numpy(),
            "amount": approved["amount"].to_numpy(),
            "currency": approved["currency"].to_numpy(),
            "settled_at": approved["settlement_ts"].to_numpy(),
            "batch_id": [f"BTH{rng.integers(1, 5_000):05d}" for _ in range(n)],
            "fee_amount": np.round(
                approved["amount"].to_numpy() * rng.uniform(0.001, 0.029, size=n), 2
            ),
            "network": weighted_choice(
                rng,
                ["VISA", "MC", "AMEX", "ACH", "SWIFT", "RTP"],
                [0.45, 0.30, 0.05, 0.12, 0.04, 0.04],
                n,
            ),
        }
    )


def _chargebacks(ctx: GenContext, payments: pd.DataFrame) -> pd.DataFrame:
    rng = ctx.rng
    card = payments[payments["rail"] == "card"]
    target = max(10_000, int(len(card) * 0.10))
    cb_idx = rng.choice(len(card), size=min(target, len(card)), replace=False)
    cb = card.iloc[cb_idx].copy().reset_index(drop=True)
    n = len(cb)
    return pd.DataFrame(
        {
            "chargeback_id": [f"CB{i:09d}" for i in range(1, n + 1)],
            "payment_id": cb["payment_id"].to_numpy(),
            "reason_code": weighted_choice(
                rng, ["10.4", "13.1", "13.2", "11.3", "12.6"], [0.30, 0.25, 0.20, 0.15, 0.10], n
            ),
            "amount": cb["amount"].to_numpy(),
            "filed_at": pd.to_datetime(cb["auth_ts"].to_numpy())
            + pd.to_timedelta(rng.integers(1, 60, size=n), unit="D"),
            "status": weighted_choice(rng, ["open", "won", "lost"], [0.18, 0.42, 0.40], n),
        }
    )


def _disputes(ctx: GenContext, chargebacks: pd.DataFrame) -> pd.DataFrame:
    rng = ctx.rng
    disputed = chargebacks[chargebacks["status"].isin(["open", "won", "lost"])]
    n = max(10_000, len(disputed))
    if n > len(disputed):
        extra = n - len(disputed)
        opened_at_extra = daterange_minutes(
            rng, extra, pd.Timestamp("2024-02-01"), pd.Timestamp("2026-04-30")
        )
        df = pd.DataFrame(
            {
                "dispute_id": [f"DSP{i:09d}" for i in range(1, n + 1)],
                "chargeback_id": list(disputed["chargeback_id"].to_numpy()) + [None] * extra,
                "opened_ts": list(disputed["filed_at"].to_numpy()) + list(opened_at_extra),
                "category": weighted_choice(
                    rng,
                    ["fraud", "non_receipt", "duplicate", "quality", "billing"],
                    [0.40, 0.25, 0.10, 0.15, 0.10],
                    n,
                ),
                "amount": list(disputed["amount"].to_numpy())
                + list(lognormal_amounts(rng, extra, 4.0, 0.8)),
            }
        )
    else:
        df = pd.DataFrame(
            {
                "dispute_id": [f"DSP{i:09d}" for i in range(1, n + 1)],
                "chargeback_id": disputed["chargeback_id"].to_numpy()[:n],
                "opened_ts": disputed["filed_at"].to_numpy()[:n],
                "category": weighted_choice(
                    rng,
                    ["fraud", "non_receipt", "duplicate", "quality", "billing"],
                    [0.40, 0.25, 0.10, 0.15, 0.10],
                    n,
                ),
                "amount": disputed["amount"].to_numpy()[:n],
            }
        )
    res_days = rng.integers(1, 90, size=n)
    df["resolved_ts"] = pd.to_datetime(df["opened_ts"]) + pd.to_timedelta(res_days, unit="D")
    df["status"] = weighted_choice(
        rng, ["pending", "resolved_customer", "resolved_merchant"], [0.10, 0.55, 0.35], n
    )
    return df


def _fraud_alerts(
    ctx: GenContext, payments: pd.DataFrame, n: int = 10_000
) -> pd.DataFrame:
    rng = ctx.rng
    pid = rng.choice(payments["payment_id"].to_numpy(), size=n)
    return pd.DataFrame(
        {
            "alert_id": [f"FRA{i:09d}" for i in range(1, n + 1)],
            "payment_id": pid,
            "score": np.round(rng.beta(2, 5, size=n), 4),
            "model_version": rng.choice(["v3.4", "v3.5", "v4.0", "v4.1"], size=n),
            "rule_set": weighted_choice(
                rng,
                ["velocity", "geo_mismatch", "device_change", "ml_only", "manual"],
                [0.30, 0.20, 0.15, 0.30, 0.05],
                n,
            ),
            "raised_at": daterange_minutes(
                rng, n, pd.Timestamp("2024-01-01"), pd.Timestamp("2026-04-30")
            ),
            "outcome": weighted_choice(
                rng,
                ["true_positive", "false_positive", "review", "auto_block"],
                [0.18, 0.55, 0.20, 0.07],
                n,
            ),
        }
    )


def generate(seed: int = 42) -> dict[str, pd.DataFrame]:
    ctx = make_context(seed)
    mcc_codes = _mcc_codes(ctx)
    customers = _customers(ctx)
    accounts = _accounts(ctx, customers)
    merchants = _merchants(ctx, mcc_codes)
    instructions = _payment_instructions(ctx, accounts)
    payments = _payments(ctx, instructions, merchants)
    settlements = _settlements(ctx, payments)
    chargebacks = _chargebacks(ctx, payments)
    disputes = _disputes(ctx, chargebacks)
    fraud_alerts = _fraud_alerts(ctx, payments)

    tables = {
        "mcc_codes": mcc_codes,
        "customers": customers,
        "accounts": accounts,
        "merchants": merchants,
        "payment_instructions": instructions,
        "payments": payments,
        "settlements": settlements,
        "chargebacks": chargebacks,
        "disputes": disputes,
        "fraud_alerts": fraud_alerts,
    }
    for name, df in tables.items():
        write_table(SUBDOMAIN, name, df)
    return tables


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--seed", type=int, default=42)
    args = p.parse_args()
    tables = generate(args.seed)
    for name, df in tables.items():
        print(f"  {SUBDOMAIN}.{name}: {len(df):,} rows")


if __name__ == "__main__":
    main()
