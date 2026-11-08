"""Worlds the pipeline was not tuned on. Seed 42 is the development seed; these seeds are held out.
FTF_SEEDS="1 2 3" widens the sweep (CI does)."""
import os

import pytest
from factory_to_field.eval.seeds import run_seed

SEEDS = [int(x) for x in os.environ.get("FTF_SEEDS", "1").split()]
FLOOR_RECALL, FLOOR_PRECISION = 0.995, 0.99


@pytest.mark.parametrize("seed", SEEDS)
def test_heldout_seed(seed):
    r = run_seed(seed)
    assert "error" not in r, r
    assert r["links"]["recall"] >= FLOOR_RECALL and r["links"]["precision"] >= FLOOR_PRECISION, r["links"]
    a = r["agent"]
    assert a.get("cases_ok") == a.get("cases_total"), a.get("failed") or a


def test_hostile_noise_seed():
    """Serial damage the base generator never produced: transposed digits, O for 0, lost separators, label text."""
    r = run_seed(1, noise="hostile")
    assert "error" not in r, r
    assert r["links"]["recall"] >= 0.99 and r["links"]["precision"] >= 0.995, r["links"]
    assert r["agent"]["cases_ok"] == r["agent"]["cases_total"], r["agent"].get("failed")
