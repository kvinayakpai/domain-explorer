"""Build, validate and load the knowledge graph.

usage: python -m factory_to_field.kg.build [--world DIR] [--out DIR] [--skip-shacl] [--decisions FILE]
"""
from __future__ import annotations

import argparse
import json
import shutil
import time
from pathlib import Path

from rdflib import BNode, Dataset, URIRef

from . import evaluate, shapes
from .pipeline import Pipeline
from .rdfutil import DATA_GRAPH, PROV_GRAPH
from .store import KG

ROOT = Path(__file__).resolve().parents[1] / "build"
SKOLEM = "https://domain-explorer.dev/ftf/.well-known/genid/"


def _skolem(t):
    """Blank nodes become IRIs before loading. Oxigraph's bulk_load parses N-Quads in parallel chunks, and
    blank-node labels are not shared across chunks, so with enough CPUs a node's triples were split over
    several nodes (identifiers lost their system/kind/value on multi-core runners)."""
    return URIRef(SKOLEM + str(t)) if isinstance(t, BNode) else t


def build_kg(world: Path = ROOT / "world", out: Path = ROOT / "kg", skip_shacl: bool = False, decisions: dict | None = None) -> dict:
    t0 = time.time()
    out.mkdir(parents=True, exist_ok=True)
    res = Pipeline(world, decisions).build()
    metrics: dict = {"stats": res.stats}
    metrics["resolution"] = evaluate.score(res, world / "truth.json")
    if skip_shacl:
        metrics["shacl"] = {"conforms": None, "skipped": True}
    else:
        t = time.time()
        ok, text, _ = shapes.validate_graph(res.builder.g)
        metrics["shacl"] = {"conforms": ok, "seconds": round(time.time() - t), "report": None if ok else text[:4000]}
    ds = Dataset()
    for s, p, o in res.builder.g:
        ds.graph(DATA_GRAPH).add((_skolem(s), p, _skolem(o)))
    for s, p, o in res.builder.prov:
        ds.graph(PROV_GRAPH).add((_skolem(s), p, _skolem(o)))
    nq = out / "kg.nq"
    ds.serialize(destination=str(nq), format="nquads")
    (out / "graph.ttl").write_text(res.builder.g.serialize(format="turtle"))
    (out / "provenance.ttl").write_text(res.builder.prov.serialize(format="turtle"))
    (out / "review_queue.json").write_text(json.dumps(res.review, indent=1))
    (out / "links.json").write_text(json.dumps([l.__dict__ for l in res.links]))
    store_dir = out / "store"
    if store_dir.exists():
        shutil.rmtree(store_dir)
    KG.from_nquads(nq, store_dir)
    metrics["seconds"] = round(time.time() - t0)
    metrics["review_queue"] = len(res.review)
    gate = metrics["resolution"]["gate"]["passed"] and (metrics["shacl"]["conforms"] in (True, None))
    metrics["gate_passed"] = bool(gate)
    (out / "metrics.json").write_text(json.dumps(metrics, indent=1))
    return metrics


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--world", type=Path, default=ROOT / "world")
    ap.add_argument("--out", type=Path, default=ROOT / "kg")
    ap.add_argument("--skip-shacl", action="store_true")
    ap.add_argument("--decisions", type=Path)
    a = ap.parse_args()
    dec = json.loads(a.decisions.read_text()) if a.decisions else None
    m = build_kg(a.world, a.out, a.skip_shacl, dec)
    r = m["resolution"]
    print(f"KG: {m['stats']['triples']} triples, {m['stats']['nodes']} nodes | links recall {r['recall']:.4f} precision {r['precision']:.4f} | "
          f"SHACL {m['shacl']['conforms']} | review queue {m['review_queue']} | gate {'PASS' if m['gate_passed'] else 'FAIL'} ({m['seconds']}s)")
