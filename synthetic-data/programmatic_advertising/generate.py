"""
Synthetic Programmatic Advertising data — IAB OpenRTB 2.6 / AdCOM 1.0 / VAST 4.2.

Entities (>=10): bid_request, imp, bid_response, bid, auction_event,
impression_event, video_event, click_event, conversion_event, campaign,
creative, advertiser.

Realism:
  - IAB content category taxonomy (IAB-1 through IAB-26).
  - Real-looking W3C user-agent strings spanning Chrome / Safari / Firefox / Edge.
  - Bid response latency lognormal with p95 ~ 80ms.
  - Win rate, viewability, IVT rate align with industry medians.
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

SUBDOMAIN = "programmatic_advertising"

IAB_CATEGORIES = [
    "IAB1-1", "IAB1-2", "IAB2-1", "IAB3-1", "IAB4-2", "IAB5-1", "IAB6-1",
    "IAB7-3", "IAB7-32", "IAB8-1", "IAB9-30", "IAB10-1", "IAB11-1",
    "IAB12-1", "IAB13-1", "IAB14-3", "IAB15-1", "IAB16-1", "IAB17-1",
    "IAB18-1", "IAB19-3", "IAB20-1", "IAB21-1", "IAB22-1", "IAB23-1",
    "IAB24", "IAB25-3", "IAB26-1",
]

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_5_0) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Linux; Android 14; SM-S918B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36 Edg/124.0.0.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (iPad; CPU OS 17_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) CriOS/124.0.0.0 Mobile/15E148 Safari/604.1",
]

DEAL_IDS = [None] * 18 + [f"DEAL-{i:05d}" for i in range(1, 200)]


def _advertisers(ctx, n=2_500):
    rng = ctx.rng
    f = ctx.faker
    return pd.DataFrame({
        "advertiser_id": [f"ADV-{i:05d}" for i in range(1, n + 1)],
        "name": [f.company() for _ in range(n)],
        "iab_categories": [",".join(rng.choice(IAB_CATEGORIES, size=2, replace=False)) for _ in range(n)],
        "country": rng.choice(["US", "GB", "DE", "FR", "JP", "AU", "CA", "BR", "IN"], size=n),
        "tier": weighted_choice(rng, ["enterprise", "mid-market", "smb", "self-serve"], [0.10, 0.20, 0.40, 0.30], n),
    })


def _campaigns(ctx, advertisers, n=10_000):
    rng = ctx.rng
    start = pd.to_datetime(rng.integers(int(pd.Timestamp("2024-06-01").timestamp()), int(pd.Timestamp("2026-04-30").timestamp()), size=n), unit="s")
    return pd.DataFrame({
        "campaign_id": [f"CAM-{i:07d}" for i in range(1, n + 1)],
        "advertiser_id": rng.choice(advertisers["advertiser_id"].to_numpy(), size=n),
        "name": [f"Campaign Q{rng.integers(1, 5)} {rng.integers(2024, 2026)}" for _ in range(n)],
        "objective": weighted_choice(rng, ["awareness", "consideration", "conversion", "retargeting", "video-view"], [0.25, 0.25, 0.30, 0.10, 0.10], n),
        "budget_total_usd": np.round(rng.lognormal(mean=10, sigma=1.5, size=n), 2),
        "budget_daily_usd": np.round(rng.lognormal(mean=6.5, sigma=1.2, size=n), 2),
        "start_date": start.date,
        "end_date": (start + pd.to_timedelta(rng.integers(7, 90, size=n), unit="D")).date,
        "bid_strategy": weighted_choice(rng, ["fixed-cpm", "tcpm", "vCPM", "tCPA", "tROAS"], [0.30, 0.30, 0.15, 0.15, 0.10], n),
        "status": weighted_choice(rng, ["active", "paused", "ended", "draft"], [0.50, 0.20, 0.25, 0.05], n),
    })


def _creatives(ctx, advertisers, campaigns, n=20_000):
    rng = ctx.rng
    return pd.DataFrame({
        "creative_id": [f"CRT-{i:08d}" for i in range(1, n + 1)],
        "advertiser_id": rng.choice(advertisers["advertiser_id"].to_numpy(), size=n),
        "campaign_id": rng.choice(campaigns["campaign_id"].to_numpy(), size=n),
        "format": weighted_choice(rng, ["banner", "video", "native", "rich-media", "audio"], [0.45, 0.30, 0.15, 0.07, 0.03], n),
        "width": rng.choice([300, 728, 300, 320, 970], size=n),
        "height": rng.choice([250, 90, 600, 50, 250], size=n),
        "duration_sec": rng.choice([6, 15, 30, 60], size=n),
        "iab_categories": [",".join(rng.choice(IAB_CATEGORIES, size=2, replace=False)) for _ in range(n)],
        "vast_version": rng.choice(["3.0", "4.1", "4.2"], size=n, p=[0.20, 0.30, 0.50]),
        "approval_status": weighted_choice(rng, ["approved", "pending", "rejected"], [0.85, 0.10, 0.05], n),
    })


def _bid_requests(ctx, n=200_000):
    """Primary entity — OpenRTB BidRequest."""
    rng = ctx.rng
    received_at = daterange_minutes(rng, n, pd.Timestamp("2026-04-15"), pd.Timestamp("2026-04-30"))
    return pd.DataFrame({
        "request_id": [f"REQ-{i:011d}" for i in range(1, n + 1)],
        "received_at": received_at,
        "tmax_ms": rng.choice([100, 120, 150, 200, 300], size=n, p=[0.20, 0.30, 0.30, 0.15, 0.05]),
        "publisher_id": [f"PUB-{rng.integers(1, 5_000):05d}" for _ in range(n)],
        "site_id": [f"SITE-{rng.integers(1, 20_000):07d}" for _ in range(n)],
        "site_domain": rng.choice(["news.example.com", "sports.example.com", "video.example.com", "weather.example.com", "tech.example.com", "shopping.example.com"], size=n),
        "iab_content_category": rng.choice(IAB_CATEGORIES, size=n),
        "device_type": weighted_choice(rng, ["mobile", "desktop", "tablet", "ctv", "audio"], [0.55, 0.32, 0.07, 0.04, 0.02], n),
        "os": weighted_choice(rng, ["iOS", "Android", "Windows", "macOS", "Linux", "ChromeOS"], [0.30, 0.30, 0.25, 0.10, 0.03, 0.02], n),
        "user_agent": rng.choice(USER_AGENTS, size=n),
        "ip_class_c": [f"{rng.integers(1, 224)}.{rng.integers(0, 255)}.{rng.integers(0, 255)}.0" for _ in range(n)],
        "country": rng.choice(["US", "GB", "DE", "FR", "JP", "BR", "IN", "AU", "CA"], size=n, p=[0.40, 0.10, 0.10, 0.07, 0.07, 0.07, 0.06, 0.07, 0.06]),
        "user_id_hash": [f"u_{rng.integers(10**11, 10**12):012d}" for _ in range(n)],
        "consent_string": [f"C{rng.integers(10**8, 10**9)}" for _ in range(n)],
        "auction_type": weighted_choice(rng, [1, 2], [0.85, 0.15], n),  # 1=first price, 2=second
    })


def _imps(ctx, bid_requests, n_target=300_000):
    rng = ctx.rng
    n = max(n_target, len(bid_requests))
    src = bid_requests.sample(n=n, replace=(n > len(bid_requests)), random_state=ctx.seed).reset_index(drop=True)
    return pd.DataFrame({
        "imp_id": [f"IMP-{i:011d}" for i in range(1, n + 1)],
        "request_id": src["request_id"].to_numpy(),
        "imp_position": np.tile(np.arange(1, 4), (n // 3) + 1)[:n],
        "ad_format": weighted_choice(rng, ["banner", "video", "native", "audio"], [0.55, 0.30, 0.10, 0.05], n),
        "width": rng.choice([300, 728, 300, 320, 970, 1280, 1920], size=n),
        "height": rng.choice([250, 90, 600, 50, 250, 720, 1080], size=n),
        "bidfloor_usd": np.round(rng.uniform(0.10, 5.0, size=n), 4),
        "secure_required": rng.random(n) < 0.95,
        "video_min_duration": rng.choice([0, 5, 6, 15], size=n),
        "video_max_duration": rng.choice([15, 30, 60, 120], size=n),
        "instl": rng.random(n) < 0.10,
    })


def _bid_responses(ctx, bid_requests, n_target=200_000):
    rng = ctx.rng
    n = min(n_target, len(bid_requests))
    src = bid_requests.sample(n=n, random_state=ctx.seed).reset_index(drop=True)
    received = pd.to_datetime(src["received_at"].to_numpy())
    latency_ms = rng.lognormal(mean=3.5, sigma=0.5, size=n).clip(5, 800)
    return pd.DataFrame({
        "response_id": [f"RES-{i:011d}" for i in range(1, n + 1)],
        "request_id": src["request_id"].to_numpy(),
        "dsp_id": [f"DSP-{rng.integers(1, 200):03d}" for _ in range(n)],
        "response_received_at": received + pd.to_timedelta(latency_ms.astype(int), unit="ms"),
        "response_latency_ms": np.round(latency_ms, 2),
        "no_bid_reason": np.where(rng.random(n) < 0.35, rng.choice(["budget_exhausted", "no_creatives", "filter_match", "below_floor", "timeout"], size=n), None),
        "bid_count": rng.integers(0, 5, size=n),
        "currency": "USD",
    })


def _bids(ctx, bid_responses, creatives, advertisers, n_target=300_000):
    rng = ctx.rng
    actual_responses = bid_responses[bid_responses["bid_count"] > 0]
    n = min(n_target, len(actual_responses) * 2)
    src = actual_responses.sample(n=n, replace=(n > len(actual_responses)), random_state=ctx.seed).reset_index(drop=True)
    return pd.DataFrame({
        "bid_id": [f"BID-{i:011d}" for i in range(1, n + 1)],
        "response_id": src["response_id"].to_numpy(),
        "request_id": src["request_id"].to_numpy(),
        "imp_id": [f"IMP-{rng.integers(1, 300_000):011d}" for _ in range(n)],
        "advertiser_id": rng.choice(advertisers["advertiser_id"].to_numpy(), size=n),
        "creative_id": rng.choice(creatives["creative_id"].to_numpy(), size=n),
        "bid_price_cpm": np.round(rng.lognormal(mean=0.7, sigma=0.6, size=n), 4),
        "currency": "USD",
        "dealid": rng.choice(DEAL_IDS, size=n),
        "iab_categories": [",".join(rng.choice(IAB_CATEGORIES, size=2, replace=False)) for _ in range(n)],
        "status": weighted_choice(rng, ["won", "lost", "no-decision", "rejected"], [0.18, 0.72, 0.07, 0.03], n),
    })


def _auction_events(ctx, bids, n_target=120_000):
    rng = ctx.rng
    won = bids[bids["status"] == "won"]
    n = min(n_target, len(won))
    src = won.sample(n=n, random_state=ctx.seed).reset_index(drop=True)
    return pd.DataFrame({
        "auction_event_id": [f"AUC-{i:010d}" for i in range(1, n + 1)],
        "request_id": src["request_id"].to_numpy(),
        "winning_bid_id": src["bid_id"].to_numpy(),
        "clearing_price": np.round(src["bid_price_cpm"].to_numpy() * rng.uniform(0.6, 1.0, size=n) / 1000.0, 6),
        "auction_type": rng.choice([1, 2], size=n, p=[0.85, 0.15]),
        "decided_at": pd.to_datetime(rng.integers(int(pd.Timestamp("2026-04-15").timestamp()), int(pd.Timestamp("2026-04-30").timestamp()), size=n), unit="s"),
        "ssp_id": [f"SSP-{rng.integers(1, 50):03d}" for _ in range(n)],
    })


def _impression_events(ctx, auction_events, n_target=110_000):
    rng = ctx.rng
    n = min(n_target, len(auction_events))
    src = auction_events.sample(n=n, random_state=ctx.seed).reset_index(drop=True)
    served = rng.random(n) < 0.94
    measurable = served & (rng.random(n) < 0.92)
    viewable = measurable & (rng.random(n) < 0.71)  # ~71% viewability
    ivt = served & (rng.random(n) < 0.04)
    decided = pd.to_datetime(src["decided_at"].to_numpy())
    return pd.DataFrame({
        "impression_event_id": [f"IEV-{i:011d}" for i in range(1, n + 1)],
        "request_id": src["request_id"].to_numpy(),
        "bid_id": src["winning_bid_id"].to_numpy(),
        "served": served,
        "served_at": decided + pd.to_timedelta(rng.integers(20, 1000, size=n), unit="ms"),
        "measurable": measurable,
        "viewable": viewable,
        "viewable_pixels_pct": np.where(measurable, np.round(rng.uniform(40, 100, size=n), 2), None),
        "viewable_seconds": np.where(measurable, np.round(rng.uniform(0.1, 8.0, size=n), 2), None),
        "ivt_flag": ivt,
        "ivt_classification": np.where(ivt, rng.choice(["GIVT", "SIVT"], size=n, p=[0.6, 0.4]), None),
        "render_ms": rng.integers(50, 1500, size=n),
    })


def _video_events(ctx, impression_events, n_target=80_000):
    rng = ctx.rng
    served = impression_events[impression_events["served"]]
    n_per = 4
    base_n = min(n_target // n_per, len(served))
    src = served.sample(n=base_n, random_state=ctx.seed).reset_index(drop=True)
    rows = []
    for i in range(len(src)):
        ie_id = src.loc[i, "impression_event_id"]
        served_at = pd.Timestamp(src.loc[i, "served_at"])
        rows.append((ie_id, "start", served_at))
        if rng.random() < 0.85:
            rows.append((ie_id, "firstQuartile", served_at + pd.Timedelta(seconds=int(rng.integers(2, 5)))))
        if rng.random() < 0.70:
            rows.append((ie_id, "midpoint", served_at + pd.Timedelta(seconds=int(rng.integers(5, 12)))))
        if rng.random() < 0.55:
            rows.append((ie_id, "thirdQuartile", served_at + pd.Timedelta(seconds=int(rng.integers(10, 20)))))
        if rng.random() < 0.45:
            rows.append((ie_id, "complete", served_at + pd.Timedelta(seconds=int(rng.integers(15, 30)))))
    df = pd.DataFrame(rows, columns=["impression_event_id", "event_type", "event_ts"])
    df.insert(0, "video_event_id", [f"VID-{i:010d}" for i in range(1, len(df) + 1)])
    return df


def _click_events(ctx, impression_events, n=12_000):
    rng = ctx.rng
    served = impression_events[impression_events["served"]]
    n = min(n, len(served))
    src = served.sample(n=n, random_state=ctx.seed).reset_index(drop=True)
    return pd.DataFrame({
        "click_event_id": [f"CLK-{i:010d}" for i in range(1, n + 1)],
        "impression_event_id": src["impression_event_id"].to_numpy(),
        "clicked_at": pd.to_datetime(src["served_at"].to_numpy()) + pd.to_timedelta(rng.integers(500, 30_000, size=n), unit="ms"),
        "click_x": rng.integers(0, 1000, size=n),
        "click_y": rng.integers(0, 800, size=n),
        "click_url": [f"https://landing.example.com/page-{rng.integers(1, 1_000)}" for _ in range(n)],
    })


def _conversion_events(ctx, click_events, n=4_000):
    rng = ctx.rng
    n = min(n, len(click_events))
    src = click_events.sample(n=n, random_state=ctx.seed).reset_index(drop=True)
    return pd.DataFrame({
        "conversion_event_id": [f"CON-{i:09d}" for i in range(1, n + 1)],
        "click_event_id": src["click_event_id"].to_numpy(),
        "converted_at": pd.to_datetime(src["clicked_at"].to_numpy()) + pd.to_timedelta(rng.integers(60, 30 * 86400, size=n), unit="s"),
        "conversion_type": weighted_choice(rng, ["purchase", "signup", "lead", "install", "view-through"], [0.40, 0.20, 0.15, 0.20, 0.05], n),
        "value_usd": np.round(rng.lognormal(mean=3.5, sigma=1.2, size=n), 2),
        "attribution_model": rng.choice(["last-click", "linear", "data-driven", "first-click"], size=n, p=[0.55, 0.20, 0.15, 0.10]),
    })


def generate(seed=42):
    ctx = make_context(seed)
    advertisers = _advertisers(ctx)
    campaigns = _campaigns(ctx, advertisers)
    creatives = _creatives(ctx, advertisers, campaigns)
    requests = _bid_requests(ctx)
    imps = _imps(ctx, requests)
    responses = _bid_responses(ctx, requests)
    bids = _bids(ctx, responses, creatives, advertisers)
    auctions = _auction_events(ctx, bids)
    impressions = _impression_events(ctx, auctions)
    videos = _video_events(ctx, impressions)
    clicks = _click_events(ctx, impressions)
    conversions = _conversion_events(ctx, clicks)
    tables = {
        "advertiser": advertisers,
        "campaign": campaigns,
        "creative": creatives,
        "bid_request": requests,
        "imp": imps,
        "bid_response": responses,
        "bid": bids,
        "auction_event": auctions,
        "impression_event": impressions,
        "video_event": videos,
        "click_event": clicks,
        "conversion_event": conversions,
    }
    for name, df in tables.items():
        write_table(SUBDOMAIN, name, df)
    return tables


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--seed", type=int, default=42)
    args = p.parse_args()
    tables = generate(args.seed)
    for name, df in tables.items():
        print(f"  {SUBDOMAIN}.{name}: {len(df):,} rows")


if __name__ == "__main__":
    main()
