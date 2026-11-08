"""Playbook agent vs the naive current-state baseline on the generated gold cases (as-of, failures by month, lot exposure).

usage: python -m factory_to_field.eval.baseline [--seeds 1 2 3 4]
Prints pass rate per question family. The baseline is a strawman I wrote (agents/baseline.py); the point is the size of the gap
on cases built from each world's own history, not that the baseline is a serious competitor.
"""
from __future__ import annotations

import argparse
import json
import tempfile
from collections import defaultdict
from pathlib import Path

from ..agents import gold
from ..agents.agent import Agent
from ..agents.baseline import NaiveAgent
from ..agents.sources import make_source
from ..kg.build import build_kg
from ..kg.store import KG
from ..world.build import build

FAMILIES = {"GEN-ASOF": "unit on a past date", "GEN-FAIL": "failures at a position in a month", "GEN-LOT-": "lot exposure of the string now running"}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, nargs="*", default=[1, 2, 3, 4])
    ap.add_argument("--out", type=Path, default=Path(__file__).resolve().parents[1] / "build" / "eval" / "baseline.json")
    a = ap.parse_args()
    tally: dict = defaultdict(lambda: {"real": [0, 0], "naive": [0, 0]})
    for seed in a.seeds:
        with tempfile.TemporaryDirectory() as td:
            wd = Path(td) / "world"
            build(wd, seed)
            build_kg(wd, Path(td) / "kg", skip_shacl=True)
            kg = KG(Path(td) / "kg" / "store", read_only=True)
            for name, cls in (("real", Agent), ("naive", NaiveAgent)):
                res = gold.score(agent=cls(kg=kg, world=wd, src=make_source(wd)), world=wd, kg=kg)
                for c in res["cases"]:
                    fam = next((f for f in FAMILIES if c["case"].startswith(f)), None)
                    if fam:
                        tally[fam][name][1] += 1
                        tally[fam][name][0] += bool(c["ok"])
        print(f"seed {seed} done", flush=True)
    rows = {FAMILIES[f]: {k: {"passed": v[0], "of": v[1], "rate": round(v[0] / v[1], 3) if v[1] else None} for k, v in t.items()} for f, t in tally.items()}
    for fam, r in rows.items():
        print(f"{fam:46} playbook agent {r['real']['passed']}/{r['real']['of']}   naive baseline {r['naive']['passed']}/{r['naive']['of']} ({r['naive']['rate']:.0%})")
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(json.dumps({"seeds": a.seeds, "families": rows}, indent=1))


if __name__ == "__main__":
    main()
