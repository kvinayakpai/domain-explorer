"""KG builder + API surface tests."""
from __future__ import annotations

import json
from pathlib import Path

import networkx as nx
import yaml


REPO_ROOT = Path(__file__).resolve().parents[3]


# ---- helpers --------------------------------------------------------------- #


def _fixture_taxonomy(tmp_path: Path) -> Path:
    """Write a tiny self-consistent registry under tmp_path/data/."""
    data = tmp_path / "data"
    (data / "taxonomy").mkdir(parents=True)
    (data / "kpis").mkdir()
    (data / "source-systems").mkdir()
    (data / "connectors").mkdir()
    (data / "glossary").mkdir()

    sub_a = {
        "id": "sub_a",
        "name": "Sub A",
        "vertical": "BFSI",
        "oneLiner": "First test subdomain.",
        "personas": [{"name": "VP A", "title": "VP of A", "level": "VP"}],
        "decisions": [{"id": "a.d.1", "statement": "Decide A."}],
        "kpis": [
            {
                "id": "a.kpi.1", "name": "A1", "formula": "x/y", "unit": "%",
                "direction": "higher_is_better", "decisionsSupported": ["a.d.1"],
            }
        ],
        "dataModel": {
            "entities": [
                {"name": "Account", "keys": ["account_id"]},
                {"name": "Transaction", "keys": ["txn_id"]},
            ]
        },
        "sourceSystems": [
            {"vendor": "Stripe", "product": "Payments", "category": "PSP"},
        ],
        "connectors": [{"type": "REST", "protocol": "HTTPS", "auth": "OAuth"}],
    }
    sub_b = {
        "id": "sub_b",
        "name": "Sub B",
        "vertical": "Insurance",
        "oneLiner": "Second test subdomain.",
        "personas": [
            {"name": "Director B", "title": "Director B", "level": "Director"},
            {"name": "Manager B", "title": "Manager B", "level": "Manager"},
        ],
        "decisions": [{"id": "b.d.1", "statement": "Decide B."}],
        "kpis": [],
        "sourceSystems": [],
        "connectors": [],
    }
    (data / "taxonomy" / "sub_a.yaml").write_text(yaml.safe_dump(sub_a), encoding="utf-8")
    (data / "taxonomy" / "sub_b.yaml").write_text(yaml.safe_dump(sub_b), encoding="utf-8")
    (data / "kpis" / "kpis.yaml").write_text(
        yaml.safe_dump({"kpis": [
            {"id": "a.kpi.1", "name": "A1", "formula": "x/y", "unit": "%",
             "direction": "higher_is_better", "vertical": "BFSI"}
        ]}),
        encoding="utf-8",
    )
    (data / "source-systems" / "sources.yaml").write_text(
        yaml.safe_dump({"sources": [
            {"id": "src.stripe", "vendor": "Stripe", "product": "Payments",
             "category": "PSP", "primaryConnectors": ["conn.rest"]}
        ]}),
        encoding="utf-8",
    )
    (data / "connectors" / "connectors.yaml").write_text(
        yaml.safe_dump({"connectors": [
            {"id": "conn.rest", "type": "REST", "protocol": "HTTPS", "auth": "OAuth",
             "latency": "realtime", "modes": ["pull"], "typicalSources": ["Stripe"]}
        ]}),
        encoding="utf-8",
    )
    (data / "glossary" / "glossary.yaml").write_text(
        yaml.safe_dump({"terms": [
            {"name": "ACH", "definition": "Automated Clearing House",
             "related_subdomains": ["sub_a"], "related_kpis": ["a.kpi.1"]}
        ]}),
        encoding="utf-8",
    )
    return data


# ---- builder tests --------------------------------------------------------- #


def test_build_graph_produces_expected_kinds_and_counts(tmp_path: Path):
    """Smoke: 2 subdomains -> 2 verticals (16 total), 1 KPI, 2 entities, 3 personas, ..."""
    import sys
    sys.path.insert(0, str(REPO_ROOT))
    from kg.build_graph import build_graph

    data = _fixture_taxonomy(tmp_path)
    g = build_graph(data)
    assert isinstance(g, nx.MultiDiGraph)

    # All 16 verticals are seeded as nodes regardless of which appear in the
    # taxonomy — the build always includes them so 'empty verticals' still
    # show up in the UI.
    kinds: dict[str, int] = {}
    for _, data_attrs in g.nodes(data=True):
        kinds[data_attrs["kind"]] = kinds.get(data_attrs["kind"], 0) + 1
    assert kinds["vertical"] == 16
    assert kinds["subdomain"] == 2
    assert kinds["persona"] == 3  # 1 + 2
    assert kinds["entity"] == 2
    assert kinds["kpi"] == 1
    assert kinds["decision"] == 2
    assert kinds["source"] == 1
    assert kinds["connector"] == 1
    assert kinds["term"] == 1


def test_build_graph_has_expected_edge_labels(tmp_path: Path):
    import sys
    sys.path.insert(0, str(REPO_ROOT))
    from kg.build_graph import build_graph

    data = _fixture_taxonomy(tmp_path)
    g = build_graph(data)
    labels: set[str] = set()
    for _, _, ed in g.edges(data=True):
        labels.add(ed["label"])
    # Required: vertical->subdomain, subdomain->persona/decision/kpi/entity,
    # persona->decision (owns), kpi->decision (supportsDecision), source->connector.
    for required in [
        "hasSubdomain",
        "hasPersona",
        "hasDecision",
        "hasKpi",
        "hasEntity",
        "owns",
        "supportsDecision",
        "reachedBy",
    ]:
        assert required in labels, f"missing edge label: {required} (got {sorted(labels)})"


def test_persona_to_kpi_traversal(tmp_path: Path):
    """End-to-end traversal: persona -owns-> decision <-supportsDecision- kpi."""
    import sys
    sys.path.insert(0, str(REPO_ROOT))
    from kg.build_graph import build_graph

    data = _fixture_taxonomy(tmp_path)
    g = build_graph(data)

    persona_node = "persona:sub_a::vp_a"
    assert g.has_node(persona_node)
    decisions = [v for _, v, ed in g.out_edges(persona_node, data=True) if ed["label"] == "owns"]
    assert decisions == ["decision:a.d.1"]

    kpis = [u for u, _, ed in g.in_edges(decisions[0], data=True) if ed["label"] == "supportsDecision"]
    assert kpis == ["kpi:a.kpi.1"]


def test_to_json_snapshot_round_trips(tmp_path: Path):
    import sys
    sys.path.insert(0, str(REPO_ROOT))
    from kg.build_graph import build_graph, force_layout, to_json_snapshot

    data = _fixture_taxonomy(tmp_path)
    g = build_graph(data)
    layout = force_layout(g, iterations=8)
    snap = to_json_snapshot(g, layout)
    assert snap["schemaVersion"] == 1
    assert snap["stats"]["nodes"] == g.number_of_nodes()
    assert snap["stats"]["edges"] == g.number_of_edges()
    # JSON-serialisable as committed.
    json.dumps(snap)


def test_force_layout_normalises_into_box(tmp_path: Path):
    import sys
    sys.path.insert(0, str(REPO_ROOT))
    from kg.build_graph import build_graph, force_layout

    data = _fixture_taxonomy(tmp_path)
    g = build_graph(data)
    layout = force_layout(g, iterations=5)
    xs = [x for x, _ in layout.values()]
    ys = [y for _, y in layout.values()]
    assert min(xs) >= -1
    assert max(xs) <= 1001
    assert min(ys) >= -1
    assert max(ys) <= 701


# ---- committed snapshot integration --------------------------------------- #


def test_committed_graph_json_loads_and_has_required_kinds():
    p = REPO_ROOT / "kg" / "graph.json"
    if not p.exists():
        import pytest
        pytest.skip("kg/graph.json not committed yet")
    snap = json.loads(p.read_text(encoding="utf-8"))
    counts = snap["stats"]["byKind"]
    assert counts.get("vertical", 0) == 16
    assert counts.get("subdomain", 0) >= 80
    assert counts.get("persona", 0) >= 100
    assert counts.get("kpi", 0) >= 50
