"""Tests for the Pydantic-backed YAML loader."""
from __future__ import annotations

from pathlib import Path

import pytest
import yaml
from pydantic import ValidationError

from metadata import (
    Connector,
    ConnectorPattern,
    Decision,
    Kpi,
    KpiRegistryEntry,
    Persona,
    SourceSystemEntry,
    Subdomain,
    load_registry,
)


REPO_ROOT = Path(__file__).resolve().parents[4]
DATA_ROOT = REPO_ROOT / "data"


# --------------------------------------------------------------------------- #
# Field-level schema validation                                               #
# --------------------------------------------------------------------------- #


def test_persona_requires_name_title_level():
    with pytest.raises(ValidationError):
        Persona.model_validate({"name": "x", "title": "y"})  # missing level
    with pytest.raises(ValidationError):
        Persona.model_validate({"name": "x", "title": "y", "level": "Wizard"})  # bad enum
    p = Persona.model_validate({"name": "x", "title": "y", "level": "Director"})
    assert p.level == "Director"


def test_kpi_direction_enum_strict():
    base = {"id": "k.x", "name": "X", "formula": "a/b", "unit": "%"}
    with pytest.raises(ValidationError):
        Kpi.model_validate({**base, "direction": "up"})
    with pytest.raises(ValidationError):
        Kpi.model_validate({**base, "direction": ""})
    Kpi.model_validate({**base, "direction": "higher_is_better"})


def test_decision_id_required():
    with pytest.raises(ValidationError):
        Decision.model_validate({"statement": "Pick a rail"})
    Decision.model_validate({"id": "d.1", "statement": "Pick a rail"})


def test_connector_strict_extras_rejected():
    """`extra='forbid'` should drop unknown fields."""
    with pytest.raises(ValidationError):
        Connector.model_validate({"type": "REST", "protocol": "HTTPS", "auth": "OAuth", "extra": "no"})


def test_connector_pattern_latency_enum():
    base = {
        "id": "c.x", "type": "REST", "protocol": "HTTPS", "auth": "OAuth",
    }
    with pytest.raises(ValidationError):
        ConnectorPattern.model_validate({**base, "latency": "instant"})
    ConnectorPattern.model_validate({**base, "latency": "realtime"})


def test_kpi_registry_entry_inherits_kpi_plus_vertical():
    raw = {
        "id": "pay.kpi.stp_rate", "name": "STP Rate", "formula": "a/b", "unit": "%",
        "direction": "higher_is_better", "vertical": "BFSI",
    }
    entry = KpiRegistryEntry.model_validate(raw)
    assert entry.vertical.value == "BFSI"


def test_source_system_default_connectors_empty():
    raw = {"id": "src.x", "vendor": "X", "product": "Y", "category": "Z"}
    s = SourceSystemEntry.model_validate(raw)
    assert s.primaryConnectors == []


# --------------------------------------------------------------------------- #
# Subdomain end-to-end                                                        #
# --------------------------------------------------------------------------- #


def _good_subdomain_dict() -> dict:
    return {
        "id": "test_sub",
        "name": "Test Sub",
        "vertical": "BFSI",
        "oneLiner": "Test one-liner.",
        "personas": [{"name": "X", "title": "Head of X", "level": "VP"}],
        "decisions": [{"id": "d.1", "statement": "Decide stuff."}],
        "kpis": [
            {
                "id": "k.1", "name": "K1", "formula": "a/b", "unit": "%",
                "direction": "higher_is_better", "decisionsSupported": ["d.1"],
            }
        ],
        "sourceSystems": [{"vendor": "V", "product": "P", "category": "C"}],
        "connectors": [{"type": "REST", "protocol": "HTTPS", "auth": "OAuth"}],
        "ingestionChallenges": ["c1"],
        "integrationChallenges": ["c2"],
    }


def test_subdomain_validates_known_good_yaml():
    sd = Subdomain.model_validate(_good_subdomain_dict())
    assert sd.id == "test_sub"
    assert len(sd.personas) == 1
    assert sd.kpis[0].decisionsSupported == ["d.1"]


def test_subdomain_rejects_missing_personas():
    raw = _good_subdomain_dict()
    raw["personas"] = []
    with pytest.raises(ValidationError):
        Subdomain.model_validate(raw)


def test_subdomain_rejects_unknown_vertical():
    raw = _good_subdomain_dict()
    raw["vertical"] = "Bogus"
    with pytest.raises(ValidationError):
        Subdomain.model_validate(raw)


def test_subdomain_rejects_extra_top_level_field():
    raw = _good_subdomain_dict()
    raw["mystery"] = 1
    with pytest.raises(ValidationError):
        Subdomain.model_validate(raw)


def test_dataModel_default_when_omitted():
    raw = _good_subdomain_dict()
    raw.pop("connectors")
    sd = Subdomain.model_validate(raw)
    assert sd.connectors == []


# --------------------------------------------------------------------------- #
# Whole registry                                                              #
# --------------------------------------------------------------------------- #


@pytest.mark.skipif(not DATA_ROOT.exists(), reason="needs data/ checked out")
def test_load_registry_reads_full_data_dir():
    reg = load_registry(DATA_ROOT)
    # The repo has 100+ subdomains seeded; assert a healthy lower bound rather
    # than an exact count so the test stays useful as the registry grows.
    assert len(reg.subdomains) >= 80
    assert len(reg.kpis) >= 20
    assert len(reg.source_systems) >= 20
    assert len(reg.connectors) >= 10


@pytest.mark.skipif(not DATA_ROOT.exists(), reason="needs data/ checked out")
def test_every_subdomain_has_at_least_one_persona():
    reg = load_registry(DATA_ROOT)
    for sd in reg.subdomains:
        assert len(sd.personas) >= 1, f"{sd.id} has no personas"


@pytest.mark.skipif(not DATA_ROOT.exists(), reason="needs data/ checked out")
def test_kpi_decisionsSupported_reference_local_decisions():
    """Every KPI's decisionsSupported should match a decision in the same subdomain."""
    reg = load_registry(DATA_ROOT)
    bad: list[str] = []
    for sd in reg.subdomains:
        local_dec_ids = {d.id for d in sd.decisions}
        for k in sd.kpis:
            for d in k.decisionsSupported:
                if d not in local_dec_ids:
                    bad.append(f"{sd.id}::{k.id}->{d}")
    # We allow up to 5% of KPIs to dangle (data-quality canary).
    total = sum(len(s.kpis) for s in reg.subdomains) or 1
    assert len(bad) <= total * 0.05, f"too many dangling decision refs: {bad[:8]}"


def test_load_registry_handles_missing_subdir(tmp_path: Path):
    (tmp_path / "taxonomy").mkdir()
    # Write one valid subdomain so registry is non-empty.
    (tmp_path / "taxonomy" / "x.yaml").write_text(
        yaml.safe_dump(_good_subdomain_dict()), encoding="utf-8"
    )
    reg = load_registry(tmp_path)
    assert len(reg.subdomains) == 1
    assert reg.kpis == []
    assert reg.source_systems == []
    assert reg.connectors == []
