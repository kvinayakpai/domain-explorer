"""
Build the Domain Explorer knowledge graph.

Reads the typed YAML registry under ``data/`` (verticals, subdomains, personas,
decisions, KPIs, source systems, connectors, glossary terms, entities) and
emits two artefacts under ``kg/``:

* ``graph.gpickle``  — full NetworkX MultiDiGraph (gitignored, regenerated).
* ``graph.json``     — serialized snapshot with precomputed force-directed
                       layout. Committed and used by the web UI / demo mode.

Usage:
    python kg/build_graph.py --data-root data --out kg

The graph schema (node ``kind`` values + edge labels) is the contract the
API and UI depend on. Keep it stable.
"""
from __future__ import annotations

import argparse
import json
import pickle
import random
import sys
from pathlib import Path
from typing import Any

import networkx as nx
import yaml

# Vertical labels (mirrors apps/explorer-web/lib/registry.ts VERTICALS).
VERTICAL_LABELS: dict[str, str] = {
    "BFSI": "Banking & Financial Services",
    "Insurance": "Insurance",
    "Retail": "Retail",
    "RCG": "Retail & Consumer Goods",
    "CPG": "Consumer Packaged Goods",
    "TTH": "Travel, Transportation & Hospitality",
    "Manufacturing": "Manufacturing",
    "LifeSciences": "Life Sciences",
    "Healthcare": "Healthcare",
    "Telecom": "Telecom",
    "Media": "Media",
    "Energy": "Energy",
    "Utilities": "Utilities",
    "PublicSector": "Public Sector",
    "HiTech": "Hi-Tech",
    "ProfessionalServices": "Professional Services",
}


def _read_yaml_dir(d: Path) -> list[Any]:
    if not d.exists():
        return []
    out: list[Any] = []
    for f in sorted(d.iterdir()):
        if f.suffix.lower() in {".yaml", ".yml"}:
            with f.open("r", encoding="utf-8") as fh:
                out.append(yaml.safe_load(fh))
    return out


def _slug(s: str) -> str:
    return "".join(ch.lower() if ch.isalnum() else "_" for ch in s).strip("_")


def build_graph(data_root: Path) -> nx.MultiDiGraph:
    """Build the multi-edge directed graph from the registry."""
    g: nx.MultiDiGraph = nx.MultiDiGraph()

    # ---- Verticals ----
    for slug, label in VERTICAL_LABELS.items():
        nid = f"vertical:{slug}"
        g.add_node(nid, kind="vertical", id=slug, label=label)

    # ---- Subdomains + their nested objects ----
    for raw in _read_yaml_dir(data_root / "taxonomy"):
        if not raw:
            continue
        sid = raw["id"]
        sub_node = f"subdomain:{sid}"
        g.add_node(
            sub_node,
            kind="subdomain",
            id=sid,
            label=raw["name"],
            vertical=raw["vertical"],
            oneLiner=raw.get("oneLiner", ""),
        )
        v_node = f"vertical:{raw['vertical']}"
        if g.has_node(v_node):
            g.add_edge(v_node, sub_node, label="hasSubdomain")

        # Personas — keyed by (subdomain, name).
        for p in raw.get("personas", []) or []:
            pid = f"persona:{sid}::{_slug(p['name'])}"
            g.add_node(
                pid,
                kind="persona",
                id=pid.split(":", 1)[1],
                label=p["name"],
                title=p.get("title", ""),
                level=p.get("level", ""),
                subdomain=sid,
            )
            g.add_edge(sub_node, pid, label="hasPersona")

        # Decisions.
        for d in raw.get("decisions", []) or []:
            did = f"decision:{d['id']}"
            g.add_node(
                did,
                kind="decision",
                id=d["id"],
                label=d.get("statement", d["id"])[:80],
                statement=d.get("statement", ""),
                subdomain=sid,
            )
            g.add_edge(sub_node, did, label="hasDecision")
            # All personas in this subdomain "own" the decisions (best-effort
            # mapping — the YAML doesn't carry persona→decision links yet).
            for p in raw.get("personas", []) or []:
                pid = f"persona:{sid}::{_slug(p['name'])}"
                g.add_edge(pid, did, label="owns")

        # KPIs (subdomain-local).
        for k in raw.get("kpis", []) or []:
            kid = f"kpi:{k['id']}"
            g.add_node(
                kid,
                kind="kpi",
                id=k["id"],
                label=k["name"],
                formula=k.get("formula", ""),
                unit=k.get("unit", ""),
                direction=k.get("direction", ""),
                subdomain=sid,
            )
            g.add_edge(sub_node, kid, label="hasKpi")
            for d_ref in k.get("decisionsSupported", []) or []:
                did = f"decision:{d_ref}"
                if g.has_node(did):
                    g.add_edge(kid, did, label="supportsDecision")

        # Entities.
        for e in (raw.get("dataModel") or {}).get("entities", []) or []:
            eid = f"entity:{sid}::{_slug(e['name'])}"
            g.add_node(
                eid,
                kind="entity",
                id=eid.split(":", 1)[1],
                label=e["name"],
                subdomain=sid,
                keys=e.get("keys", []),
            )
            g.add_edge(sub_node, eid, label="hasEntity")

        # Source systems mentioned inline (de-duped against the registry below).
        for s in raw.get("sourceSystems", []) or []:
            sid_node = f"sourceLocal:{sid}::{_slug(s['vendor'])}_{_slug(s['product'])}"
            g.add_node(
                sid_node,
                kind="source_local",
                id=sid_node.split(":", 1)[1],
                label=f"{s['vendor']} {s['product']}",
                vendor=s["vendor"],
                product=s["product"],
                category=s.get("category", ""),
                subdomain=sid,
            )
            g.add_edge(sub_node, sid_node, label="usesSource")

        # Local connector patterns.
        for c in raw.get("connectors", []) or []:
            cid_node = (
                f"connectorLocal:{sid}::{_slug(c['type'])}_{_slug(c['protocol'])}"
            )
            g.add_node(
                cid_node,
                kind="connector_local",
                id=cid_node.split(":", 1)[1],
                label=f"{c['type']} ({c['protocol']})",
                type=c["type"],
                protocol=c["protocol"],
                auth=c.get("auth", ""),
                subdomain=sid,
            )
            g.add_edge(sub_node, cid_node, label="usesConnector")

    # ---- Cross-vertical KPI registry ----
    for raw in _read_yaml_dir(data_root / "kpis"):
        for k in (raw or {}).get("kpis", []) or []:
            kid = f"kpi:{k['id']}"
            if not g.has_node(kid):
                g.add_node(
                    kid,
                    kind="kpi",
                    id=k["id"],
                    label=k["name"],
                    formula=k.get("formula", ""),
                    unit=k.get("unit", ""),
                    direction=k.get("direction", ""),
                    vertical=k.get("vertical", ""),
                )
            elif k.get("vertical") and "vertical" not in g.nodes[kid]:
                g.nodes[kid]["vertical"] = k["vertical"]

    # ---- Source systems registry ----
    for raw in _read_yaml_dir(data_root / "source-systems"):
        for s in (raw or {}).get("sources", []) or []:
            sid_node = f"source:{s['id']}"
            g.add_node(
                sid_node,
                kind="source",
                id=s["id"],
                label=f"{s['vendor']} {s['product']}",
                vendor=s["vendor"],
                product=s["product"],
                category=s.get("category", ""),
            )
            for cref in s.get("primaryConnectors", []) or []:
                cnode = f"connector:{cref}"
                if g.has_node(cnode):
                    g.add_edge(sid_node, cnode, label="reachedBy")

    # ---- Connector patterns registry ----
    for raw in _read_yaml_dir(data_root / "connectors"):
        for c in (raw or {}).get("connectors", []) or []:
            cid_node = f"connector:{c['id']}"
            if not g.has_node(cid_node):
                g.add_node(
                    cid_node,
                    kind="connector",
                    id=c["id"],
                    label=c["type"],
                    type=c["type"],
                    protocol=c["protocol"],
                    auth=c.get("auth", ""),
                    latency=c.get("latency", ""),
                    modes=c.get("modes", []),
                )

    # Resolve the source.primaryConnectors edges that may have been deferred.
    for raw in _read_yaml_dir(data_root / "source-systems"):
        for s in (raw or {}).get("sources", []) or []:
            sid_node = f"source:{s['id']}"
            for cref in s.get("primaryConnectors", []) or []:
                cnode = f"connector:{cref}"
                if g.has_node(cnode) and not g.has_edge(sid_node, cnode):
                    g.add_edge(sid_node, cnode, label="reachedBy")

    # ---- Glossary terms ----
    for raw in _read_yaml_dir(data_root / "glossary"):
        for t in (raw or {}).get("terms", []) or []:
            tid = f"term:{_slug(t['name'])}"
            g.add_node(
                tid,
                kind="term",
                id=tid.split(":", 1)[1],
                label=t["name"],
                definition=t.get("definition", ""),
                aliases=t.get("aliases", []),
            )
            for sref in t.get("related_subdomains", []) or []:
                snode = f"subdomain:{sref}"
                if g.has_node(snode):
                    g.add_edge(tid, snode, label="termRelatedTo")
            for kref in t.get("related_kpis", []) or []:
                kn = f"kpi:{kref}"
                if g.has_node(kn):
                    g.add_edge(tid, kn, label="termRelatedTo")

    return g


def force_layout(
    g: nx.MultiDiGraph, iterations: int = 80, seed: int = 42
) -> dict[str, tuple[float, float]]:
    """Cheap deterministic spring layout for the snapshot.

    We bias the initial positions by ``kind`` so the JSON snapshot already
    looks sensible if the consumer chooses not to re-run a layout.
    """
    rng = random.Random(seed)
    # Coarse seeding by kind — keeps verticals on the left, KPIs on the right.
    band = {
        "vertical": -1.0,
        "subdomain": -0.6,
        "persona": -0.2,
        "entity": -0.1,
        "source": 0.2,
        "source_local": 0.2,
        "connector": 0.5,
        "connector_local": 0.5,
        "decision": 0.2,
        "kpi": 0.8,
        "term": 0.0,
    }
    pos: dict[str, list[float]] = {}
    for n, data in g.nodes(data=True):
        kx = band.get(data.get("kind", ""), 0.0)
        pos[n] = [
            kx * 600 + rng.uniform(-80, 80),
            rng.uniform(-400, 400),
        ]

    # Spring forces — attractive along edges, repulsive between all pairs.
    nodes = list(g.nodes())
    n = len(nodes)
    if n == 0:
        return {}
    k_attr = 1.0 / max(g.number_of_edges(), 1)
    k_rep = 1500.0

    edges = [(u, v) for u, v in g.edges() if u != v]

    for it in range(iterations):
        cooling = 1.0 - it / iterations
        forces: dict[str, list[float]] = {nid: [0.0, 0.0] for nid in nodes}
        # Repulsion (sampled to keep this O(n*k) on big graphs).
        sample_size = min(40, n - 1)
        for a in nodes:
            ax, ay = pos[a]
            sample = rng.sample([x for x in nodes if x != a], sample_size)
            for b in sample:
                bx, by = pos[b]
                dx, dy = ax - bx, ay - by
                d2 = dx * dx + dy * dy + 0.01
                f = k_rep / d2
                forces[a][0] += dx * f * 0.001
                forces[a][1] += dy * f * 0.001
        # Attraction along edges.
        for u, v in edges:
            ux, uy = pos[u]
            vx, vy = pos[v]
            dx, dy = vx - ux, vy - uy
            forces[u][0] += dx * k_attr * 60
            forces[u][1] += dy * k_attr * 60
            forces[v][0] -= dx * k_attr * 60
            forces[v][1] -= dy * k_attr * 60
        for nid in nodes:
            pos[nid][0] += forces[nid][0] * cooling
            pos[nid][1] += forces[nid][1] * cooling

    # Normalise into a 0..1000 box.
    xs = [p[0] for p in pos.values()]
    ys = [p[1] for p in pos.values()]
    if xs and ys:
        x0, x1 = min(xs), max(xs)
        y0, y1 = min(ys), max(ys)
        sx = 1000 / max(x1 - x0, 1)
        sy = 700 / max(y1 - y0, 1)
        scale = min(sx, sy)
        for nid in pos:
            pos[nid][0] = round((pos[nid][0] - x0) * scale, 2)
            pos[nid][1] = round((pos[nid][1] - y0) * scale, 2)
    return {k: (v[0], v[1]) for k, v in pos.items()}


def to_json_snapshot(
    g: nx.MultiDiGraph, layout: dict[str, tuple[float, float]]
) -> dict[str, Any]:
    """Serialize the graph as a JSON-friendly dict for the UI."""
    nodes_out = []
    for n, data in g.nodes(data=True):
        x, y = layout.get(n, (0.0, 0.0))
        nodes_out.append(
            {
                "id": n,
                "kind": data.get("kind", "unknown"),
                "label": data.get("label", n),
                "vertical": data.get("vertical"),
                "subdomain": data.get("subdomain"),
                "x": x,
                "y": y,
                "extras": {
                    k: v
                    for k, v in data.items()
                    if k
                    not in {
                        "kind",
                        "label",
                        "vertical",
                        "subdomain",
                        "id",
                    }
                    and isinstance(v, (str, int, float, bool, list))
                },
            }
        )
    edges_out = []
    for u, v, data in g.edges(data=True):
        edges_out.append(
            {"source": u, "target": v, "label": data.get("label", "")}
        )
    counts: dict[str, int] = {}
    for _, data in g.nodes(data=True):
        counts[data.get("kind", "unknown")] = counts.get(data.get("kind", "unknown"), 0) + 1
    return {
        "schemaVersion": 1,
        "stats": {
            "nodes": g.number_of_nodes(),
            "edges": g.number_of_edges(),
            "byKind": counts,
        },
        "nodes": nodes_out,
        "edges": edges_out,
    }


def write_outputs(g: nx.MultiDiGraph, out_dir: Path) -> tuple[Path, Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    pickle_path = out_dir / "graph.gpickle"
    with pickle_path.open("wb") as fh:
        pickle.dump(g, fh, protocol=4)

    layout = force_layout(g)
    snap = to_json_snapshot(g, layout)
    json_path = out_dir / "graph.json"
    json_path.write_text(json.dumps(snap, separators=(",", ":")), encoding="utf-8")
    return pickle_path, json_path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Build the Domain Explorer knowledge graph."
    )
    parser.add_argument("--data-root", type=Path, default=Path("data"))
    parser.add_argument("--out", type=Path, default=Path("kg"))
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args(argv)

    g = build_graph(args.data_root)
    pickle_path, json_path = write_outputs(g, args.out)

    if not args.quiet:
        kinds: dict[str, int] = {}
        for _, data in g.nodes(data=True):
            kinds[data.get("kind", "?")] = kinds.get(data.get("kind", "?"), 0) + 1
        print(
            f"KG built: {g.number_of_nodes()} nodes, {g.number_of_edges()} edges "
            f"→ {pickle_path} + {json_path}"
        )
        for k, n in sorted(kinds.items(), key=lambda kv: -kv[1]):
            print(f"  {k:18s} {n}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
