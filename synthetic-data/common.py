"""
Shared helpers for synthetic data generators.

All generators import from this module so we get:
  * a single Faker / Mimesis / numpy seeding entry point
  * a uniform writer (CSV + parquet under output/<subdomain>/)
  * helpers for ID minting and weighted choice that respect the seed
"""
from __future__ import annotations

import random
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
from faker import Faker
from mimesis import Generic
from mimesis.locales import Locale

REPO_ROOT = Path(__file__).resolve().parent.parent
SYNTH_ROOT = Path(__file__).resolve().parent
OUTPUT_ROOT = SYNTH_ROOT / "output"


@dataclass
class GenContext:
    """Bundles the deterministic RNGs every generator needs."""

    seed: int
    rng: np.random.Generator
    faker: Faker
    mimesis: Generic
    py_random: random.Random


def make_context(seed: int) -> GenContext:
    """Create a GenContext with all PRNGs seeded from the same integer."""
    rng = np.random.default_rng(seed)
    faker = Faker(["en_US", "en_GB", "de_DE"])
    Faker.seed(seed)
    py_random = random.Random(seed)
    mimesis = Generic(locale=Locale.EN, seed=seed)
    return GenContext(
        seed=seed, rng=rng, faker=faker, mimesis=mimesis, py_random=py_random
    )


def output_dir_for(subdomain: str) -> Path:
    out = OUTPUT_ROOT / subdomain
    out.mkdir(parents=True, exist_ok=True)
    return out


def write_table(subdomain: str, name: str, df: pd.DataFrame) -> Path:
    """Write a DataFrame as both CSV and Parquet under output/<subdomain>/."""
    out = output_dir_for(subdomain)
    csv_path = out / f"{name}.csv"
    pq_path = out / f"{name}.parquet"
    df.to_csv(csv_path, index=False)
    df.to_parquet(pq_path, index=False)
    return pq_path


def weighted_choice(rng: np.random.Generator, choices: Sequence[str], weights: Sequence[float], size: int) -> np.ndarray:
    w = np.asarray(weights, dtype=float)
    w = w / w.sum()
    return rng.choice(choices, size=size, p=w)


def country_codes() -> list[str]:
    return [
        "US", "GB", "DE", "FR", "ES", "IT", "NL", "SE", "DK", "NO",
        "FI", "PL", "CA", "MX", "BR", "AR", "JP", "KR", "AU", "NZ",
        "SG", "IN", "ZA", "AE", "SA",
    ]


def currency_codes() -> list[str]:
    return ["USD", "EUR", "GBP", "JPY", "AUD", "CAD", "CHF", "INR", "SGD", "BRL"]


def daterange_minutes(rng: np.random.Generator, n: int, start: pd.Timestamp, end: pd.Timestamp) -> pd.DatetimeIndex:
    """Generate `n` timestamps uniformly between start and end with minute precision,
    with a soft business-hour weekday bias."""
    span_minutes = int((end - start).total_seconds() // 60)
    raw_offsets = rng.integers(0, span_minutes, size=n)
    ts = start + pd.to_timedelta(raw_offsets, unit="m")
    return pd.DatetimeIndex(ts).sort_values()


def lognormal_amounts(rng: np.random.Generator, n: int, mean: float = 4.5, sigma: float = 1.0) -> np.ndarray:
    """Realistic lognormal-shaped monetary amounts."""
    raw = rng.lognormal(mean=mean, sigma=sigma, size=n)
    return np.round(raw, 2)
