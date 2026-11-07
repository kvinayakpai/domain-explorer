"""Seed sweep: does the pipeline still work on worlds it was not tuned on?

usage: python -m factory_to_field.eval.seeds [--seeds 1 2 3 ...] [--out DIR] [--skip-agent]

For each seed: build a fresh world, resolve identities, score links against that world's own truth file,
then (unless --skip-agent) run the ten gold cases. Seed 42 is the development seed; every other seed is held out.
Results are written to build/eval/seed-sweep.json and printed as one line per seed.
"""
from __future__ import annotations

import argparse
import json
import tempfile
import time
import traceback
from pathlib import Path

from ..kg import evaluate
from ..kg.pipeline import Pipeline
from ..world.build import build

OUT = Path(__file__).resolve().parents[1] / "build" / "eval"
DEV_SEED = 42


def run_seed(seed: int, agent: bool = True, noise: str = "base") -> dict:
    t0 = time.time()
    r: dict = {"seed": seed, "noise": noise, "dev": seed == DEV_SEED and noise == "base"}
    with tempfile.TemporaryDirectory() as td:
        wd = Path(td) / "world"
        try:
            build(wd, seed, noise)
        except Exception as e:  # a world that cannot be built is a result, not a crash
            r["error"] = f"world: {type(e).__name__}: {e}"
            return r
        try:
            res = Pipeline(wd, None).build()
            sc = evaluate.score(res, wd / "truth.json")
            r["links"] = {k: sc[k] for k in ("links_truth", "recall", "precision")}
            r["worst_source"] = min(sc["by_source"].items(), key=lambda kv: kv[1]["recall"])[0] if sc["by_source"] else None
        except Exception as e:
            r["error"] = f"resolve: {type(e).__name__}: {e}"
            r["trace"] = traceback.format_exc()[-800:]
            return r
        if agent:
            try:
                from ..agents import gold
                g = gold.score(world=wd)
                r["agent"] = {"cases_ok": g["cases_ok"], "cases_total": g["cases_total"], "passed": g["passed"], "checks": g["checks"],
                              "failed": {c["case"]: [k for k, v in c["checks"].items() if not v] + c["problems"][:2] for c in g["cases"] if not c["ok"]}}
            except Exception as e:
                r["agent"] = {"error": f"{type(e).__name__}: {e}"}
                r["trace"] = traceback.format_exc()[-800:]
    r["seconds"] = round(time.time() - t0)
    return r


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, nargs="*", default=[DEV_SEED, 1, 2, 3, 4])
    ap.add_argument("--noise", default="base", help="base or dirty")
    ap.add_argument("--skip-agent", action="store_true")
    ap.add_argument("--out", type=Path, default=OUT / "seed-sweep.json")
    a = ap.parse_args()
    rows = []
    for s in a.seeds:
        r = run_seed(s, not a.skip_agent, a.noise)
        rows.append(r)
        l = r.get("links", {}); g = r.get("agent", {})
        print(f"{a.noise} seed {s:>4}{' (dev)' if r['dev'] else '      '} "
              + (f"links recall {l.get('recall')} precision {l.get('precision')}" if l else r.get("error", ""))
              + (f" | agent {g.get('cases_ok')}/{g.get('cases_total')}" if "cases_ok" in g else (f" | agent {g.get('error')}" if g else "")), flush=True)
        for c, why in g.get("failed", {}).items():
            print(f"      {c}: {'; '.join(why)[:160]}")
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(json.dumps(rows, indent=1))


if __name__ == "__main__":
    main()
