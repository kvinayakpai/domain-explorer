"""
Synthetic Agentic Commerce data — AP2 / Visa Trusted Agent Protocol /
Mastercard Agent Pay / Stripe Agentic SDK / Anthropic MCP.

Entities (>=10):
  agent, principal, merchant, authorization_grant, agent_session, intent_event,
  tool_call, cart, agent_transaction, attribution_link, trust_score_event,
  dispute.

Realism:
  - Long-tail merchant GMV (Pareto sampling).
  - Bursty intent windows aligned with chat traffic peaks.
  - ~0.5% fraud / chargeback rate on agent transactions.
  - Lookback delays from intent → purchase that respect AP2 IntentMandate
    grant TTLs.
  - All large-range integer IDs use the int64-safe pattern from
    capital_markets/generate.py (rng.integers + zero-padded format string).
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from common import (
    daterange_minutes,
    make_context,
    weighted_choice,
    write_table,
)

SUBDOMAIN = "agentic_commerce"

OPERATORS = ["anthropic", "openai", "google", "amazon", "klarna", "merchant_internal"]
OPERATOR_W = [0.32, 0.28, 0.16, 0.12, 0.08, 0.04]
MODEL_FAMILIES_BY_OP = {
    "anthropic": ["claude-opus-4-6", "claude-sonnet-4-6", "claude-haiku-4-5"],
    "openai": ["gpt-4o", "gpt-4-turbo", "operator-1.0"],
    "google": ["gemini-2-ultra", "gemini-2-flash", "buy-for-me-1.0"],
    "amazon": ["nova-pro", "buy-for-me-amzn"],
    "klarna": ["klarna-agent-1"],
    "merchant_internal": ["custom-llm"],
}
AGENT_KINDS = ["shopping_assistant", "task_agent", "browser_agent", "chat_agent", "workflow_agent"]
AGENT_KIND_W = [0.46, 0.18, 0.18, 0.12, 0.06]
KYA_STATUS = ["verified", "self_asserted", "denied"]
KYA_STATUS_W = [0.78, 0.20, 0.02]
PSPS = ["stripe", "adyen", "braintree", "skyfire", "crossmint", "klarna"]
PSP_W = [0.42, 0.18, 0.10, 0.10, 0.10, 0.10]
RAILS = ["card", "ach", "sepa", "stable_usd", "wire"]
RAIL_W = [0.78, 0.06, 0.06, 0.07, 0.03]
SCHEMES = ["Visa", "Mastercard", "Amex", "Discover", "JCB", "n/a"]
SCHEME_W = [0.50, 0.32, 0.10, 0.04, 0.02, 0.02]
COUNTRIES = ["US", "GB", "DE", "FR", "JP", "CA", "AU", "IN", "BR", "SG", "NL", "ES", "IT", "MX"]
KYC_LEVELS = ["L0", "L1", "L2", "L3"]
KYC_W = [0.05, 0.55, 0.32, 0.08]
RAR_TYPES = ["agentic_purchase", "recurring_purchase", "refund"]
RAR_TYPE_W = [0.74, 0.18, 0.08]
GRANT_STATUS = ["active", "expired", "revoked", "exhausted"]
GRANT_STATUS_W = [0.62, 0.22, 0.06, 0.10]
INTENT_STATES = ["received", "searching", "cart_built", "awaiting_auth", "fulfilled", "abandoned", "expired"]
INTENT_STATE_W = [0.05, 0.05, 0.10, 0.05, 0.55, 0.15, 0.05]
TXN_STATUS = ["authorized", "captured", "declined", "reversed", "refunded", "disputed"]
TXN_STATUS_W = [0.04, 0.84, 0.05, 0.01, 0.05, 0.01]
STEPUP_METHODS = ["none", "webauthn", "spc", "push", "sms", "email_otp"]
STEPUP_W = [0.55, 0.20, 0.10, 0.08, 0.05, 0.02]
SERVERS = ["stripe-mcp", "shopify-mcp", "merchant-mcp", "search-mcp", "square-mcp", "paypal-mcp", "gtin-lookup-mcp"]
SERVER_W = [0.28, 0.22, 0.18, 0.12, 0.08, 0.07, 0.05]
TOOL_NAMES = [
    "search_products", "get_product", "get_price", "create_cart", "update_cart",
    "checkout_session.create", "payment_intent.create", "confirm_payment",
    "tax.calculate", "shipping.estimate", "refund.create", "subscription.create",
]
CATEGORY_HINTS = ["apparel", "footwear", "electronics", "groceries", "home", "books", "toys", "beauty", "auto_parts", "outdoors"]
DECLINE_REASONS = ["insufficient_funds", "do_not_honor", "expired_card", "fraud_suspected", "scope_violation", "stepup_required", "merchant_blocked"]
DISPUTE_REASONS = ["10.4", "11.3", "12.5", "13.1", "13.6", "13.7", "4855", "4831"]
DISPUTE_OUTCOMES = ["won", "lost", "withdrawn", "carried_back"]
DISPUTE_OUTCOME_W = [0.45, 0.30, 0.10, 0.15]


# ---------------------------------------------------------------------------
def _agents(ctx, n=10_000):
    rng = ctx.rng
    operator = weighted_choice(rng, OPERATORS, OPERATOR_W, n)
    model = np.array([rng.choice(MODEL_FAMILIES_BY_OP[op]) for op in operator])
    kya = weighted_choice(rng, KYA_STATUS, KYA_STATUS_W, n)
    base_score = rng.normal(72, 14, size=n).clip(0, 100)
    base_score = np.where(kya == "denied", base_score * 0.3, base_score)
    base_score = np.where(kya == "self_asserted", base_score * 0.85, base_score)
    return pd.DataFrame({
        "agent_id": [f"AGT{i:08d}" for i in range(1, n + 1)],
        "aaid": [f"AAID-{rng.integers(10**9, 10**10):010d}" for _ in range(n)],
        "operator_org": operator,
        "agent_kind": weighted_choice(rng, AGENT_KINDS, AGENT_KIND_W, n),
        "model_family": model,
        "kya_status": kya,
        "kya_trust_score": np.round(base_score, 2),
        "created_at": pd.to_datetime(
            rng.integers(int(pd.Timestamp("2025-06-01").timestamp()),
                         int(pd.Timestamp("2026-05-01").timestamp()), size=n),
            unit="s"),
        "status": weighted_choice(rng, ["active", "paused", "blocked", "retired"], [0.88, 0.05, 0.04, 0.03], n),
    })


def _principals(ctx, n=100_000):
    rng = ctx.rng
    return pd.DataFrame({
        "principal_id": [f"PRN{i:09d}" for i in range(1, n + 1)],
        "external_user_ref": [f"USR-{rng.integers(10**11, 10**12):012d}" for _ in range(n)],
        "country_iso2": rng.choice(COUNTRIES, size=n),
        "kyc_level": weighted_choice(rng, KYC_LEVELS, KYC_W, n),
        "created_at": pd.to_datetime(
            rng.integers(int(pd.Timestamp("2024-01-01").timestamp()),
                         int(pd.Timestamp("2026-05-01").timestamp()), size=n),
            unit="s"),
        "stepup_capable": rng.random(n) < 0.62,
        "status": weighted_choice(rng, ["active", "blocked", "deleted"], [0.97, 0.02, 0.01], n),
    })


def _merchants(ctx, n=10_000):
    rng = ctx.rng
    f = ctx.faker
    tier = weighted_choice(rng, ["tier1_native", "tier2_mcp", "tier3_legacy"], [0.10, 0.30, 0.60], n)
    has_mcp = (tier != "tier3_legacy")
    has_ap2 = (tier == "tier1_native")
    return pd.DataFrame({
        "merchant_id": [f"MER{i:07d}" for i in range(1, n + 1)],
        "legal_name": [f.company() for _ in range(n)],
        "domain": [f.domain_name() for _ in range(n)],
        "country_iso2": rng.choice(COUNTRIES, size=n),
        "mcc": [f"{rng.integers(1000, 9999):04d}" for _ in range(n)],
        "agent_aware_tier": tier,
        "mcp_endpoint": np.where(has_mcp,
                                 [f"https://mcp.{d}/v1" for d in [f.domain_name() for _ in range(n)]],
                                 None),
        "ap2_endpoint": np.where(has_ap2,
                                 [f"https://ap2.{d}/mandates" for d in [f.domain_name() for _ in range(n)]],
                                 None),
        "created_at": pd.to_datetime(
            rng.integers(int(pd.Timestamp("2024-01-01").timestamp()),
                         int(pd.Timestamp("2026-04-01").timestamp()), size=n),
            unit="s"),
    })


def _grants(ctx, principals, agents, n=200_000):
    rng = ctx.rng
    p_idx = rng.integers(0, len(principals), size=n)
    a_idx = rng.integers(0, len(agents), size=n)
    issued = pd.to_datetime(
        rng.integers(int(pd.Timestamp("2025-09-01").timestamp()),
                     int(pd.Timestamp("2026-05-08").timestamp()), size=n),
        unit="s")
    ttl_days = rng.integers(1, 365, size=n)
    expires = issued + pd.to_timedelta(ttl_days, unit="D")
    max_amt = (rng.lognormal(7.5, 1.0, size=n) * 100).astype(np.int64)  # minor units
    per_txn = (max_amt * rng.uniform(0.05, 0.5, size=n)).astype(np.int64).clip(min=500)
    stepup_threshold = (per_txn * rng.uniform(1.5, 4.0, size=n)).astype(np.int64)
    return pd.DataFrame({
        "grant_id": [f"GRT{i:09d}" for i in range(1, n + 1)],
        "principal_id": principals["principal_id"].to_numpy()[p_idx],
        "agent_id": agents["agent_id"].to_numpy()[a_idx],
        "rar_type": weighted_choice(rng, RAR_TYPES, RAR_TYPE_W, n),
        "max_amount_minor": max_amt,
        "max_amount_currency": rng.choice(["USD", "EUR", "GBP", "JPY"], p=[0.65, 0.18, 0.10, 0.07], size=n),
        "merchant_scope": rng.choice([
            '{"any":true}', '{"merchants":["MER0000001"]}', '{"domains":["*.shopify.com"]}',
            '{"category":"apparel"}', '{"category":"groceries"}'
        ], size=n),
        "category_scope": rng.choice([None, "apparel", "groceries", "any"], size=n),
        "per_txn_cap_minor": per_txn,
        "scope_expires_at": expires,
        "stepup_required_above_minor": stepup_threshold,
        "issued_at": issued,
        "revoked_at": pd.NaT,
        "status": weighted_choice(rng, GRANT_STATUS, GRANT_STATUS_W, n),
    })


def _sessions(ctx, agents, principals, grants, n=400_000):
    rng = ctx.rng
    g_idx = rng.integers(0, len(grants), size=n)
    g_subset = grants.iloc[g_idx].reset_index(drop=True)
    started = pd.to_datetime(
        rng.integers(int(pd.Timestamp("2025-12-01").timestamp()),
                     int(pd.Timestamp("2026-05-09").timestamp()), size=n),
        unit="s")
    duration_s = rng.gamma(2.5, 600, size=n).clip(15, 14_400).astype(int)
    ended = started + pd.to_timedelta(duration_s, unit="s")
    return pd.DataFrame({
        "session_id": [f"SES{i:010d}" for i in range(1, n + 1)],
        "agent_id": g_subset["agent_id"].to_numpy(),
        "principal_id": g_subset["principal_id"].to_numpy(),
        "grant_id": g_subset["grant_id"].to_numpy(),
        "started_at": started,
        "ended_at": ended,
        "client_signature": [f"jwt:{rng.integers(10**11, 10**12):012d}" for _ in range(n)],
        "principal_present": rng.random(n) < 0.42,
    })


def _intents(ctx, sessions, n=1_000_000):
    rng = ctx.rng
    s_idx = rng.integers(0, len(sessions), size=n)
    sub = sessions.iloc[s_idx].reset_index(drop=True)
    created = sub["started_at"].to_numpy() + pd.to_timedelta(rng.integers(0, 3600, size=n), unit="s")
    state = weighted_choice(rng, INTENT_STATES, INTENT_STATE_W, n)
    bmin = (rng.lognormal(4.0, 1.2, size=n) * 100).astype(np.int64)  # minor
    bmax = (bmin * rng.uniform(1.05, 4.0, size=n)).astype(np.int64)
    deadline_offset_d = rng.integers(0, 14, size=n)
    deadline = created + pd.to_timedelta(deadline_offset_d, unit="D")
    resolved_offset_s = rng.integers(60, 7 * 86400, size=n)
    resolved = np.where(np.isin(state, ["fulfilled", "abandoned", "expired"]),
                        created + pd.to_timedelta(resolved_offset_s, unit="s"),
                        np.datetime64("NaT"))
    return pd.DataFrame({
        "intent_id": [f"INT{i:010d}" for i in range(1, n + 1)],
        "session_id": sub["session_id"].to_numpy(),
        "principal_id": sub["principal_id"].to_numpy(),
        "agent_id": sub["agent_id"].to_numpy(),
        "intent_text_hash": [f"sha256:{rng.integers(10**15, 10**16):016d}" for _ in range(n)],
        "category_hint": rng.choice(CATEGORY_HINTS, size=n),
        "budget_min_minor": bmin,
        "budget_max_minor": bmax,
        "budget_currency": rng.choice(["USD", "EUR", "GBP", "JPY"], p=[0.7, 0.15, 0.10, 0.05], size=n),
        "deadline_ts": deadline,
        "state": state,
        "created_at": created,
        "resolved_at": resolved,
    })


def _tool_calls(ctx, sessions, intents, n=1_000_000):
    rng = ctx.rng
    s_idx = rng.integers(0, len(sessions), size=n)
    i_idx = rng.integers(0, len(intents), size=n)
    sub_sess = sessions.iloc[s_idx].reset_index(drop=True)
    sub_int = intents.iloc[i_idx].reset_index(drop=True)
    started = sub_sess["started_at"].to_numpy() + pd.to_timedelta(rng.integers(0, 3600, size=n), unit="s")
    return pd.DataFrame({
        "tool_call_id": [f"TC{i:011d}" for i in range(1, n + 1)],
        "session_id": sub_sess["session_id"].to_numpy(),
        "intent_id": sub_int["intent_id"].to_numpy(),
        "server_name": weighted_choice(rng, SERVERS, SERVER_W, n),
        "tool_name": rng.choice(TOOL_NAMES, size=n),
        "started_at": started,
        "latency_ms": rng.gamma(2.0, 130, size=n).clip(15, 30_000).astype(int),
        "cost_usd": np.round(rng.uniform(0.0001, 0.05, size=n), 6),
        "status": weighted_choice(rng, ["ok", "error", "timeout", "rate_limited", "denied"],
                                   [0.88, 0.06, 0.03, 0.02, 0.01], n),
        "input_size_bytes": rng.integers(50, 16_000, size=n),
        "output_size_bytes": rng.integers(50, 64_000, size=n),
    })


def _carts(ctx, intents, merchants, n=520_000):
    rng = ctx.rng
    fulfilled = intents[intents["state"].isin(["fulfilled", "awaiting_auth", "cart_built"])].reset_index(drop=True)
    if len(fulfilled) < n:
        n = len(fulfilled)
    sample = fulfilled.sample(n=n, random_state=ctx.seed).reset_index(drop=True)
    m_idx = rng.integers(0, len(merchants), size=n)
    subtotal = (rng.lognormal(4.5, 1.0, size=n) * 100).astype(np.int64)
    tax = (subtotal * rng.uniform(0.0, 0.20, size=n)).astype(np.int64)
    ship = rng.choice([0, 499, 799, 1299, 2499], size=n).astype(np.int64)
    total = subtotal + tax + ship
    built = sample["created_at"].to_numpy() + pd.to_timedelta(rng.integers(30, 7200, size=n), unit="s")
    confirmed = rng.random(n) < 0.78
    return pd.DataFrame({
        "cart_id": [f"CART{i:010d}" for i in range(1, n + 1)],
        "intent_id": sample["intent_id"].to_numpy(),
        "merchant_id": merchants["merchant_id"].to_numpy()[m_idx],
        "subtotal_minor": subtotal,
        "tax_minor": tax,
        "shipping_minor": ship,
        "total_minor": total,
        "currency": sample["budget_currency"].to_numpy(),
        "line_count": rng.integers(1, 12, size=n).astype("int16"),
        "signed_payload_hash": [f"sha256:{rng.integers(10**15, 10**16):016d}" for _ in range(n)],
        "signature_alg": rng.choice(["ES256", "RS256"], p=[0.78, 0.22], size=n),
        "built_at": built,
        "confirmed_by_principal": confirmed,
        "confirmation_ts": np.where(confirmed, built + pd.to_timedelta(rng.integers(2, 600, size=n), unit="s"), np.datetime64("NaT")),
    })


def _transactions(ctx, carts, grants, agents, principals, merchants, n=500_000):
    rng = ctx.rng
    if len(carts) < n:
        n = len(carts)
    sub_carts = carts.sample(n=n, random_state=ctx.seed + 1).reset_index(drop=True)
    g_idx = rng.integers(0, len(grants), size=n)
    sub_grants = grants.iloc[g_idx].reset_index(drop=True)
    psp = weighted_choice(rng, PSPS, PSP_W, n)
    rail = np.where(np.isin(psp, ["skyfire", "crossmint"]),
                    rng.choice(["stable_usd", "card"], p=[0.75, 0.25], size=n),
                    weighted_choice(rng, RAILS, RAIL_W, n))
    scheme = np.where(rail == "card",
                      weighted_choice(rng, SCHEMES, SCHEME_W, n),
                      "n/a")
    agent_indicator = rng.choice(["AGI", "AAI", "none"], p=[0.46, 0.36, 0.18], size=n)
    amount = sub_carts["total_minor"].to_numpy()
    status = weighted_choice(rng, TXN_STATUS, TXN_STATUS_W, n)
    stepup = weighted_choice(rng, STEPUP_METHODS, STEPUP_W, n)
    auth_at = sub_carts["built_at"].to_numpy() + pd.to_timedelta(rng.integers(1, 600, size=n), unit="s")
    captured = pd.Series(auth_at).where(np.isin(status, ["captured", "refunded", "disputed"]), pd.NaT).to_numpy()
    captured = np.where(np.isin(status, ["captured", "refunded", "disputed"]),
                        auth_at + pd.to_timedelta(rng.integers(0, 86400, size=n), unit="s"),
                        np.datetime64("NaT"))
    return pd.DataFrame({
        "agent_txn_id": [f"ATX{i:010d}" for i in range(1, n + 1)],
        "cart_id": sub_carts["cart_id"].to_numpy(),
        "grant_id": sub_grants["grant_id"].to_numpy(),
        "agent_id": sub_grants["agent_id"].to_numpy(),
        "principal_id": sub_grants["principal_id"].to_numpy(),
        "merchant_id": sub_carts["merchant_id"].to_numpy(),
        "psp": psp,
        "rail": rail,
        "scheme": scheme,
        "agent_indicator": agent_indicator,
        "amount_minor": amount,
        "currency": sub_carts["currency"].to_numpy(),
        "stepup_method": stepup,
        "status": status,
        "authorized_at": auth_at,
        "captured_at": captured,
        "decline_reason": np.where(status == "declined", rng.choice(DECLINE_REASONS, size=n), None),
        "latency_ms": rng.gamma(2.5, 90, size=n).clip(40, 12_000).astype(int),
    })


def _attribution_links(ctx, intents, transactions):
    rng = ctx.rng
    txn_intents = transactions.merge(
        intents[["intent_id", "session_id", "created_at"]],
        left_on="cart_id", right_on="intent_id", how="left"
    )
    n = len(transactions)
    return pd.DataFrame({
        "attribution_id": [f"ATT{i:010d}" for i in range(1, n + 1)],
        "intent_id": rng.choice(intents["intent_id"].to_numpy(), size=n),
        "agent_txn_id": transactions["agent_txn_id"].to_numpy(),
        "model": rng.choice(["first_touch", "last_touch", "linear", "time_decay", "ml_uplift"],
                            p=[0.10, 0.30, 0.20, 0.30, 0.10], size=n),
        "weight": np.round(rng.uniform(0.0, 1.0, size=n), 4),
        "lookback_seconds": rng.integers(60, 7 * 86400, size=n),
        "created_at": transactions["authorized_at"].to_numpy(),
    })


def _trust_score_events(ctx, agents, n=120_000):
    rng = ctx.rng
    a_idx = rng.integers(0, len(agents), size=n)
    return pd.DataFrame({
        "trust_event_id": [f"TSE{i:010d}" for i in range(1, n + 1)],
        "agent_id": agents["agent_id"].to_numpy()[a_idx],
        "source": rng.choice(["skyfire", "visa_kya", "mastercard_aai", "merchant_local"],
                             p=[0.35, 0.30, 0.25, 0.10], size=n),
        "score": np.round(rng.normal(70, 15, size=n).clip(0, 100), 2),
        "signal_summary": rng.choice([
            "stable cadence", "reduced velocity", "high-value txn drift",
            "geo-spread anomaly", "new merchant exploration", "post-refund cooloff"
        ], size=n),
        "observed_at": pd.to_datetime(
            rng.integers(int(pd.Timestamp("2026-01-01").timestamp()),
                         int(pd.Timestamp("2026-05-09").timestamp()), size=n),
            unit="s"),
    })


def _disputes(ctx, transactions, n=50_000):
    rng = ctx.rng
    eligible = transactions[transactions["status"].isin(["captured", "disputed", "refunded"])].reset_index(drop=True)
    if len(eligible) < n:
        n = len(eligible)
    sub = eligible.sample(n=n, random_state=ctx.seed + 2).reset_index(drop=True)
    opened = sub["captured_at"].to_numpy() + pd.to_timedelta(rng.integers(86400, 60 * 86400, size=n), unit="s")
    resolved = opened + pd.to_timedelta(rng.integers(86400, 90 * 86400, size=n), unit="s")
    return pd.DataFrame({
        "dispute_id": [f"DSP{i:010d}" for i in range(1, n + 1)],
        "agent_txn_id": sub["agent_txn_id"].to_numpy(),
        "reason_code": rng.choice(DISPUTE_REASONS, size=n),
        "opened_at": opened,
        "resolved_at": resolved,
        "amount_minor": sub["amount_minor"].to_numpy(),
        "currency": sub["currency"].to_numpy(),
        "outcome": weighted_choice(rng, DISPUTE_OUTCOMES, DISPUTE_OUTCOME_W, n),
        "carryback_to_operator": rng.random(n) < 0.18,
    })


def generate(seed=42):
    ctx = make_context(seed)
    print("  generating agents...")
    agents = _agents(ctx)
    print("  generating principals...")
    principals = _principals(ctx)
    print("  generating merchants...")
    merchants = _merchants(ctx)
    print("  generating grants...")
    grants = _grants(ctx, principals, agents)
    print("  generating sessions...")
    sessions = _sessions(ctx, agents, principals, grants)
    print("  generating intents (1M+ rows)...")
    intents = _intents(ctx, sessions)
    print("  generating tool calls (1M+ rows)...")
    tool_calls = _tool_calls(ctx, sessions, intents)
    print("  generating carts...")
    carts = _carts(ctx, intents, merchants)
    print("  generating transactions...")
    transactions = _transactions(ctx, carts, grants, agents, principals, merchants)
    print("  generating attribution_links...")
    attribution = _attribution_links(ctx, intents, transactions)
    print("  generating trust_score_events...")
    trust = _trust_score_events(ctx, agents)
    print("  generating disputes...")
    disputes = _disputes(ctx, transactions)
    tables = {
        "agent": agents,
        "principal": principals,
        "merchant": merchants,
        "authorization_grant": grants,
        "agent_session": sessions,
        "intent_event": intents,
        "tool_call": tool_calls,
        "cart": carts,
        "agent_transaction": transactions,
        "attribution_link": attribution,
        "trust_score_event": trust,
        "dispute": disputes,
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
