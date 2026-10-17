"""In-memory ground truth for the synthetic world. Renderers turn this into per-system source files."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Any

import numpy as np

from .spec import SEED


def d(s: str | date) -> date:
    return s if isinstance(s, date) else date.fromisoformat(s)


def days(a: date, b: date) -> int:
    return (b - a).days


@dataclass
class World:
    seed: int = SEED
    rng: np.random.Generator = field(default_factory=lambda: np.random.default_rng(SEED))
    orgs: dict[str, dict] = field(default_factory=dict)
    sites: dict[str, dict] = field(default_factory=dict)
    positions: dict[str, dict] = field(default_factory=dict)
    units: dict[str, dict] = field(default_factory=dict)
    installs: list[dict] = field(default_factory=list)
    failures: list[dict] = field(default_factory=list)
    notifications: list[dict] = field(default_factory=list)
    workorders: list[dict] = field(default_factory=list)
    signals: dict[str, dict] = field(default_factory=dict)
    spectra: list[dict] = field(default_factory=list)
    runs: list[dict] = field(default_factory=list)
    difa: list[dict] = field(default_factory=list)
    production: list[dict] = field(default_factory=list)
    stock: list[dict] = field(default_factory=list)
    windows: list[dict] = field(default_factory=list)
    rigs: list[dict] = field(default_factory=list)
    documents: list[dict] = field(default_factory=list)
    # maker side
    lots: dict[str, dict] = field(default_factory=dict)
    ecos: dict[str, dict] = field(default_factory=dict)
    builds: list[dict] = field(default_factory=list)
    genealogy: list[dict] = field(default_factory=list)
    tests: list[dict] = field(default_factory=list)
    shipments: list[dict] = field(default_factory=list)
    customers: dict[str, dict] = field(default_factory=dict)
    claims: list[dict] = field(default_factory=list)
    ncrs: list[dict] = field(default_factory=list)
    # time series, filled by signals.py
    daily: dict[str, dict[str, np.ndarray]] = field(default_factory=dict)
    raw: dict[str, tuple[np.ndarray, np.ndarray]] = field(default_factory=dict)
    answer: dict[str, Any] = field(default_factory=dict)
    _n: dict[str, int] = field(default_factory=dict)

    def nid(self, prefix: str) -> str:
        self._n[prefix] = self._n.get(prefix, 0) + 1
        return f"{prefix}{self._n[prefix]:05d}"

    # -- queries used by the generators and by tests (ground truth, not by the KG) --
    def installs_of(self, unit: str) -> list[dict]:
        return sorted((i for i in self.installs if i["unit"] == unit), key=lambda i: i["from"])

    def installs_at(self, pos: str) -> list[dict]:
        return sorted((i for i in self.installs if i["pos"] == pos), key=lambda i: i["from"])

    def unit_at(self, pos: str, on: date) -> str | None:
        for i in self.installs_at(pos):
            if i["from"] <= on and (i["to"] is None or on < i["to"]):
                return i["unit"]
        return None

    def position_of(self, unit: str, on: date) -> str | None:
        for i in self.installs_of(unit):
            if i["from"] <= on and (i["to"] is None or on < i["to"]):
                return i["pos"]
        return None


def add_days(x: date, n: int) -> date:
    return x + timedelta(days=int(n))
