"""Build the synthetic world and write every source system's files.

usage: python -m factory_to_field.world.build [--out DIR] [--seed N]
"""
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

from . import gen_factory, gen_field, gen_refinery, render, signals, stories
from .model import World
from .spec import SEED

DEFAULT_OUT = Path(__file__).resolve().parents[1] / "build" / "world"


def make_world(seed: int = SEED) -> World:
    import numpy as np
    w = World(seed=seed, rng=np.random.default_rng(seed))
    gen_factory.setup_orgs_and_customers(w)
    gen_factory.setup_changes_and_lots(w)
    gen_refinery.generate(w)
    gen_field.generate(w)
    gen_factory.bulk_production(w)
    signals.generate(w)
    return w


def build(out: Path = DEFAULT_OUT, seed: int = SEED) -> World:
    t0 = time.time()
    w = make_world(seed)
    tr = render.render_all(w, out)
    key = stories.build(w)
    (out / "truth.json").write_text(json.dumps([list(r) for r in tr.rows]))
    (out / "answer_key.json").write_text(json.dumps(key, indent=1, default=str))
    (out / "MANIFEST.json").write_text(json.dumps({"seed": seed, "files": sorted(p.name for p in out.iterdir()),
                                                   "note": "All data is synthetic. truth.json and answer_key.json are for scoring only."}, indent=1))
    print(f"world built in {time.time() - t0:.1f}s -> {out}")
    return w


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT)
    ap.add_argument("--seed", type=int, default=SEED)
    a = ap.parse_args()
    build(a.out, a.seed)
