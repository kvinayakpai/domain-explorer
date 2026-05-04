"""YAML loader that builds a typed Registry from data/."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from .schema import (
    ConnectorPattern,
    KpiRegistryEntry,
    SourceSystemEntry,
    Subdomain,
)


def _read_yaml_dir(d: Path) -> list[Any]:
    if not d.exists():
        return []
    out: list[Any] = []
    for f in sorted(d.iterdir()):
        if f.suffix.lower() in {".yaml", ".yml"}:
            with f.open("r", encoding="utf-8") as fh:
                out.append(yaml.safe_load(fh))
    return out


@dataclass
class Registry:
    subdomains: list[Subdomain]
    kpis: list[KpiRegistryEntry]
    source_systems: list[SourceSystemEntry]
    connectors: list[ConnectorPattern]


def load_registry(data_root: Path | str = "data") -> Registry:
    root = Path(data_root)
    subdomains = [
        Subdomain.model_validate(raw) for raw in _read_yaml_dir(root / "taxonomy")
    ]
    kpis: list[KpiRegistryEntry] = []
    for raw in _read_yaml_dir(root / "kpis"):
        for k in (raw or {}).get("kpis", []):
            kpis.append(KpiRegistryEntry.model_validate(k))
    sources: list[SourceSystemEntry] = []
    for raw in _read_yaml_dir(root / "source-systems"):
        for s in (raw or {}).get("sources", []):
            sources.append(SourceSystemEntry.model_validate(s))
    connectors: list[ConnectorPattern] = []
    for raw in _read_yaml_dir(root / "connectors"):
        for c in (raw or {}).get("connectors", []):
            connectors.append(ConnectorPattern.model_validate(c))
    return Registry(
        subdomains=subdomains,
        kpis=kpis,
        source_systems=sources,
        connectors=connectors,
    )


def get_subdomain(registry: Registry, sub_id: str) -> Subdomain | None:
    return next((s for s in registry.subdomains if s.id == sub_id), None)


def get_kpi(registry: Registry, kpi_id: str) -> KpiRegistryEntry | None:
    return next((k for k in registry.kpis if k.id == kpi_id), None)


def get_source_system(registry: Registry, source_id: str) -> SourceSystemEntry | None:
    return next((s for s in registry.source_systems if s.id == source_id), None)
