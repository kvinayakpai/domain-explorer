"""Domain Explorer metadata package — Pydantic v2 schemas and loader."""
from .schema import (
    Connector,
    ConnectorPattern,
    DataModel,
    Decision,
    Entity,
    Kpi,
    KpiDirection,
    KpiRegistryEntry,
    Persona,
    SourceSystem,
    SourceSystemEntry,
    Subdomain,
    Vertical,
)
from .loader import Registry, get_kpi, get_source_system, get_subdomain, load_registry

__all__ = [
    "Connector",
    "ConnectorPattern",
    "DataModel",
    "Decision",
    "Entity",
    "Kpi",
    "KpiDirection",
    "KpiRegistryEntry",
    "Persona",
    "Registry",
    "SourceSystem",
    "SourceSystemEntry",
    "Subdomain",
    "Vertical",
    "get_kpi",
    "get_source_system",
    "get_subdomain",
    "load_registry",
]
