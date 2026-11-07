"""Shared access to the Factory to Field simulated world for the oil and gas generators.

The refinery and upstream generators do not invent rows with Faker. They export tables from
the Factory to Field world (``factory_to_field/world``): the seeded simulation the knowledge
graph, the agents and the gold cases run on. The explorer's oil and gas pages and the demo
therefore describe the same three refineries, the same ESP wells and the same pump maker.

All data is synthetic. Names, serials and numbers are invented.
"""
from __future__ import annotations

import sys
from datetime import date, timedelta
from functools import lru_cache
from pathlib import Path
from typing import Any

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


@lru_cache(maxsize=2)
def load_world(seed: int = 42) -> Any:
    """Build the Factory to Field world once per seed (about 7 seconds)."""
    from factory_to_field.world.build import make_world

    return make_world(seed)


def history_days() -> list[date]:
    """Every day the historians hold, oldest first."""
    from factory_to_field.world.signals import N
    from factory_to_field.world.spec import HIST_START

    return [HIST_START + timedelta(days=i) for i in range(N)]


def as_of() -> date:
    from factory_to_field.world.spec import TODAY

    return TODAY


def strip(prefixed: str | None) -> str | None:
    """'unit:OEM-24-0412' -> 'OEM-24-0412'; position and site ids keep their own prefixes."""
    if prefixed is None:
        return None
    return prefixed.split(":", 1)[1] if prefixed.startswith(("unit:", "org:", "cust:")) else prefixed


def daily_frame(w: Any, signal_ids: list[str], days: list[date]) -> pd.DataFrame:
    """Long table of daily aggregates (mean, min, max, sample count) for the given signals."""
    frames = []
    for sid in signal_ids:
        agg = w.daily.get(sid)
        if agg is None:
            continue
        frames.append(pd.DataFrame({
            "signal_id": sid,
            "day": days,
            "mean_value": agg["mean"].round(4),
            "min_value": agg["min"].round(4),
            "max_value": agg["max"].round(4),
            "sample_count": agg["n"].astype(int),
        }))
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame(
        columns=["signal_id", "day", "mean_value", "min_value", "max_value", "sample_count"])
