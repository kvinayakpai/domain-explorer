"""Score the resolved links against the truth file written by the world builder."""
from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

from .pipeline import Result

GATE_RECALL = 0.95
GATE_PRECISION = 0.98


def score(res: Result, truth_path: Path) -> dict:
    truth = defaultdict(set)  # (system, table, key) -> {canon}
    for system, table, key, canon in json.loads(truth_path.read_text()):
        if system == "TRUTH":
            system, table = "PLM", table
            key = key
        truth[(system, table, key)].add(canon)
    pred = defaultdict(set)
    for l in res.links:
        pred[(l.system, l.table, l.key)].add(_norm(l.canon))
    out: dict = {"by_source": {}}
    tp = fp = fn = 0
    for (system, table, key), want in truth.items():
        if system == "TRUTH":
            continue
        want = {_norm(x) for x in want}
        got = pred.get((system, table, key), set())
        hit = len(want & got)
        miss = len(want - got)
        wrong = len(got - want)
        s = out["by_source"].setdefault(f"{system}.{table}", {"tp": 0, "fp": 0, "fn": 0})
        s["tp"] += hit; s["fp"] += wrong; s["fn"] += miss
        tp += hit; fp += wrong; fn += miss
    for s in out["by_source"].values():
        s["recall"] = round(s["tp"] / max(s["tp"] + s["fn"], 1), 4)
        s["precision"] = round(s["tp"] / max(s["tp"] + s["fp"], 1), 4)
    out["links_truth"] = tp + fn
    out["recall"] = round(tp / max(tp + fn, 1), 4)
    out["precision"] = round(tp / max(tp + fp, 1), 4)
    out["gate"] = {"recall": GATE_RECALL, "precision": GATE_PRECISION, "passed": out["recall"] >= GATE_RECALL and out["precision"] >= GATE_PRECISION}
    return out


def _norm(c: str) -> str:
    return c
