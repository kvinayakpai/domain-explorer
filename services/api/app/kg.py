"""Knowledge Graph API.

Loads the NetworkX MultiDiGraph emitted by ``kg/build_graph.py`` (preferring
the binary ``graph.gpickle`` for speed; falling back to the JSON snapshot).
Exposes a tiny query surface used by the explorer UI and the assistant
grounding layer:

* ``GET  /kg/stats``            — node/edge counts by kind.
* ``GET  /kg/node/{id}``        — fetch a node + its 1-hop neighbourhood.
* ``GET  /kg/path``             — shortest path between two nodes.
* ``POST /kg/query``            — Cypher-flavoured templated traversals
                                   (small subset; see ``KgQuery`` below).
* ``GET  /kg/snapshot``         — return the precomputed JSON snapshot
                                   (already laid out for the SVG demo view).

Prefer this API in the assistant grounding layer; the explorer-web library
falls back to a YAML-direct traversal when the API isn't reachable.
"""
from __future__ import annotations

import json
import pickle
from functools import lru_cache
from itertools import pairwise
from pathlib import Path
from typing import Any, Literal

import networkx as nx
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

router = APIRouter(prefix="/kg", tags=["knowledge-graph"])


def _repo_root() -> Path:
    here = Path(__file__).resolve()
    for parent in here.parents:
        if (parent / "kg").is_dir() and (parent / "data").is_dir():
            return parent
    raise RuntimeError("Could not locate repo root containing kg/ and data/")


def _kg_pickle_path() -> Path:
    return _repo_root() / "kg" / "graph.gpickle"


def _kg_json_path() -> Path:
    return _repo_root() / "kg" / "graph.json"


@lru_cache(maxsize=1)
def _load_graph() -> nx.MultiDiGraph:
    """Load the graph, preferring the pickle; rebuilding from JSON if needed."""
    p = _kg_pickle_path()
    if p.exists():
        with p.open("rb") as fh:
            g = pickle.load(fh)
        if isinstance(g, nx.MultiDiGraph):
            return g
        # Fall through to JSON.
    j = _kg_json_path()
    if j.exists():
        return _graph_from_snapshot(json.loads(j.read_text(encoding="utf-8")))
    raise HTTPException(
        status_code=503,
        detail="KG not built yet — run `python kg/build_graph.py`.",
    )


@lru_cache(maxsize=1)
def _load_snapshot() -> dict[str, Any]:
    j = _kg_json_path()
    if not j.exists():
        raise HTTPException(
            status_code=503,
            detail="KG snapshot missing — run `python kg/build_graph.py`.",
        )
    return json.loads(j.read_text(encoding="utf-8"))


def _graph_from_snapshot(snap: dict[str, Any]) -> nx.MultiDiGraph:
    g: nx.MultiDiGraph = nx.MultiDiGraph()
    for n in snap.get("nodes", []):
        attrs = {
            "kind": n.get("kind"),
            "label": n.get("label"),
            "vertical": n.get("vertical"),
            "subdomain": n.get("subdomain"),
            **(n.get("extras") or {}),
        }
        g.add_node(n["id"], **{k: v for k, v in attrs.items() if v is not None})
    for e in snap.get("edges", []):
        g.add_edge(e["source"], e["target"], label=e.get("label", ""))
    return g


# --------------------------------------------------------------------------- #
# Models                                                                      #
# --------------------------------------------------------------------------- #


class KgNode(BaseModel):
    id: str
    kind: str
    label: str
    extras: dict[str, Any] = Field(default_factory=dict)


class KgEdge(BaseModel):
    source: str
    target: str
    label: str


class KgNeighbourhood(BaseModel):
    node: KgNode
    neighbours: list[KgNode]
    edges: list[KgEdge]


class KgPath(BaseModel):
    source: str
    target: str
    length: int
    nodes: list[KgNode]
    edges: list[KgEdge]


class KgStats(BaseModel):
    nodes: int
    edges: int
    byKind: dict[str, int]


# Tiny Cypher-ish DSL for the assistant.
class KgQuery(BaseModel):
    template: Literal[
        "persona_to_kpis",
        "kpi_to_sources",
        "subdomain_to_entities",
        "vertical_to_subdomains",
        "kpi_to_decisions",
    ]
    persona_id: str | None = None
    kpi_id: str | None = None
    subdomain_id: str | None = None
    vertical_id: str | None = None
    limit: int = 50


class KgQueryResponse(BaseModel):
    template: str
    rows: list[dict[str, Any]]
    note: str


# --------------------------------------------------------------------------- #
# Helpers                                                                     #
# --------------------------------------------------------------------------- #


def _node_to_model(g: nx.MultiDiGraph, n: str) -> KgNode:
    data = g.nodes[n]
    return KgNode(
        id=n,
        kind=str(data.get("kind", "")),
        label=str(data.get("label", n)),
        extras={
            k: v
            for k, v in data.items()
            if k not in {"kind", "label"}
        },
    )


# --------------------------------------------------------------------------- #
# Endpoints                                                                   #
# --------------------------------------------------------------------------- #


@router.get("/stats", response_model=KgStats)
def stats() -> KgStats:
    g = _load_graph()
    counts: dict[str, int] = {}
    for _, data in g.nodes(data=True):
        counts[str(data.get("kind", "?"))] = counts.get(str(data.get("kind", "?")), 0) + 1
    return KgStats(nodes=g.number_of_nodes(), edges=g.number_of_edges(), byKind=counts)


@router.get("/snapshot")
def snapshot() -> dict[str, Any]:
    return _load_snapshot()


@router.get("/node/{node_id:path}", response_model=KgNeighbourhood)
def node(node_id: str) -> KgNeighbourhood:
    g = _load_graph()
    if not g.has_node(node_id):
        raise HTTPException(status_code=404, detail=f"node not found: {node_id}")
    neighbours: list[KgNode] = []
    edges: list[KgEdge] = []
    seen: set[str] = set()
    for u, v, data in g.out_edges(node_id, data=True):
        if v not in seen:
            neighbours.append(_node_to_model(g, v))
            seen.add(v)
        edges.append(KgEdge(source=u, target=v, label=str(data.get("label", ""))))
    for u, v, data in g.in_edges(node_id, data=True):
        if u not in seen:
            neighbours.append(_node_to_model(g, u))
            seen.add(u)
        edges.append(KgEdge(source=u, target=v, label=str(data.get("label", ""))))
    return KgNeighbourhood(
        node=_node_to_model(g, node_id),
        neighbours=neighbours,
        edges=edges,
    )


@router.get("/path", response_model=KgPath)
def path(source: str, target: str) -> KgPath:
    g = _load_graph()
    if not g.has_node(source) or not g.has_node(target):
        raise HTTPException(status_code=404, detail="source or target node not found")
    # Shortest path on the underlying undirected view.
    try:
        nodes = nx.shortest_path(g.to_undirected(as_view=True), source=source, target=target)
    except nx.NetworkXNoPath as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    edges: list[KgEdge] = []
    for u, v in pairwise(nodes):
        # Pick any edge between u and v in either direction.
        if g.has_edge(u, v):
            data = next(iter(g[u][v].values()))
        elif g.has_edge(v, u):
            data = next(iter(g[v][u].values()))
            u, v = v, u
        else:
            data = {"label": ""}
        edges.append(KgEdge(source=u, target=v, label=str(data.get("label", ""))))
    return KgPath(
        source=source,
        target=target,
        length=len(nodes) - 1,
        nodes=[_node_to_model(g, n) for n in nodes],
        edges=edges,
    )


@router.post("/query", response_model=KgQueryResponse)
def query(req: KgQuery) -> KgQueryResponse:
    """Tiny templated traversal layer.

    This isn't real Cypher — it's a fixed set of named templates so we can
    stay schema-aware on the API side. The shape stays compatible with a
    future Neo4j or Memgraph backend (each template maps cleanly to the
    matching query under ``kg/cypher/``).
    """
    g = _load_graph()
    rows: list[dict[str, Any]] = []
    note = ""

    if req.template == "persona_to_kpis":
        if not req.persona_id:
            raise HTTPException(status_code=400, detail="persona_id required")
        node_id = req.persona_id if req.persona_id.startswith("persona:") else f"persona:{req.persona_id}"
        if not g.has_node(node_id):
            raise HTTPException(status_code=404, detail=f"persona not found: {node_id}")
        # persona -> decisions -> kpis (reversed via supportsDecision).
        decisions = [
            v
            for _, v, data in g.out_edges(node_id, data=True)
            if data.get("label") == "owns" and g.nodes[v].get("kind") == "decision"
        ]
        for d in decisions:
            for k, _, data in g.in_edges(d, data=True):
                if data.get("label") == "supportsDecision" and g.nodes[k].get("kind") == "kpi":
                    rows.append(
                        {
                            "persona": node_id,
                            "decision": d,
                            "decision_label": g.nodes[d].get("label"),
                            "kpi": k,
                            "kpi_label": g.nodes[k].get("label"),
                            "kpi_formula": g.nodes[k].get("formula", ""),
                        }
                    )

    elif req.template == "kpi_to_sources":
        if not req.kpi_id:
            raise HTTPException(status_code=400, detail="kpi_id required")
        node_id = req.kpi_id if req.kpi_id.startswith("kpi:") else f"kpi:{req.kpi_id}"
        if not g.has_node(node_id):
            raise HTTPException(status_code=404, detail=f"kpi not found: {node_id}")
        # kpi <- subdomain -> sourceLocal (and the source registry, if linked).
        for u, _, data in g.in_edges(node_id, data=True):
            if data.get("label") == "hasKpi":
                # u is the subdomain.
                for _, v, edata in g.out_edges(u, data=True):
                    if edata.get("label") == "usesSource":
                        rows.append(
                            {
                                "kpi": node_id,
                                "subdomain": u,
                                "source": v,
                                "source_label": g.nodes[v].get("label"),
                                "vendor": g.nodes[v].get("vendor"),
                                "product": g.nodes[v].get("product"),
                                "category": g.nodes[v].get("category"),
                            }
                        )

    elif req.template == "subdomain_to_entities":
        if not req.subdomain_id:
            raise HTTPException(status_code=400, detail="subdomain_id required")
        node_id = (
            req.subdomain_id
            if req.subdomain_id.startswith("subdomain:")
            else f"subdomain:{req.subdomain_id}"
        )
        if not g.has_node(node_id):
            raise HTTPException(status_code=404, detail=f"subdomain not found: {node_id}")
        for _, v, data in g.out_edges(node_id, data=True):
            if data.get("label") == "hasEntity":
                rows.append(
                    {
                        "subdomain": node_id,
                        "entity": v,
                        "entity_label": g.nodes[v].get("label"),
                        "keys": g.nodes[v].get("keys", []),
                    }
                )

    elif req.template == "vertical_to_subdomains":
        if not req.vertical_id:
            raise HTTPException(status_code=400, detail="vertical_id required")
        node_id = (
            req.vertical_id
            if req.vertical_id.startswith("vertical:")
            else f"vertical:{req.vertical_id}"
        )
        if not g.has_node(node_id):
            raise HTTPException(status_code=404, detail=f"vertical not found: {node_id}")
        for _, v, data in g.out_edges(node_id, data=True):
            if data.get("label") == "hasSubdomain":
                rows.append(
                    {
                        "vertical": node_id,
                        "subdomain": v,
                        "subdomain_label": g.nodes[v].get("label"),
                        "oneLiner": g.nodes[v].get("oneLiner", ""),
                    }
                )

    elif req.template == "kpi_to_decisions":
        if not req.kpi_id:
            raise HTTPException(status_code=400, detail="kpi_id required")
        node_id = req.kpi_id if req.kpi_id.startswith("kpi:") else f"kpi:{req.kpi_id}"
        if not g.has_node(node_id):
            raise HTTPException(status_code=404, detail=f"kpi not found: {node_id}")
        for _, v, data in g.out_edges(node_id, data=True):
            if data.get("label") == "supportsDecision":
                rows.append(
                    {
                        "kpi": node_id,
                        "decision": v,
                        "decision_label": g.nodes[v].get("label"),
                    }
                )

    rows = rows[: req.limit]
    note = f"Backend: NetworkX in-memory graph ({g.number_of_nodes()} nodes)."
    return KgQueryResponse(template=req.template, rows=rows, note=note)
