"""
Synthetic Customer Loyalty + CDP data — Salesforce Data Cloud / Adobe RT-CDP /
Treasure Data / mParticle / Tealium / Segment / BlueShift / Klaviyo / Braze /
Iterable / Twilio Engage / ActionIQ / Amperity / Epsilon PeopleCloud / Cordial
on the CDP side; Eagle Eye / Annex Cloud / Comarch / LoyaltyLion / Smile.io on
the loyalty side.

Entities (>=10):
  customer_master, identity_link, event, segment, segment_membership,
  loyalty_account, points_ledger, reward, redemption, preference_center,
  consent_record.

Realism:
  - Power-law identifier counts per customer (5 avg with long tail to 25+).
  - Event mix skewed to page_view / product_view; purchases ~2% of events.
  - 40% loyalty enrollment rate; tier distribution heavy on bronze/silver.
  - Points liability tracked under ASC 606 cash-equivalent valuation.
  - Segment memberships favour evergreen segments (RFM cells, lifecycle stages).
  - GDPR / CCPA / CPRA consent split by jurisdiction proportional to country mix.
  - All large-range integer IDs use the int64-safe pattern (rng.integers +
    zero-padded format string) from capital_markets/generate.py.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from common import make_context, weighted_choice, write_table

SUBDOMAIN = "customer_loyalty_cdp"

# ---------------------------------------------------------------------------
# Reference universes

COUNTRIES = ["US", "GB", "DE", "FR", "JP", "CA", "AU", "IN", "BR", "SG", "NL", "ES", "IT", "MX"]
COUNTRY_W = [0.40, 0.10, 0.07, 0.06, 0.05, 0.05, 0.04, 0.05, 0.04, 0.03, 0.04, 0.03, 0.02, 0.02]
LIFECYCLE = ["prospect", "new", "active", "lapsed", "churned", "reactivated", "vip"]
LIFECYCLE_W = [0.08, 0.12, 0.42, 0.18, 0.10, 0.06, 0.04]
RES_METHODS = ["deterministic", "probabilistic", "hybrid", "manual_merge"]
RES_METHOD_W = [0.55, 0.20, 0.23, 0.02]
GOLDEN_SRC = ["amperity", "salesforce_dc", "adobe_rtcdp", "treasure_data", "in_house"]
GOLDEN_W = [0.32, 0.26, 0.20, 0.12, 0.10]

ID_TYPES = ["email_sha256", "phone_sha256", "loyalty_id", "device_id", "maid",
            "fbp", "ga_client_id", "cookie_id", "postal_addr", "wallet_pass"]
ID_TYPE_W = [0.20, 0.12, 0.08, 0.18, 0.10, 0.08, 0.10, 0.08, 0.04, 0.02]

CDP_SOURCES = ["salesforce_dc", "adobe_rtcdp", "amperity", "segment", "mparticle",
               "tealium", "treasure_data", "klaviyo", "braze", "iterable",
               "epsilon", "actioniq", "blueshift", "cordial", "twilio_engage"]

EVENT_TYPES = ["page_view", "product_view", "search", "add_to_cart", "purchase",
               "email_send", "email_open", "email_click", "push_send", "push_open",
               "sms_send", "store_visit", "app_open", "review_submit", "return"]
EVENT_TYPE_W = [0.28, 0.20, 0.08, 0.06, 0.02, 0.07, 0.05, 0.03, 0.05, 0.03, 0.02, 0.04, 0.05, 0.01, 0.01]

CHANNELS = ["web", "app", "email", "push", "sms", "in_store", "call_center", "chat"]
CHANNEL_W = [0.36, 0.24, 0.14, 0.08, 0.05, 0.08, 0.03, 0.02]

SEG_KINDS = ["rfm", "behavioural", "predictive", "rules", "lookalike", "suppression"]
SEG_KIND_W = [0.25, 0.30, 0.15, 0.20, 0.05, 0.05]
SEG_REFRESH = ["realtime", "hourly", "daily", "weekly"]
SEG_REFRESH_W = [0.20, 0.15, 0.50, 0.15]
SEG_TEAMS = ["CRM", "Lifecycle", "Loyalty", "Insights", "Paid Media", "Data Science"]
SEG_DESTS = [
    '["klaviyo","meta_audiences"]',
    '["braze","google_audiences"]',
    '["iterable","tiktok"]',
    '["paid_search","meta_audiences"]',
    '["in_store_pos","klaviyo"]',
    '["sms_only"]',
    '["meta_audiences","google_audiences","tiktok"]',
    '["braze","iterable","klaviyo"]',
    '["suppression_only"]',
]

ENTRY_REASONS = ["rfm_recalc", "behavioural_trigger", "predictive_score_xover", "manual"]
ENTRY_REASON_W = [0.45, 0.30, 0.20, 0.05]

PROGRAMS = ["BRAND_LOYAL", "REWARDS_PLUS", "INSIDER_CLUB", "VIP_BLACK"]
PROGRAM_W = [0.55, 0.25, 0.15, 0.05]
TIERS = ["bronze", "silver", "gold", "platinum", "black", "founder"]
TIER_W = [0.42, 0.30, 0.18, 0.07, 0.025, 0.005]
ENROLL_CHANNELS = ["web", "app", "in_store", "partner", "call_center"]
ENROLL_W = [0.40, 0.28, 0.22, 0.06, 0.04]
LOYALTY_STATUS = ["active", "paused", "expired", "closed", "fraud_hold"]
LOYALTY_STATUS_W = [0.86, 0.04, 0.06, 0.03, 0.01]

LEDGER_TYPES = ["earn", "redeem", "expire", "adjust", "transfer_in", "transfer_out", "bonus", "reversal"]
LEDGER_TYPE_W = [0.62, 0.18, 0.08, 0.04, 0.02, 0.01, 0.04, 0.01]

REWARD_TYPES = ["gift_card", "product_voucher", "discount_percent", "discount_amount",
                "partner_experience", "charitable_donation", "sweepstakes_entry"]
REWARD_TYPE_W = [0.18, 0.20, 0.22, 0.20, 0.08, 0.07, 0.05]
REWARD_VENDORS = ["Internal", "Starbucks", "Amazon", "Visa Prepaid", "Patagonia",
                  "DoorDash", "Spotify", "REI", "Sephora", "Nike"]

PREF_TOPICS = ["newsletter", "promotions", "order_updates", "loyalty_updates", "new_product", "partner_offers"]
PREF_STATES = ["opted_in", "opted_out", "paused", "never_set"]
PREF_STATE_W = [0.62, 0.18, 0.05, 0.15]

JURIS = ["EU_GDPR", "UK_GDPR", "US_CCPA", "US_CPRA", "CA_PIPEDA", "BR_LGPD", "other"]
JURIS_W = [0.28, 0.06, 0.20, 0.18, 0.05, 0.04, 0.19]
CONSENT_BASIS = ["consent", "contract", "legitimate_interest", "legal_obligation"]
CONSENT_BASIS_W = [0.55, 0.20, 0.20, 0.05]
CONSENT_ACTIONS = ["granted", "withdrawn", "updated", "right_to_delete", "right_to_portability", "complaint"]
CONSENT_ACTION_W = [0.55, 0.15, 0.20, 0.06, 0.03, 0.01]


# ---------------------------------------------------------------------------
def _customers(ctx, n=500_000):
    rng = ctx.rng
    res = weighted_choice(rng, RES_METHODS, RES_METHOD_W, n)
    base_conf = rng.beta(8, 2, size=n)
    conf = np.where(res == "manual_merge", 1.0,
                    np.where(res == "deterministic", np.clip(base_conf + 0.10, 0, 1.0),
                             np.where(res == "probabilistic", base_conf * 0.85,
                                      base_conf)))
    lifecycle = weighted_choice(rng, LIFECYCLE, LIFECYCLE_W, n)
    return pd.DataFrame({
        "customer_id":           [f"CUST{i:09d}" for i in range(1, n + 1)],
        "first_name_token":      [f"FNT-{rng.integers(10**9, 10**10):010d}" for _ in range(n)],
        "last_name_token":       [f"LNT-{rng.integers(10**9, 10**10):010d}" for _ in range(n)],
        "email_sha256":          [f"{rng.integers(10**15, 10**16):016d}" for _ in range(n)],
        "phone_sha256":          [f"{rng.integers(10**15, 10**16):016d}" for _ in range(n)],
        "country_iso2":          weighted_choice(rng, COUNTRIES, COUNTRY_W, n),
        "postal_code":           [f"{rng.integers(10000, 99999):05d}" for _ in range(n)],
        "golden_record_source":  weighted_choice(rng, GOLDEN_SRC, GOLDEN_W, n),
        "confidence_score":      np.round(conf, 4),
        "resolution_method":     res,
        "lifecycle_stage":       lifecycle,
        "rfm_recency":           rng.integers(1, 6, size=n).astype("int16"),
        "rfm_frequency":         rng.integers(1, 6, size=n).astype("int16"),
        "rfm_monetary":          rng.integers(1, 6, size=n).astype("int16"),
        "predicted_clv":         np.round(rng.lognormal(5.5, 1.0, size=n), 2),
        "predicted_churn_prob":  np.round(rng.beta(2, 5, size=n), 4),
        "first_seen_at":         pd.to_datetime(
                                     rng.integers(int(pd.Timestamp("2020-01-01").timestamp()),
                                                  int(pd.Timestamp("2026-04-01").timestamp()), size=n),
                                     unit="s"),
        "last_seen_at":          pd.to_datetime(
                                     rng.integers(int(pd.Timestamp("2025-06-01").timestamp()),
                                                  int(pd.Timestamp("2026-05-10").timestamp()), size=n),
                                     unit="s"),
        "created_at":            pd.to_datetime(
                                     rng.integers(int(pd.Timestamp("2020-01-01").timestamp()),
                                                  int(pd.Timestamp("2026-04-01").timestamp()), size=n),
                                     unit="s"),
        "updated_at":            pd.to_datetime(
                                     rng.integers(int(pd.Timestamp("2026-01-01").timestamp()),
                                                  int(pd.Timestamp("2026-05-10").timestamp()), size=n),
                                     unit="s"),
        "status":                weighted_choice(rng, ["active", "deleted", "suppressed", "right_to_be_forgotten"],
                                                 [0.95, 0.02, 0.02, 0.01], n),
    })


def _identity_links(ctx, customers, n=2_500_000):
    """5 identifiers per customer on average — total 2.5M edges."""
    rng = ctx.rng
    c_idx = rng.integers(0, len(customers), size=n)
    method = weighted_choice(rng, ["deterministic", "probabilistic", "merged", "manual"],
                             [0.55, 0.35, 0.08, 0.02], n)
    conf = np.where(method == "deterministic", 1.0,
                    np.where(method == "manual", 1.0,
                             np.where(method == "merged", rng.uniform(0.70, 0.95, size=n),
                                      rng.uniform(0.60, 0.99, size=n))))
    last_seen = pd.to_datetime(
        rng.integers(int(pd.Timestamp("2025-06-01").timestamp()),
                     int(pd.Timestamp("2026-05-10").timestamp()), size=n),
        unit="s")
    first_seen = last_seen - pd.to_timedelta(rng.integers(0, 365 * 3, size=n), unit="D")
    return pd.DataFrame({
        "identity_id":             [f"ID{i:012d}" for i in range(1, n + 1)],
        "customer_id":             customers["customer_id"].to_numpy()[c_idx],
        "identifier_type":         weighted_choice(rng, ID_TYPES, ID_TYPE_W, n),
        "identifier_value_hash":   [f"{rng.integers(10**15, 10**16):016d}" for _ in range(n)],
        "match_method":            method,
        "match_confidence":        np.round(conf, 4),
        "source_system":           rng.choice(CDP_SOURCES, size=n),
        "first_observed_at":       first_seen,
        "last_observed_at":        last_seen,
        "is_active":               rng.random(n) < 0.92,
    })


def _events(ctx, customers, n=1_000_000):
    rng = ctx.rng
    c_idx = rng.integers(0, len(customers), size=n)
    et = weighted_choice(rng, EVENT_TYPES, EVENT_TYPE_W, n)
    is_purchase = (et == "purchase")
    amount = np.where(is_purchase,
                      (rng.lognormal(4.0, 1.0, size=n) * 100).astype(np.int64),
                      np.where(et == "add_to_cart",
                               (rng.lognormal(3.8, 1.0, size=n) * 100).astype(np.int64),
                               0)).astype(np.int64)
    event_ts = pd.to_datetime(
        rng.integers(int(pd.Timestamp("2025-12-01").timestamp()),
                     int(pd.Timestamp("2026-05-10").timestamp()), size=n),
        unit="s")
    ingest_lag = rng.integers(1, 600, size=n)
    return pd.DataFrame({
        "event_id":          [f"EVT{i:012d}" for i in range(1, n + 1)],
        "customer_id":       customers["customer_id"].to_numpy()[c_idx],
        "anonymous_id":      [f"ANON-{rng.integers(10**11, 10**12):012d}" for _ in range(n)],
        "event_type":        et,
        "channel":           weighted_choice(rng, CHANNELS, CHANNEL_W, n),
        "source_system":     rng.choice(CDP_SOURCES, size=n),
        "campaign_id":       np.where(rng.random(n) < 0.55,
                                      [f"CMP{rng.integers(10**4, 10**5):05d}" for _ in range(n)],
                                      None),
        "journey_id":        np.where(rng.random(n) < 0.30,
                                      [f"JNY{rng.integers(10**3, 10**4):04d}" for _ in range(n)],
                                      None),
        "product_id":        np.where(np.isin(et, ["product_view", "add_to_cart", "purchase", "return"]),
                                      [f"PRD{rng.integers(10**5, 10**6):06d}" for _ in range(n)],
                                      None),
        "order_id":          np.where(np.isin(et, ["purchase", "return"]),
                                      [f"ORD{rng.integers(10**7, 10**8):08d}" for _ in range(n)],
                                      None),
        "amount_minor":      amount,
        "currency":          weighted_choice(rng, ["USD", "EUR", "GBP", "JPY", "CAD", "AUD"],
                                              [0.55, 0.18, 0.10, 0.07, 0.05, 0.05], n),
        "event_ts":          event_ts,
        "ingest_ts":         event_ts + pd.to_timedelta(ingest_lag, unit="s"),
        "properties_json":   [f'{{"v":{rng.integers(0, 1000)}}}' for _ in range(n)],
    })


def _segments(ctx, n=10):
    rng = ctx.rng
    names = [
        "RFM-Champions", "RFM-Loyal", "RFM-At-Risk", "RFM-Hibernating", "RFM-Cannot-Lose",
        "Behavioural-Cart-Abandoners", "Behavioural-Email-Engaged", "Predictive-High-CLV",
        "Predictive-Churn-Risk", "Lookalike-VIP",
    ]
    n = min(n, len(names))
    return pd.DataFrame({
        "segment_id":             [f"SEG{i:04d}" for i in range(1, n + 1)],
        "segment_name":           names[:n],
        "segment_kind":           weighted_choice(rng, SEG_KINDS, SEG_KIND_W, n),
        "definition_dsl":         [f'{{"rule":"v{i}"}}' for i in range(n)],
        "refresh_cadence":        weighted_choice(rng, SEG_REFRESH, SEG_REFRESH_W, n),
        "owning_team":            rng.choice(SEG_TEAMS, size=n),
        "activated_destinations": rng.choice(SEG_DESTS, size=n),
        "created_at":             pd.to_datetime(
                                      rng.integers(int(pd.Timestamp("2024-01-01").timestamp()),
                                                   int(pd.Timestamp("2026-01-01").timestamp()), size=n),
                                      unit="s"),
        "updated_at":             pd.to_datetime(
                                      rng.integers(int(pd.Timestamp("2026-01-01").timestamp()),
                                                   int(pd.Timestamp("2026-05-10").timestamp()), size=n),
                                      unit="s"),
        "status":                 weighted_choice(rng, ["draft", "active", "paused", "deprecated"],
                                                  [0.05, 0.85, 0.07, 0.03], n),
    })


def _segment_memberships(ctx, customers, segments, n=5_000_000):
    """10 segments × 500k customers = 5M membership rows."""
    rng = ctx.rng
    c_idx = rng.integers(0, len(customers), size=n)
    s_idx = rng.integers(0, len(segments), size=n)
    entered = pd.to_datetime(
        rng.integers(int(pd.Timestamp("2025-09-01").timestamp()),
                     int(pd.Timestamp("2026-05-08").timestamp()), size=n),
        unit="s")
    is_current = rng.random(n) < 0.62
    exit_offset_s = rng.integers(3600, 90 * 86400, size=n)
    exited = np.where(is_current, np.datetime64("NaT"),
                      entered + pd.to_timedelta(exit_offset_s, unit="s"))
    return pd.DataFrame({
        "membership_id":   [f"SMB{i:012d}" for i in range(1, n + 1)],
        "customer_id":     customers["customer_id"].to_numpy()[c_idx],
        "segment_id":      segments["segment_id"].to_numpy()[s_idx],
        "entered_at":      entered,
        "exited_at":       exited,
        "entry_reason":    weighted_choice(rng, ENTRY_REASONS, ENTRY_REASON_W, n),
        "source_system":   rng.choice(CDP_SOURCES, size=n),
        "is_current":      is_current,
    })


def _loyalty_accounts(ctx, customers, n=200_000):
    """40% of customers enrolled in loyalty (500k → 200k)."""
    rng = ctx.rng
    if n > len(customers):
        n = len(customers)
    sub = customers.sample(n=n, random_state=ctx.seed + 7).reset_index(drop=True)
    enrolled_at = pd.to_datetime(
        rng.integers(int(pd.Timestamp("2021-01-01").timestamp()),
                     int(pd.Timestamp("2026-04-01").timestamp()), size=n),
        unit="s")
    earned = (rng.lognormal(7.0, 1.2, size=n)).astype(np.int64)
    redeemed = (earned * rng.uniform(0.10, 0.80, size=n)).astype(np.int64)
    balance = (earned - redeemed).clip(min=0)
    return pd.DataFrame({
        "loyalty_account_id":       [f"LOY{i:09d}" for i in range(1, n + 1)],
        "customer_id":              sub["customer_id"].to_numpy(),
        "program_code":             weighted_choice(rng, PROGRAMS, PROGRAM_W, n),
        "tier_code":                weighted_choice(rng, TIERS, TIER_W, n),
        "tier_progress_points":     rng.integers(0, 50_000, size=n),
        "tier_anchor_date":         pd.to_datetime(
                                        rng.integers(int(pd.Timestamp("2025-01-01").timestamp()),
                                                     int(pd.Timestamp("2026-01-01").timestamp()), size=n),
                                        unit="s").normalize(),
        "enrolled_at":              enrolled_at,
        "enrollment_channel":       weighted_choice(rng, ENROLL_CHANNELS, ENROLL_W, n),
        "lifetime_points_earned":   earned,
        "lifetime_points_redeemed": redeemed,
        "current_points_balance":   balance,
        "status":                   weighted_choice(rng, LOYALTY_STATUS, LOYALTY_STATUS_W, n),
        "opt_in_marketing":         rng.random(n) < 0.78,
        "last_engagement_at":       pd.to_datetime(
                                        rng.integers(int(pd.Timestamp("2025-09-01").timestamp()),
                                                     int(pd.Timestamp("2026-05-10").timestamp()), size=n),
                                        unit="s"),
    })


def _points_ledger(ctx, loyalty, n=500_000):
    rng = ctx.rng
    a_idx = rng.integers(0, len(loyalty), size=n)
    txn_type = weighted_choice(rng, LEDGER_TYPES, LEDGER_TYPE_W, n)
    raw_delta = rng.integers(50, 5000, size=n).astype(np.int64)
    points_delta = np.where(
        np.isin(txn_type, ["earn", "transfer_in", "bonus"]), raw_delta,
        np.where(np.isin(txn_type, ["redeem", "expire", "transfer_out"]), -raw_delta,
                 np.where(txn_type == "reversal", rng.choice([-1, 1], size=n) * raw_delta,
                          rng.choice([-1, 1], size=n) * (raw_delta // 4))),
    ).astype(np.int64)
    cash_minor = (np.abs(points_delta) * rng.uniform(0.5, 1.5, size=n)).astype(np.int64)
    txn_ts = pd.to_datetime(
        rng.integers(int(pd.Timestamp("2025-06-01").timestamp()),
                     int(pd.Timestamp("2026-05-10").timestamp()), size=n),
        unit="s")
    posted_ts = txn_ts + pd.to_timedelta(rng.integers(0, 86400, size=n), unit="s")
    expiry_ts = txn_ts + pd.to_timedelta(rng.integers(180, 730, size=n), unit="D")
    return pd.DataFrame({
        "ledger_id":             [f"LDG{i:012d}" for i in range(1, n + 1)],
        "loyalty_account_id":    loyalty["loyalty_account_id"].to_numpy()[a_idx],
        "txn_type":              txn_type,
        "source_event_id":       [f"REF{rng.integers(10**11, 10**12):012d}" for _ in range(n)],
        "order_id":              np.where(txn_type == "earn",
                                          [f"ORD{rng.integers(10**7, 10**8):08d}" for _ in range(n)],
                                          None),
        "points_delta":          points_delta,
        "cash_equivalent_minor": cash_minor,
        "campaign_code":         np.where(rng.random(n) < 0.40,
                                          [f"CAMP{rng.integers(10**3, 10**4):04d}" for _ in range(n)],
                                          None),
        "txn_ts":                txn_ts,
        "posted_ts":             posted_ts,
        "expiry_ts":             expiry_ts,
        "status":                weighted_choice(rng, ["posted", "pending", "reversed", "expired"],
                                                 [0.86, 0.06, 0.04, 0.04], n),
    })


def _rewards(ctx, n=200):
    rng = ctx.rng
    return pd.DataFrame({
        "reward_id":             [f"RWD{i:05d}" for i in range(1, n + 1)],
        "reward_name":           [f"Reward {i:05d}" for i in range(1, n + 1)],
        "reward_type":           weighted_choice(rng, REWARD_TYPES, REWARD_TYPE_W, n),
        "points_cost":           rng.integers(250, 25_000, size=n),
        "cash_equivalent_minor": (rng.integers(500, 25_000, size=n)).astype(np.int64),
        "stock_remaining":       np.where(rng.random(n) < 0.40, rng.integers(0, 5000, size=n), None),
        "vendor":                rng.choice(REWARD_VENDORS, size=n),
        "valid_from":            pd.to_datetime(
                                     rng.integers(int(pd.Timestamp("2024-01-01").timestamp()),
                                                  int(pd.Timestamp("2026-01-01").timestamp()), size=n),
                                     unit="s"),
        "valid_to":              pd.to_datetime(
                                     rng.integers(int(pd.Timestamp("2026-06-01").timestamp()),
                                                  int(pd.Timestamp("2027-12-01").timestamp()), size=n),
                                     unit="s"),
        "status":                weighted_choice(rng, ["active", "paused", "sold_out", "retired"],
                                                  [0.78, 0.07, 0.08, 0.07], n),
    })


def _redemptions(ctx, loyalty, rewards, n=100_000):
    rng = ctx.rng
    a_idx = rng.integers(0, len(loyalty), size=n)
    r_idx = rng.integers(0, len(rewards), size=n)
    sub_r = rewards.iloc[r_idx].reset_index(drop=True)
    requested_at = pd.to_datetime(
        rng.integers(int(pd.Timestamp("2025-06-01").timestamp()),
                     int(pd.Timestamp("2026-05-10").timestamp()), size=n),
        unit="s")
    fulfilled_offset = rng.integers(60, 7 * 86400, size=n)
    status = weighted_choice(rng, ["pending", "fulfilled", "cancelled", "reversed", "fraud_review"],
                             [0.05, 0.85, 0.04, 0.04, 0.02], n)
    fulfilled_at = np.where(status == "fulfilled",
                             requested_at + pd.to_timedelta(fulfilled_offset, unit="s"),
                             np.datetime64("NaT"))
    return pd.DataFrame({
        "redemption_id":         [f"RED{i:010d}" for i in range(1, n + 1)],
        "loyalty_account_id":    loyalty["loyalty_account_id"].to_numpy()[a_idx],
        "reward_id":             sub_r["reward_id"].to_numpy(),
        "points_spent":          sub_r["points_cost"].to_numpy(),
        "cash_equivalent_minor": sub_r["cash_equivalent_minor"].to_numpy(),
        "channel":               weighted_choice(rng, ["web", "app", "in_store", "call_center", "partner"],
                                                  [0.34, 0.30, 0.26, 0.06, 0.04], n),
        "order_id":              [f"ORD{rng.integers(10**7, 10**8):08d}" for _ in range(n)],
        "requested_at":          requested_at,
        "fulfilled_at":          fulfilled_at,
        "status":                status,
    })


def _preferences(ctx, customers, n=800_000):
    rng = ctx.rng
    c_idx = rng.integers(0, len(customers), size=n)
    channel = weighted_choice(rng, ["email", "sms", "push", "direct_mail", "in_app", "paid_media"],
                              [0.36, 0.20, 0.18, 0.08, 0.10, 0.08], n)
    return pd.DataFrame({
        "preference_id":     [f"PRF{i:012d}" for i in range(1, n + 1)],
        "customer_id":       customers["customer_id"].to_numpy()[c_idx],
        "channel":           channel,
        "topic":             rng.choice(PREF_TOPICS, size=n),
        "state":             weighted_choice(rng, PREF_STATES, PREF_STATE_W, n),
        "source_system":     rng.choice(CDP_SOURCES, size=n),
        "changed_at":        pd.to_datetime(
                                 rng.integers(int(pd.Timestamp("2023-01-01").timestamp()),
                                              int(pd.Timestamp("2026-05-10").timestamp()), size=n),
                                 unit="s"),
        "effective_until":   pd.to_datetime(
                                 rng.integers(int(pd.Timestamp("2026-05-10").timestamp()),
                                              int(pd.Timestamp("2028-01-01").timestamp()), size=n),
                                 unit="s"),
    })


def _consents(ctx, customers, n=900_000):
    rng = ctx.rng
    c_idx = rng.integers(0, len(customers), size=n)
    return pd.DataFrame({
        "consent_id":         [f"CNS{i:012d}" for i in range(1, n + 1)],
        "customer_id":        customers["customer_id"].to_numpy()[c_idx],
        "jurisdiction":       weighted_choice(rng, JURIS, JURIS_W, n),
        "consent_basis":      weighted_choice(rng, CONSENT_BASIS, CONSENT_BASIS_W, n),
        "consent_string":     [f"CPv1~{rng.integers(10**11, 10**12):012d}" for _ in range(n)],
        "purpose_codes":      rng.choice(['[1,2,3]', '[1,3,5]', '[1,2,4,6]', '[1,2,3,4,5,6]', '[1]'], size=n),
        "action":             weighted_choice(rng, CONSENT_ACTIONS, CONSENT_ACTION_W, n),
        "source_system":      rng.choice(CDP_SOURCES, size=n),
        "event_ts":           pd.to_datetime(
                                  rng.integers(int(pd.Timestamp("2023-01-01").timestamp()),
                                               int(pd.Timestamp("2026-05-10").timestamp()), size=n),
                                  unit="s"),
        "ip_token":           [f"IPT-{rng.integers(10**11, 10**12):012d}" for _ in range(n)],
        "user_agent_token":   [f"UAT-{rng.integers(10**11, 10**12):012d}" for _ in range(n)],
    })


def generate(seed=42):
    ctx = make_context(seed)
    print("  generating customers (500k)...")
    customers = _customers(ctx)
    print("  generating identity_links (2.5M)...")
    idlinks = _identity_links(ctx, customers)
    print("  generating events (1M)...")
    events = _events(ctx, customers)
    print("  generating segments (10)...")
    segments = _segments(ctx)
    print("  generating segment_memberships (5M)...")
    seg_mem = _segment_memberships(ctx, customers, segments)
    print("  generating loyalty_accounts (200k)...")
    loyalty = _loyalty_accounts(ctx, customers)
    print("  generating points_ledger (500k)...")
    ledger = _points_ledger(ctx, loyalty)
    print("  generating rewards (200)...")
    rewards = _rewards(ctx)
    print("  generating redemptions (100k)...")
    redemptions = _redemptions(ctx, loyalty, rewards)
    print("  generating preferences (800k)...")
    prefs = _preferences(ctx, customers)
    print("  generating consents (900k)...")
    consents = _consents(ctx, customers)
    tables = {
        "customer_master":     customers,
        "identity_link":       idlinks,
        "event":               events,
        "segment":             segments,
        "segment_membership":  seg_mem,
        "loyalty_account":     loyalty,
        "points_ledger":       ledger,
        "reward":              rewards,
        "redemption":          redemptions,
        "preference_center":   prefs,
        "consent_record":      consents,
    }
    for name, df in tables.items():
        write_table(SUBDOMAIN, name, df)
    return tables


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--seed", type=int, default=42)
    args = p.parse_args()
    tables = generate(args.seed)
    print()
    for name, df in tables.items():
        print(f"  {SUBDOMAIN}.{name}: {len(df):,} rows")


if __name__ == "__main__":
    main()
