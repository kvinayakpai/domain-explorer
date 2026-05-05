"""Pydantic v2 schemas for the Domain Explorer metadata registry.

The shapes mirror packages/metadata/src/schema.ts (Zod) so the same YAML
files validate identically in both ecosystems.
"""
from enum import Enum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class Vertical(str, Enum):
    BFSI = "BFSI"
    INSURANCE = "Insurance"
    RETAIL = "Retail"
    RCG = "RCG"
    CPG = "CPG"
    TTH = "TTH"
    MANUFACTURING = "Manufacturing"
    LIFE_SCIENCES = "LifeSciences"
    HEALTHCARE = "Healthcare"
    TELECOM = "Telecom"
    MEDIA = "Media"
    ENERGY = "Energy"
    UTILITIES = "Utilities"
    PUBLIC_SECTOR = "PublicSector"
    HI_TECH = "HiTech"
    PROFESSIONAL_SERVICES = "ProfessionalServices"


KpiDirection = Literal["higher_is_better", "lower_is_better", "target_band"]
PersonaLevel = Literal["C-suite", "VP", "Director", "Manager", "IC"]
ConnectorLatency = Literal["realtime", "near-realtime", "batch"]
ConnectorMode = Literal["push", "pull", "stream", "file"]


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class Persona(_Strict):
    name: str = Field(..., min_length=1)
    title: str = Field(..., min_length=1)
    level: PersonaLevel


class Decision(_Strict):
    id: str = Field(..., min_length=1)
    statement: str = Field(..., min_length=1)


class Kpi(_Strict):
    id: str = Field(..., min_length=1)
    name: str = Field(..., min_length=1)
    formula: str = Field(..., min_length=1)
    unit: str = Field(..., min_length=1)
    direction: KpiDirection
    decisionsSupported: list[str] = Field(default_factory=list)


class Entity(_Strict):
    name: str = Field(..., min_length=1)
    description: str | None = None
    keys: list[str] = Field(default_factory=list)


class DataModel(_Strict):
    entities: list[Entity] = Field(default_factory=list)


class SourceSystem(_Strict):
    vendor: str = Field(..., min_length=1)
    product: str = Field(..., min_length=1)
    category: str = Field(..., min_length=1)


class Connector(_Strict):
    type: str = Field(..., min_length=1)
    protocol: str = Field(..., min_length=1)
    auth: str = Field(..., min_length=1)


class Subdomain(_Strict):
    id: str = Field(..., min_length=1)
    name: str = Field(..., min_length=1)
    vertical: Vertical
    oneLiner: str = Field(..., min_length=1)
    personas: list[Persona] = Field(..., min_length=1)
    decisions: list[Decision] = Field(default_factory=list)
    kpis: list[Kpi] = Field(default_factory=list)
    dataModel: DataModel = Field(default_factory=DataModel)
    sourceSystems: list[SourceSystem] = Field(default_factory=list)
    connectors: list[Connector] = Field(default_factory=list)
    ingestionChallenges: list[str] = Field(default_factory=list)
    integrationChallenges: list[str] = Field(default_factory=list)


class KpiRegistryEntry(Kpi):
    vertical: Vertical


class SourceSystemEntry(_Strict):
    id: str = Field(..., min_length=1)
    vendor: str = Field(..., min_length=1)
    product: str = Field(..., min_length=1)
    category: str = Field(..., min_length=1)
    primaryConnectors: list[str] = Field(default_factory=list)


class ConnectorPattern(_Strict):
    id: str = Field(..., min_length=1)
    type: str = Field(..., min_length=1)
    protocol: str = Field(..., min_length=1)
    auth: str = Field(..., min_length=1)
    typicalSources: list[str] = Field(default_factory=list)
    latency: ConnectorLatency
    modes: list[ConnectorMode] = Field(default_factory=list)
