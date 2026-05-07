"""YAML loader that builds a typed Registry from data/."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from .schema import (
    ConnectorPattern,
    KpiMasterEntry,
    KpiRegistryEntry,
    KpiSqlSpec,
    SourceSystemEntry,
    Subdomain,
)


def _read_yaml_dir(d: Path, *, exclude: tuple[str, ...] = ()) -> list[Any]:
    if not d.exists():
        return []
    out: list[Any] = []
    for f in sorted(d.iterdir()):
        if f.suffix.lower() not in {".yaml", ".yml"}:
            continue
        if f.name in exclude:
            continue
        with f.open("r", encoding="utf-8") as fh:
            out.append(yaml.safe_load(fh))
    return out


def _read_yaml(file: Path) -> Any:
    if not file.exists():
        return None
    with file.open("r", encoding="utf-8") as fh:
        return yaml.safe_load(fh)


@dataclass
class Registry:
    subdomains: list[Subdomain]
    kpis: list[KpiRegistryEntry]
    source_systems: list[SourceSystemEntry]
    connectors: list[ConnectorPattern]
    kpi_master: list[KpiMasterEntry] = field(default_factory=list)
    kpi_sql: list[KpiSqlSpec] = field(default_factory=list)


def load_registry(data_root: Path | str = "data") -> Registry:
    root = Path(data_root)
    subdomains = [
        Subdomain.model_validate(raw) for raw in _read_yaml_dir(root / "taxonomy")
    ]
    kpis: list[KpiRegistryEntry] = []
    # Skip master.yaml + sql.yaml here; they're loaded via dedicated helpers
    # because they carry richer (forbidden-extra) fields.
    for raw in _read_yaml_dir(root / "kpis", exclude=("master.yaml", "sql.yaml")):
        for k in (raw or {}).get("kpis", []):
            try:
                kpis.append(KpiRegistryEntry.model_validate(k))
            except Exception:
                # Tolerate stray entries that don't fit the registry shape
                # (e.g. master entries without `vertical`).
                continue
    sources: list[SourceSystemEntry] = []
    for raw in _read_yaml_dir(root / "source-systems"):
        for s in (raw or {}).get("sources", []):
            sources.append(SourceSystemEntry.model_validate(s))
    connectors: list[ConnectorPattern] = []
    for raw in _read_yaml_dir(root / "connectors"):
        for c in (raw or {}).get("connectors", []):
            connectors.append(ConnectorPattern.model_validate(c))
    kpi_master = load_kpi_master(root)
    kpi_sql = load_kpi_sql(root)
    return Registry(
        subdomains=subdomains,
        kpis=kpis,
        source_systems=sources,
        connectors=connectors,
        kpi_master=kpi_master,
        kpi_sql=kpi_sql,
    )


def load_kpi_master(data_root: Path | str = "data") -> list[KpiMasterEntry]:
    """Load `data/kpis/master.yaml` if it exists, otherwise return []."""
    root = Path(data_root)
    raw = _read_yaml(root / "kpis" / "master.yaml")
    if not raw:
        return []
    return [KpiMasterEntry.model_validate(k) for k in (raw.get("kpis") or [])]


def load_kpi_sql(data_root: Path | str = "data") -> list[KpiSqlSpec]:
    """Load `data/kpis/sql.yaml` if it exists, otherwise return []."""
    root = Path(data_root)
    raw = _read_yaml(root / "kpis" / "sql.yaml")
    if not raw:
        return []
    return [KpiSqlSpec.model_validate(k) for k in (raw.get("kpis") or [])]


def get_subdomain(registry: Registry, sub_id: str) -> Subdomain | None:
    return next((s for s in registry.subdomains if s.id == sub_id), None)


def get_kpi(registry: Registry, kpi_id: str) -> KpiRegistryEntry | None:
    return next((k for k in registry.kpis if k.id == kpi_id), None)


def get_source_system(registry: Registry, source_id: str) -> SourceSystemEntry | None:
    return next((s for s in registry.source_systems if s.id == source_id), None)
