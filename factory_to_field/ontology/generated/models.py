from __future__ import annotations

import re
import sys
from datetime import (
    date,
    datetime,
    time
)
from decimal import Decimal
from enum import Enum
from typing import (
    Any,
    ClassVar,
    Literal,
    Optional,
    Union
)

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    RootModel,
    SerializationInfo,
    SerializerFunctionWrapHandler,
    field_validator,
    model_serializer
)


metamodel_version = "1.12.0"
version = "0.1.0"


class ConfiguredBaseModel(BaseModel):
    model_config = ConfigDict(
        serialize_by_alias = True,
        validate_by_name = True,
        validate_assignment = True,
        validate_default = True,
        extra = "forbid",
        arbitrary_types_allowed = True,
        use_enum_values = True,
        strict = False,
    )





class LinkMLMeta(RootModel):
    root: dict[str, Any] = {}
    model_config = ConfigDict(frozen=True)

    def __getattr__(self, key:str):
        return getattr(self.root, key)

    def __getitem__(self, key:str):
        return self.root[key]

    def __setitem__(self, key:str, value):
        self.root[key] = value

    def __contains__(self, key:str) -> bool:
        return key in self.root


linkml_meta = LinkMLMeta({'default_prefix': 'ftf',
     'default_range': 'string',
     'description': 'Umbrella schema. Import this one to get every module.',
     'id': 'https://domain-explorer.dev/ftf',
     'imports': ['linkml:types', 'core', 'refinery', 'oilfield', 'factory', 'kpi'],
     'name': 'ftf',
     'prefixes': {'ftf': {'prefix_prefix': 'ftf',
                          'prefix_reference': 'https://domain-explorer.dev/ftf#'},
                  'linkml': {'prefix_prefix': 'linkml',
                             'prefix_reference': 'https://w3id.org/linkml/'}},
     'source_file': 'ftf.yaml',
     'title': 'Factory to Field ontology v0.1'} )

class World(str, Enum):
    """
    Which of the three data worlds a record comes from (OT / IT / ET).
    """
    OT = "OT"
    """
    Operational technology: control systems, historians, SCADA, MES, test benches
    """
    IT = "IT"
    """
    Information technology: ERP, CMMS/EAM, QMS, supply chain
    """
    ET = "ET"
    """
    Engineering technology: P&IDs, datasheets, completion schematics, PLM
    """


class FailureMode(str, Enum):
    """
    Failure modes after ISO 14224 (codes as used in the Annex B equipment tables).
    """
    VIB = "VIB"
    """
    Vibration
    """
    ELP = "ELP"
    """
    External leakage, process medium
    """
    ELU = "ELU"
    """
    External leakage, utility medium
    """
    OHE = "OHE"
    """
    Overheating
    """
    BRD = "BRD"
    """
    Breakdown
    """
    FTS = "FTS"
    """
    Fail to start on demand
    """
    STP = "STP"
    """
    Unexpected shutdown
    """
    NOI = "NOI"
    """
    Noise
    """
    PDE = "PDE"
    """
    Parameter deviation
    """
    INL = "INL"
    """
    Internal leakage
    """
    ERO = "ERO"
    """
    Erratic output
    """
    SER = "SER"
    """
    Minor in-service problems
    """


class Severity(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"


class DraftStatus(str, Enum):
    pending = "pending"
    """
    Written by an agent, waiting for a named human
    """
    approved = "approved"
    """
    Approved by a named person with the right role
    """
    rejected = "rejected"
    """
    Rejected by a named person
    """


class LinkMethod(str, Enum):
    """
    How an identity link between two source records was established.
    """
    exact_key = "exact_key"
    """
    Identical normalised key (serial, lot, document number)
    """
    tag_rule = "tag_rule"
    """
    Tag grammar rule (e.g. 10P101A.* → P-101A)
    """
    alias_table = "alias_table"
    """
    Governed alias or rename table
    """
    fuzzy = "fuzzy"
    """
    String similarity above the auto-accept threshold
    """
    human = "human"
    """
    Confirmed in the review queue
    """


class ESPComponentKind(str, Enum):
    pump = "pump"
    intake = "intake"
    seal_section = "seal_section"
    motor = "motor"
    cable = "cable"
    sensor = "sensor"


class EndState(str, Enum):
    """
    How a run of a string ended.
    """
    failed = "failed"
    running = "running"
    """
    Still in the well; the run life is censored
    """
    pulled_for_other = "pulled_for_other"
    """
    Pulled for a reason unrelated to the string
    """



class Entity(ConfiguredBaseModel):
    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta({'abstract': True, 'from_schema': 'https://domain-explorer.dev/ftf/core'})

    id: str = Field(default=..., description="""Stable graph identifier (a CURIE-like local name)""", json_schema_extra = { "linkml_meta": {'domain_of': ['Entity']} })
    label: Optional[str] = Field(default=None, description="""Human-readable label""", json_schema_extra = { "linkml_meta": {'domain_of': ['Entity']} })
    identifiers: Optional[list[SourceIdentifier]] = Field(default=None, description="""The names this thing has in each source system (the crosswalk).""", json_schema_extra = { "linkml_meta": {'domain_of': ['Entity']} })


class SourceIdentifier(ConfiguredBaseModel):
    """
    One name for one thing in one system.
    """
    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta({'from_schema': 'https://domain-explorer.dev/ftf/core'})

    system: str = Field(default=..., description="""Source system, e.g. SAP-PM, PI, P&ID, MES, PLM""", json_schema_extra = { "linkml_meta": {'domain_of': ['SourceIdentifier']} })
    world: World = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['SourceIdentifier']} })
    kind: Optional[str] = Field(default=None, description="""What the key is: tag, serial, floc, equipment_no, document ...""", json_schema_extra = { "linkml_meta": {'domain_of': ['SourceIdentifier', 'ESPComponent']} })
    value: str = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['SourceIdentifier', 'TestRecord']} })


class Organization(Entity):
    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta({'from_schema': 'https://domain-explorer.dev/ftf/core'})

    org_kind: Optional[str] = Field(default=None, description="""operator | oem | supplier | contractor""", json_schema_extra = { "linkml_meta": {'domain_of': ['Organization']} })
    id: str = Field(default=..., description="""Stable graph identifier (a CURIE-like local name)""", json_schema_extra = { "linkml_meta": {'domain_of': ['Entity']} })
    label: Optional[str] = Field(default=None, description="""Human-readable label""", json_schema_extra = { "linkml_meta": {'domain_of': ['Entity']} })
    identifiers: Optional[list[SourceIdentifier]] = Field(default=None, description="""The names this thing has in each source system (the crosswalk).""", json_schema_extra = { "linkml_meta": {'domain_of': ['Entity']} })


class Site(Entity):
    """
    A refinery, a field, or a factory.
    """
    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta({'from_schema': 'https://domain-explorer.dev/ftf/core'})

    site_kind: Optional[str] = Field(default=None, description="""refinery | field | factory""", json_schema_extra = { "linkml_meta": {'domain_of': ['Site']} })
    operated_by: Optional[str] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['Site']} })
    time_zone: Optional[str] = Field(default=None, description="""IANA zone the local records are written in""", json_schema_extra = { "linkml_meta": {'domain_of': ['Site']} })
    id: str = Field(default=..., description="""Stable graph identifier (a CURIE-like local name)""", json_schema_extra = { "linkml_meta": {'domain_of': ['Entity']} })
    label: Optional[str] = Field(default=None, description="""Human-readable label""", json_schema_extra = { "linkml_meta": {'domain_of': ['Entity']} })
    identifiers: Optional[list[SourceIdentifier]] = Field(default=None, description="""The names this thing has in each source system (the crosswalk).""", json_schema_extra = { "linkml_meta": {'domain_of': ['Entity']} })


class FunctionalLocation(Entity):
    """
    A POSITION. Where equipment is needed; defined by the engineering design and survives swaps.
    """
    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta({'from_schema': 'https://domain-explorer.dev/ftf/core'})

    site: Optional[str] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['FunctionalLocation']} })
    parent: Optional[str] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['FunctionalLocation']} })
    function: Optional[str] = Field(default=None, description="""What the position does, e.g. crude charge pump""", json_schema_extra = { "linkml_meta": {'domain_of': ['FunctionalLocation']} })
    design_datasheet: Optional[str] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['FunctionalLocation']} })
    installed_spare_of: Optional[str] = Field(default=None, description="""This position is the installed spare of another""", json_schema_extra = { "linkml_meta": {'domain_of': ['FunctionalLocation']} })
    id: str = Field(default=..., description="""Stable graph identifier (a CURIE-like local name)""", json_schema_extra = { "linkml_meta": {'domain_of': ['Entity']} })
    label: Optional[str] = Field(default=None, description="""Human-readable label""", json_schema_extra = { "linkml_meta": {'domain_of': ['Entity']} })
    identifiers: Optional[list[SourceIdentifier]] = Field(default=None, description="""The names this thing has in each source system (the crosswalk).""", json_schema_extra = { "linkml_meta": {'domain_of': ['Entity']} })


class PhysicalEquipment(Entity):
    """
    A UNIT. A serial-numbered thing that can be built, installed, moved, repaired and scrapped.
    """
    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta({'from_schema': 'https://domain-explorer.dev/ftf/core'})

    serial: str = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['PhysicalEquipment']} })
    model: Optional[str] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['PhysicalEquipment']} })
    manufacturer: Optional[str] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['PhysicalEquipment']} })
    built_on: Optional[date] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['PhysicalEquipment', 'BuildRecord']} })
    parent_unit: Optional[str] = Field(default=None, description="""Set when this is a component of another unit""", json_schema_extra = { "linkml_meta": {'domain_of': ['PhysicalEquipment']} })
    build_lots: Optional[list[str]] = Field(default=None, description="""Material lots built into this unit (maker genealogy)""", json_schema_extra = { "linkml_meta": {'domain_of': ['PhysicalEquipment']} })
    id: str = Field(default=..., description="""Stable graph identifier (a CURIE-like local name)""", json_schema_extra = { "linkml_meta": {'domain_of': ['Entity']} })
    label: Optional[str] = Field(default=None, description="""Human-readable label""", json_schema_extra = { "linkml_meta": {'domain_of': ['Entity']} })
    identifiers: Optional[list[SourceIdentifier]] = Field(default=None, description="""The names this thing has in each source system (the crosswalk).""", json_schema_extra = { "linkml_meta": {'domain_of': ['Entity']} })


class Installation(Entity):
    """
    A unit at a position over a period. The only place unit and position meet.
    """
    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta({'from_schema': 'https://domain-explorer.dev/ftf/core'})

    from_date: Optional[date] = Field(default=None, description="""Start of validity (inclusive)""", json_schema_extra = { "linkml_meta": {'domain_of': ['Installation']} })
    to_date: Optional[date] = Field(default=None, description="""End of validity (exclusive); empty means still current""", json_schema_extra = { "linkml_meta": {'domain_of': ['Installation']} })
    position: str = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['Installation']} })
    unit: str = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['Installation', 'BuildRecord', 'TestRecord', 'Shipment']} })
    id: str = Field(default=..., description="""Stable graph identifier (a CURIE-like local name)""", json_schema_extra = { "linkml_meta": {'domain_of': ['Entity']} })
    label: Optional[str] = Field(default=None, description="""Human-readable label""", json_schema_extra = { "linkml_meta": {'domain_of': ['Entity']} })
    identifiers: Optional[list[SourceIdentifier]] = Field(default=None, description="""The names this thing has in each source system (the crosswalk).""", json_schema_extra = { "linkml_meta": {'domain_of': ['Entity']} })


class Signal(Entity):
    """
    A measured or computed time series (historian tag, SCADA point).
    """
    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta({'from_schema': 'https://domain-explorer.dev/ftf/core'})

    measures_position: Optional[list[str]] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['Signal']} })
    quantity: Optional[str] = Field(default=None, description="""vibration_velocity | motor_temperature | intake_pressure ...""", json_schema_extra = { "linkml_meta": {'domain_of': ['Signal']} })
    engineering_unit: Optional[str] = Field(default=None, description="""mm/s | degC | bar ...""", json_schema_extra = { "linkml_meta": {'domain_of': ['Signal', 'TestRecord']} })
    alarm_high: Optional[float] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['Signal']} })
    sample_seconds: Optional[int] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['Signal']} })
    id: str = Field(default=..., description="""Stable graph identifier (a CURIE-like local name)""", json_schema_extra = { "linkml_meta": {'domain_of': ['Entity']} })
    label: Optional[str] = Field(default=None, description="""Human-readable label""", json_schema_extra = { "linkml_meta": {'domain_of': ['Entity']} })
    identifiers: Optional[list[SourceIdentifier]] = Field(default=None, description="""The names this thing has in each source system (the crosswalk).""", json_schema_extra = { "linkml_meta": {'domain_of': ['Entity']} })


class Document(Entity):
    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta({'from_schema': 'https://domain-explorer.dev/ftf/core'})

    doc_kind: Optional[str] = Field(default=None, description="""P&ID | datasheet | completion schematic | procedure""", json_schema_extra = { "linkml_meta": {'domain_of': ['Document']} })
    revision: Optional[str] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['Document']} })
    depicts: Optional[list[str]] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['Document']} })
    about_unit: Optional[list[str]] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['Document', 'Notification']} })
    summary: Optional[str] = Field(default=None, description="""Findings or abstract, as written""", json_schema_extra = { "linkml_meta": {'domain_of': ['Document']} })
    issued_on: Optional[date] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['Document']} })
    id: str = Field(default=..., description="""Stable graph identifier (a CURIE-like local name)""", json_schema_extra = { "linkml_meta": {'domain_of': ['Entity']} })
    label: Optional[str] = Field(default=None, description="""Human-readable label""", json_schema_extra = { "linkml_meta": {'domain_of': ['Entity']} })
    identifiers: Optional[list[SourceIdentifier]] = Field(default=None, description="""The names this thing has in each source system (the crosswalk).""", json_schema_extra = { "linkml_meta": {'domain_of': ['Entity']} })


class Event(Entity):
    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta({'abstract': True, 'from_schema': 'https://domain-explorer.dev/ftf/core'})

    occurred_on: date = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['Event']} })
    id: str = Field(default=..., description="""Stable graph identifier (a CURIE-like local name)""", json_schema_extra = { "linkml_meta": {'domain_of': ['Entity']} })
    label: Optional[str] = Field(default=None, description="""Human-readable label""", json_schema_extra = { "linkml_meta": {'domain_of': ['Entity']} })
    identifiers: Optional[list[SourceIdentifier]] = Field(default=None, description="""The names this thing has in each source system (the crosswalk).""", json_schema_extra = { "linkml_meta": {'domain_of': ['Entity']} })


class FailureEvent(Event):
    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta({'from_schema': 'https://domain-explorer.dev/ftf/core'})

    mode: FailureMode = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['FailureEvent']} })
    of_unit: str = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['FailureEvent']} })
    at_position: str = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['FailureEvent', 'Workover']} })
    installation: Optional[str] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['FailureEvent', 'RunRecord']} })
    description: Optional[str] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['FailureEvent', 'NonConformance']} })
    occurred_on: date = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['Event']} })
    id: str = Field(default=..., description="""Stable graph identifier (a CURIE-like local name)""", json_schema_extra = { "linkml_meta": {'domain_of': ['Entity']} })
    label: Optional[str] = Field(default=None, description="""Human-readable label""", json_schema_extra = { "linkml_meta": {'domain_of': ['Entity']} })
    identifiers: Optional[list[SourceIdentifier]] = Field(default=None, description="""The names this thing has in each source system (the crosswalk).""", json_schema_extra = { "linkml_meta": {'domain_of': ['Entity']} })


class Notification(Event):
    """
    A maintenance notification or malfunction report.
    """
    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta({'from_schema': 'https://domain-explorer.dev/ftf/core'})

    about_position: Optional[str] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['Notification']} })
    about_unit: Optional[str] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['Document', 'Notification']} })
    text: Optional[str] = Field(default=None, description="""Free text as typed; treat as untrusted data""", json_schema_extra = { "linkml_meta": {'domain_of': ['Notification']} })
    occurred_on: date = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['Event']} })
    id: str = Field(default=..., description="""Stable graph identifier (a CURIE-like local name)""", json_schema_extra = { "linkml_meta": {'domain_of': ['Entity']} })
    label: Optional[str] = Field(default=None, description="""Human-readable label""", json_schema_extra = { "linkml_meta": {'domain_of': ['Entity']} })
    identifiers: Optional[list[SourceIdentifier]] = Field(default=None, description="""The names this thing has in each source system (the crosswalk).""", json_schema_extra = { "linkml_meta": {'domain_of': ['Entity']} })


class MaterialLot(Entity):
    """
    A homogeneous batch of a purchased material (bearing set, elastomer compound).
    """
    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta({'from_schema': 'https://domain-explorer.dev/ftf/core'})

    material: Optional[str] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['MaterialLot']} })
    supplier: Optional[str] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['MaterialLot']} })
    introduced_by: Optional[str] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['MaterialLot']} })
    id: str = Field(default=..., description="""Stable graph identifier (a CURIE-like local name)""", json_schema_extra = { "linkml_meta": {'domain_of': ['Entity']} })
    label: Optional[str] = Field(default=None, description="""Human-readable label""", json_schema_extra = { "linkml_meta": {'domain_of': ['Entity']} })
    identifiers: Optional[list[SourceIdentifier]] = Field(default=None, description="""The names this thing has in each source system (the crosswalk).""", json_schema_extra = { "linkml_meta": {'domain_of': ['Entity']} })


class EngineeringChange(Entity):
    """
    An ECO. The route says how it was approved.
    """
    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta({'from_schema': 'https://domain-explorer.dev/ftf/core'})

    approved_on: Optional[date] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['EngineeringChange', 'ManagementOfChange']} })
    route: Optional[str] = Field(default=None, description="""standard | expedited""", json_schema_extra = { "linkml_meta": {'domain_of': ['EngineeringChange']} })
    qualification_test_waived: Optional[bool] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['EngineeringChange']} })
    change_summary: Optional[str] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['EngineeringChange']} })
    id: str = Field(default=..., description="""Stable graph identifier (a CURIE-like local name)""", json_schema_extra = { "linkml_meta": {'domain_of': ['Entity']} })
    label: Optional[str] = Field(default=None, description="""Human-readable label""", json_schema_extra = { "linkml_meta": {'domain_of': ['Entity']} })
    identifiers: Optional[list[SourceIdentifier]] = Field(default=None, description="""The names this thing has in each source system (the crosswalk).""", json_schema_extra = { "linkml_meta": {'domain_of': ['Entity']} })


class WarrantyClaim(Entity):
    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta({'from_schema': 'https://domain-explorer.dev/ftf/core'})

    raised_by: Optional[str] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['WarrantyClaim']} })
    covers_units: Optional[list[str]] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['WarrantyClaim']} })
    opened_on: Optional[date] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['WarrantyClaim', 'NonConformance']} })
    id: str = Field(default=..., description="""Stable graph identifier (a CURIE-like local name)""", json_schema_extra = { "linkml_meta": {'domain_of': ['Entity']} })
    label: Optional[str] = Field(default=None, description="""Human-readable label""", json_schema_extra = { "linkml_meta": {'domain_of': ['Entity']} })
    identifiers: Optional[list[SourceIdentifier]] = Field(default=None, description="""The names this thing has in each source system (the crosswalk).""", json_schema_extra = { "linkml_meta": {'domain_of': ['Entity']} })


class Case(Entity):
    """
    An investigation opened by an alarm or a question. Holds findings and drafts.
    """
    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta({'from_schema': 'https://domain-explorer.dev/ftf/core'})

    trigger: Optional[str] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['Case']} })
    opened_at: Optional[datetime ] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['Case']} })
    severity: Optional[Severity] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['Case']} })
    id: str = Field(default=..., description="""Stable graph identifier (a CURIE-like local name)""", json_schema_extra = { "linkml_meta": {'domain_of': ['Entity']} })
    label: Optional[str] = Field(default=None, description="""Human-readable label""", json_schema_extra = { "linkml_meta": {'domain_of': ['Entity']} })
    identifiers: Optional[list[SourceIdentifier]] = Field(default=None, description="""The names this thing has in each source system (the crosswalk).""", json_schema_extra = { "linkml_meta": {'domain_of': ['Entity']} })


class Draft(Entity):
    """
    A proposed write to a system of record. Never applied without a named approver.
    """
    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta({'from_schema': 'https://domain-explorer.dev/ftf/core'})

    target_system: Optional[str] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['Draft']} })
    status: DraftStatus = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['Draft']} })
    required_role: Optional[str] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['Draft']} })
    approved_by: Optional[str] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['Draft']} })
    case: Optional[str] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['Draft']} })
    id: str = Field(default=..., description="""Stable graph identifier (a CURIE-like local name)""", json_schema_extra = { "linkml_meta": {'domain_of': ['Entity']} })
    label: Optional[str] = Field(default=None, description="""Human-readable label""", json_schema_extra = { "linkml_meta": {'domain_of': ['Entity']} })
    identifiers: Optional[list[SourceIdentifier]] = Field(default=None, description="""The names this thing has in each source system (the crosswalk).""", json_schema_extra = { "linkml_meta": {'domain_of': ['Entity']} })


class LinkAssertion(ConfiguredBaseModel):
    """
    Provenance of one identity or relationship link between source records.
    """
    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta({'from_schema': 'https://domain-explorer.dev/ftf/core'})

    subject: str = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['LinkAssertion']} })
    predicate: str = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['LinkAssertion']} })
    object: str = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['LinkAssertion']} })
    method: LinkMethod = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['LinkAssertion', 'KpiDefinition']} })
    confidence: float = Field(default=..., ge=0, le=1, json_schema_extra = { "linkml_meta": {'domain_of': ['LinkAssertion']} })
    evidence: Optional[str] = Field(default=None, description="""Rule name or the record pair the link came from""", json_schema_extra = { "linkml_meta": {'domain_of': ['LinkAssertion']} })


class ProcessUnit(FunctionalLocation):
    """
    A process unit such as a crude distillation unit; positions hang under it.
    """
    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta({'from_schema': 'https://domain-explorer.dev/ftf/refinery'})

    capacity_bpd: Optional[int] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['ProcessUnit']} })
    site: Optional[str] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['FunctionalLocation']} })
    parent: Optional[str] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['FunctionalLocation']} })
    function: Optional[str] = Field(default=None, description="""What the position does, e.g. crude charge pump""", json_schema_extra = { "linkml_meta": {'domain_of': ['FunctionalLocation']} })
    design_datasheet: Optional[str] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['FunctionalLocation']} })
    installed_spare_of: Optional[str] = Field(default=None, description="""This position is the installed spare of another""", json_schema_extra = { "linkml_meta": {'domain_of': ['FunctionalLocation']} })
    id: str = Field(default=..., description="""Stable graph identifier (a CURIE-like local name)""", json_schema_extra = { "linkml_meta": {'domain_of': ['Entity']} })
    label: Optional[str] = Field(default=None, description="""Human-readable label""", json_schema_extra = { "linkml_meta": {'domain_of': ['Entity']} })
    identifiers: Optional[list[SourceIdentifier]] = Field(default=None, description="""The names this thing has in each source system (the crosswalk).""", json_schema_extra = { "linkml_meta": {'domain_of': ['Entity']} })


class PumpPosition(FunctionalLocation):
    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta({'from_schema': 'https://domain-explorer.dev/ftf/refinery'})

    service: Optional[str] = Field(default=None, description="""Pumped service""", json_schema_extra = { "linkml_meta": {'domain_of': ['PumpPosition']} })
    rated_flow_m3h: Optional[float] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['PumpPosition']} })
    api_type: Optional[str] = Field(default=None, description="""API 610 type, e.g. BB2""", json_schema_extra = { "linkml_meta": {'domain_of': ['PumpPosition']} })
    site: Optional[str] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['FunctionalLocation']} })
    parent: Optional[str] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['FunctionalLocation']} })
    function: Optional[str] = Field(default=None, description="""What the position does, e.g. crude charge pump""", json_schema_extra = { "linkml_meta": {'domain_of': ['FunctionalLocation']} })
    design_datasheet: Optional[str] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['FunctionalLocation']} })
    installed_spare_of: Optional[str] = Field(default=None, description="""This position is the installed spare of another""", json_schema_extra = { "linkml_meta": {'domain_of': ['FunctionalLocation']} })
    id: str = Field(default=..., description="""Stable graph identifier (a CURIE-like local name)""", json_schema_extra = { "linkml_meta": {'domain_of': ['Entity']} })
    label: Optional[str] = Field(default=None, description="""Human-readable label""", json_schema_extra = { "linkml_meta": {'domain_of': ['Entity']} })
    identifiers: Optional[list[SourceIdentifier]] = Field(default=None, description="""The names this thing has in each source system (the crosswalk).""", json_schema_extra = { "linkml_meta": {'domain_of': ['Entity']} })


class Stream(Entity):
    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta({'from_schema': 'https://domain-explorer.dev/ftf/refinery'})

    from_position: Optional[str] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['Stream']} })
    to_position: Optional[str] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['Stream']} })
    medium: Optional[str] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['Stream']} })
    id: str = Field(default=..., description="""Stable graph identifier (a CURIE-like local name)""", json_schema_extra = { "linkml_meta": {'domain_of': ['Entity']} })
    label: Optional[str] = Field(default=None, description="""Human-readable label""", json_schema_extra = { "linkml_meta": {'domain_of': ['Entity']} })
    identifiers: Optional[list[SourceIdentifier]] = Field(default=None, description="""The names this thing has in each source system (the crosswalk).""", json_schema_extra = { "linkml_meta": {'domain_of': ['Entity']} })


class ManagementOfChange(Entity):
    """
    A plant change request; ties engineering changes to positions.
    """
    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta({'from_schema': 'https://domain-explorer.dev/ftf/refinery'})

    affects: Optional[list[str]] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['ManagementOfChange']} })
    approved_on: Optional[date] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['EngineeringChange', 'ManagementOfChange']} })
    id: str = Field(default=..., description="""Stable graph identifier (a CURIE-like local name)""", json_schema_extra = { "linkml_meta": {'domain_of': ['Entity']} })
    label: Optional[str] = Field(default=None, description="""Human-readable label""", json_schema_extra = { "linkml_meta": {'domain_of': ['Entity']} })
    identifiers: Optional[list[SourceIdentifier]] = Field(default=None, description="""The names this thing has in each source system (the crosswalk).""", json_schema_extra = { "linkml_meta": {'domain_of': ['Entity']} })


class OilField(Site):
    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta({'from_schema': 'https://domain-explorer.dev/ftf/oilfield'})

    site_kind: Optional[str] = Field(default=None, description="""refinery | field | factory""", json_schema_extra = { "linkml_meta": {'domain_of': ['Site']} })
    operated_by: Optional[str] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['Site']} })
    time_zone: Optional[str] = Field(default=None, description="""IANA zone the local records are written in""", json_schema_extra = { "linkml_meta": {'domain_of': ['Site']} })
    id: str = Field(default=..., description="""Stable graph identifier (a CURIE-like local name)""", json_schema_extra = { "linkml_meta": {'domain_of': ['Entity']} })
    label: Optional[str] = Field(default=None, description="""Human-readable label""", json_schema_extra = { "linkml_meta": {'domain_of': ['Entity']} })
    identifiers: Optional[list[SourceIdentifier]] = Field(default=None, description="""The names this thing has in each source system (the crosswalk).""", json_schema_extra = { "linkml_meta": {'domain_of': ['Entity']} })


class Well(FunctionalLocation):
    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta({'from_schema': 'https://domain-explorer.dev/ftf/oilfield'})

    pad: Optional[str] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['Well']} })
    lift_method: Optional[str] = Field(default=None, description="""esp | gas_lift | rod_pump""", json_schema_extra = { "linkml_meta": {'domain_of': ['Well']} })
    producing: Optional[bool] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['Well']} })
    site: Optional[str] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['FunctionalLocation']} })
    parent: Optional[str] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['FunctionalLocation']} })
    function: Optional[str] = Field(default=None, description="""What the position does, e.g. crude charge pump""", json_schema_extra = { "linkml_meta": {'domain_of': ['FunctionalLocation']} })
    design_datasheet: Optional[str] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['FunctionalLocation']} })
    installed_spare_of: Optional[str] = Field(default=None, description="""This position is the installed spare of another""", json_schema_extra = { "linkml_meta": {'domain_of': ['FunctionalLocation']} })
    id: str = Field(default=..., description="""Stable graph identifier (a CURIE-like local name)""", json_schema_extra = { "linkml_meta": {'domain_of': ['Entity']} })
    label: Optional[str] = Field(default=None, description="""Human-readable label""", json_schema_extra = { "linkml_meta": {'domain_of': ['Entity']} })
    identifiers: Optional[list[SourceIdentifier]] = Field(default=None, description="""The names this thing has in each source system (the crosswalk).""", json_schema_extra = { "linkml_meta": {'domain_of': ['Entity']} })


class ESPPosition(FunctionalLocation):
    """
    The artificial-lift position in a well (the ESP slot), under the Well.
    """
    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta({'from_schema': 'https://domain-explorer.dev/ftf/oilfield'})

    setting_depth_m: Optional[float] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['ESPPosition']} })
    site: Optional[str] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['FunctionalLocation']} })
    parent: Optional[str] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['FunctionalLocation']} })
    function: Optional[str] = Field(default=None, description="""What the position does, e.g. crude charge pump""", json_schema_extra = { "linkml_meta": {'domain_of': ['FunctionalLocation']} })
    design_datasheet: Optional[str] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['FunctionalLocation']} })
    installed_spare_of: Optional[str] = Field(default=None, description="""This position is the installed spare of another""", json_schema_extra = { "linkml_meta": {'domain_of': ['FunctionalLocation']} })
    id: str = Field(default=..., description="""Stable graph identifier (a CURIE-like local name)""", json_schema_extra = { "linkml_meta": {'domain_of': ['Entity']} })
    label: Optional[str] = Field(default=None, description="""Human-readable label""", json_schema_extra = { "linkml_meta": {'domain_of': ['Entity']} })
    identifiers: Optional[list[SourceIdentifier]] = Field(default=None, description="""The names this thing has in each source system (the crosswalk).""", json_schema_extra = { "linkml_meta": {'domain_of': ['Entity']} })


class ESPString(PhysicalEquipment):
    """
    A complete submersible pump string as run in a well.
    """
    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta({'from_schema': 'https://domain-explorer.dev/ftf/oilfield'})

    components: Optional[list[str]] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['ESPString']} })
    serial: str = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['PhysicalEquipment']} })
    model: Optional[str] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['PhysicalEquipment']} })
    manufacturer: Optional[str] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['PhysicalEquipment']} })
    built_on: Optional[date] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['PhysicalEquipment', 'BuildRecord']} })
    parent_unit: Optional[str] = Field(default=None, description="""Set when this is a component of another unit""", json_schema_extra = { "linkml_meta": {'domain_of': ['PhysicalEquipment']} })
    build_lots: Optional[list[str]] = Field(default=None, description="""Material lots built into this unit (maker genealogy)""", json_schema_extra = { "linkml_meta": {'domain_of': ['PhysicalEquipment']} })
    id: str = Field(default=..., description="""Stable graph identifier (a CURIE-like local name)""", json_schema_extra = { "linkml_meta": {'domain_of': ['Entity']} })
    label: Optional[str] = Field(default=None, description="""Human-readable label""", json_schema_extra = { "linkml_meta": {'domain_of': ['Entity']} })
    identifiers: Optional[list[SourceIdentifier]] = Field(default=None, description="""The names this thing has in each source system (the crosswalk).""", json_schema_extra = { "linkml_meta": {'domain_of': ['Entity']} })


class ESPComponent(PhysicalEquipment):
    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta({'from_schema': 'https://domain-explorer.dev/ftf/oilfield'})

    kind: ESPComponentKind = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['SourceIdentifier', 'ESPComponent']} })
    serial: str = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['PhysicalEquipment']} })
    model: Optional[str] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['PhysicalEquipment']} })
    manufacturer: Optional[str] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['PhysicalEquipment']} })
    built_on: Optional[date] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['PhysicalEquipment', 'BuildRecord']} })
    parent_unit: Optional[str] = Field(default=None, description="""Set when this is a component of another unit""", json_schema_extra = { "linkml_meta": {'domain_of': ['PhysicalEquipment']} })
    build_lots: Optional[list[str]] = Field(default=None, description="""Material lots built into this unit (maker genealogy)""", json_schema_extra = { "linkml_meta": {'domain_of': ['PhysicalEquipment']} })
    id: str = Field(default=..., description="""Stable graph identifier (a CURIE-like local name)""", json_schema_extra = { "linkml_meta": {'domain_of': ['Entity']} })
    label: Optional[str] = Field(default=None, description="""Human-readable label""", json_schema_extra = { "linkml_meta": {'domain_of': ['Entity']} })
    identifiers: Optional[list[SourceIdentifier]] = Field(default=None, description="""The names this thing has in each source system (the crosswalk).""", json_schema_extra = { "linkml_meta": {'domain_of': ['Entity']} })


class RunRecord(Entity):
    """
    One run of a string in a well. Run life belongs to the string, not to the well.
    """
    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta({'from_schema': 'https://domain-explorer.dev/ftf/oilfield'})

    installation: Optional[str] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['FailureEvent', 'RunRecord']} })
    start: Optional[date] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['RunRecord']} })
    end: Optional[date] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['RunRecord']} })
    end_state: EndState = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['RunRecord']} })
    run_days: Optional[int] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['RunRecord']} })
    id: str = Field(default=..., description="""Stable graph identifier (a CURIE-like local name)""", json_schema_extra = { "linkml_meta": {'domain_of': ['Entity']} })
    label: Optional[str] = Field(default=None, description="""Human-readable label""", json_schema_extra = { "linkml_meta": {'domain_of': ['Entity']} })
    identifiers: Optional[list[SourceIdentifier]] = Field(default=None, description="""The names this thing has in each source system (the crosswalk).""", json_schema_extra = { "linkml_meta": {'domain_of': ['Entity']} })


class Workover(Event):
    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta({'from_schema': 'https://domain-explorer.dev/ftf/oilfield'})

    rig: Optional[str] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['Workover']} })
    pulled_unit: Optional[str] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['Workover']} })
    set_unit: Optional[str] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['Workover']} })
    at_position: Optional[str] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['FailureEvent', 'Workover']} })
    occurred_on: date = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['Event']} })
    id: str = Field(default=..., description="""Stable graph identifier (a CURIE-like local name)""", json_schema_extra = { "linkml_meta": {'domain_of': ['Entity']} })
    label: Optional[str] = Field(default=None, description="""Human-readable label""", json_schema_extra = { "linkml_meta": {'domain_of': ['Entity']} })
    identifiers: Optional[list[SourceIdentifier]] = Field(default=None, description="""The names this thing has in each source system (the crosswalk).""", json_schema_extra = { "linkml_meta": {'domain_of': ['Entity']} })


class Deferment(ConfiguredBaseModel):
    """
    Production lost or at risk while a well runs degraded or is down.
    """
    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta({'from_schema': 'https://domain-explorer.dev/ftf/oilfield'})

    well: Optional[str] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['Deferment']} })
    barrels_per_day: Optional[float] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['Deferment']} })
    reason: Optional[str] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['Deferment']} })


class BuildRecord(Entity):
    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta({'from_schema': 'https://domain-explorer.dev/ftf/factory'})

    unit: str = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['Installation', 'BuildRecord', 'TestRecord', 'Shipment']} })
    built_on: Optional[date] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['PhysicalEquipment', 'BuildRecord']} })
    work_order: Optional[str] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['BuildRecord']} })
    lots: Optional[list[str]] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['BuildRecord', 'NonConformance']} })
    id: str = Field(default=..., description="""Stable graph identifier (a CURIE-like local name)""", json_schema_extra = { "linkml_meta": {'domain_of': ['Entity']} })
    label: Optional[str] = Field(default=None, description="""Human-readable label""", json_schema_extra = { "linkml_meta": {'domain_of': ['Entity']} })
    identifiers: Optional[list[SourceIdentifier]] = Field(default=None, description="""The names this thing has in each source system (the crosswalk).""", json_schema_extra = { "linkml_meta": {'domain_of': ['Entity']} })


class TestRecord(Entity):
    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta({'from_schema': 'https://domain-explorer.dev/ftf/factory'})

    unit: Optional[str] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['Installation', 'BuildRecord', 'TestRecord', 'Shipment']} })
    test_kind: Optional[str] = Field(default=None, description="""performance | leak | press_fit_force""", json_schema_extra = { "linkml_meta": {'domain_of': ['TestRecord']} })
    passed: Optional[bool] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['TestRecord']} })
    value: Optional[float] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['SourceIdentifier', 'TestRecord']} })
    engineering_unit: Optional[str] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['Signal', 'TestRecord']} })
    id: str = Field(default=..., description="""Stable graph identifier (a CURIE-like local name)""", json_schema_extra = { "linkml_meta": {'domain_of': ['Entity']} })
    label: Optional[str] = Field(default=None, description="""Human-readable label""", json_schema_extra = { "linkml_meta": {'domain_of': ['Entity']} })
    identifiers: Optional[list[SourceIdentifier]] = Field(default=None, description="""The names this thing has in each source system (the crosswalk).""", json_schema_extra = { "linkml_meta": {'domain_of': ['Entity']} })


class Shipment(Entity):
    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta({'from_schema': 'https://domain-explorer.dev/ftf/factory'})

    unit: Optional[str] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['Installation', 'BuildRecord', 'TestRecord', 'Shipment']} })
    customer: Optional[str] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['Shipment']} })
    shipped_on: Optional[date] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['Shipment']} })
    id: str = Field(default=..., description="""Stable graph identifier (a CURIE-like local name)""", json_schema_extra = { "linkml_meta": {'domain_of': ['Entity']} })
    label: Optional[str] = Field(default=None, description="""Human-readable label""", json_schema_extra = { "linkml_meta": {'domain_of': ['Entity']} })
    identifiers: Optional[list[SourceIdentifier]] = Field(default=None, description="""The names this thing has in each source system (the crosswalk).""", json_schema_extra = { "linkml_meta": {'domain_of': ['Entity']} })


class NonConformance(Entity):
    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta({'from_schema': 'https://domain-explorer.dev/ftf/factory'})

    lots: Optional[list[str]] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['BuildRecord', 'NonConformance']} })
    opened_on: Optional[date] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['WarrantyClaim', 'NonConformance']} })
    description: Optional[str] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['FailureEvent', 'NonConformance']} })
    id: str = Field(default=..., description="""Stable graph identifier (a CURIE-like local name)""", json_schema_extra = { "linkml_meta": {'domain_of': ['Entity']} })
    label: Optional[str] = Field(default=None, description="""Human-readable label""", json_schema_extra = { "linkml_meta": {'domain_of': ['Entity']} })
    identifiers: Optional[list[SourceIdentifier]] = Field(default=None, description="""The names this thing has in each source system (the crosswalk).""", json_schema_extra = { "linkml_meta": {'domain_of': ['Entity']} })


class EightD(Entity):
    """
    Corrective-action report (8D). Always created as a draft by agents.
    """
    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta({'from_schema': 'https://domain-explorer.dev/ftf/factory'})

    covers_claims: Optional[list[str]] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['EightD']} })
    root_cause: Optional[str] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['EightD']} })
    containment_units: Optional[list[str]] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['EightD']} })
    id: str = Field(default=..., description="""Stable graph identifier (a CURIE-like local name)""", json_schema_extra = { "linkml_meta": {'domain_of': ['Entity']} })
    label: Optional[str] = Field(default=None, description="""Human-readable label""", json_schema_extra = { "linkml_meta": {'domain_of': ['Entity']} })
    identifiers: Optional[list[SourceIdentifier]] = Field(default=None, description="""The names this thing has in each source system (the crosswalk).""", json_schema_extra = { "linkml_meta": {'domain_of': ['Entity']} })


class KpiDefinition(Entity):
    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta({'from_schema': 'https://domain-explorer.dev/ftf/kpi'})

    question: Optional[str] = Field(default=None, description="""The decision the KPI supports""", json_schema_extra = { "linkml_meta": {'domain_of': ['KpiDefinition']} })
    grain: Optional[str] = Field(default=None, description="""unit | position | fleet | lot""", json_schema_extra = { "linkml_meta": {'domain_of': ['KpiDefinition']} })
    method: Optional[str] = Field(default=None, description="""How it is computed, in one sentence""", json_schema_extra = { "linkml_meta": {'domain_of': ['LinkAssertion', 'KpiDefinition']} })
    standard: Optional[str] = Field(default=None, description="""Standard it follows, if any""", json_schema_extra = { "linkml_meta": {'domain_of': ['KpiDefinition']} })
    query: Optional[str] = Field(default=None, description="""Name of the SPARQL file that computes it""", json_schema_extra = { "linkml_meta": {'domain_of': ['KpiDefinition']} })
    id: str = Field(default=..., description="""Stable graph identifier (a CURIE-like local name)""", json_schema_extra = { "linkml_meta": {'domain_of': ['Entity']} })
    label: Optional[str] = Field(default=None, description="""Human-readable label""", json_schema_extra = { "linkml_meta": {'domain_of': ['Entity']} })
    identifiers: Optional[list[SourceIdentifier]] = Field(default=None, description="""The names this thing has in each source system (the crosswalk).""", json_schema_extra = { "linkml_meta": {'domain_of': ['Entity']} })


# Model rebuild
# see https://pydantic-docs.helpmanual.io/usage/models/#rebuilding-a-model
Entity.model_rebuild()
SourceIdentifier.model_rebuild()
Organization.model_rebuild()
Site.model_rebuild()
FunctionalLocation.model_rebuild()
PhysicalEquipment.model_rebuild()
Installation.model_rebuild()
Signal.model_rebuild()
Document.model_rebuild()
Event.model_rebuild()
FailureEvent.model_rebuild()
Notification.model_rebuild()
MaterialLot.model_rebuild()
EngineeringChange.model_rebuild()
WarrantyClaim.model_rebuild()
Case.model_rebuild()
Draft.model_rebuild()
LinkAssertion.model_rebuild()
ProcessUnit.model_rebuild()
PumpPosition.model_rebuild()
Stream.model_rebuild()
ManagementOfChange.model_rebuild()
OilField.model_rebuild()
Well.model_rebuild()
ESPPosition.model_rebuild()
ESPString.model_rebuild()
ESPComponent.model_rebuild()
RunRecord.model_rebuild()
Workover.model_rebuild()
Deferment.model_rebuild()
BuildRecord.model_rebuild()
TestRecord.model_rebuild()
Shipment.model_rebuild()
NonConformance.model_rebuild()
EightD.model_rebuild()
KpiDefinition.model_rebuild()
