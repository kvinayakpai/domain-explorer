export type EntityId = string;
export type OrganizationId = string;
export type SiteId = string;
export type FunctionalLocationId = string;
export type PhysicalEquipmentId = string;
export type InstallationId = string;
export type SignalId = string;
export type DocumentId = string;
export type EventId = string;
export type FailureEventId = string;
export type NotificationId = string;
export type MaterialLotId = string;
export type EngineeringChangeId = string;
export type WarrantyClaimId = string;
export type CaseId = string;
export type DraftId = string;
export type ProcessUnitId = string;
export type PumpPositionId = string;
export type StreamId = string;
export type ManagementOfChangeId = string;
export type OilFieldId = string;
export type WellId = string;
export type ESPPositionId = string;
export type ESPStringId = string;
export type ESPComponentId = string;
export type RunRecordId = string;
export type WorkoverId = string;
export type BuildRecordId = string;
export type TestRecordId = string;
export type ShipmentId = string;
export type NonConformanceId = string;
export type EightDId = string;
export type KpiDefinitionId = string;
/**
* Which of the three data worlds a record comes from (OT / IT / ET).
*/
export enum World {
    
    /** Operational technology: control systems, historians, SCADA, MES, test benches */
    OT = "OT",
    /** Information technology: ERP, CMMS/EAM, QMS, supply chain */
    IT = "IT",
    /** Engineering technology: P&IDs, datasheets, completion schematics, PLM */
    ET = "ET",
};
/**
* Failure modes after ISO 14224 (codes as used in the Annex B equipment tables).
*/
export enum FailureMode {
    
    /** Vibration */
    VIB = "VIB",
    /** External leakage, process medium */
    ELP = "ELP",
    /** External leakage, utility medium */
    ELU = "ELU",
    /** Overheating */
    OHE = "OHE",
    /** Breakdown */
    BRD = "BRD",
    /** Fail to start on demand */
    FTS = "FTS",
    /** Unexpected shutdown */
    STP = "STP",
    /** Noise */
    NOI = "NOI",
    /** Parameter deviation */
    PDE = "PDE",
    /** Internal leakage */
    INL = "INL",
    /** Erratic output */
    ERO = "ERO",
    /** Minor in-service problems */
    SER = "SER",
};

export enum Severity {
    
    low = "low",
    medium = "medium",
    high = "high",
    critical = "critical",
};

export enum DraftStatus {
    
    /** Written by an agent, waiting for a named human */
    pending = "pending",
    /** Approved by a named person with the right role */
    approved = "approved",
    /** Rejected by a named person */
    rejected = "rejected",
};
/**
* How an identity link between two source records was established.
*/
export enum LinkMethod {
    
    /** Identical normalised key (serial, lot, document number) */
    exact_key = "exact_key",
    /** Tag grammar rule (e.g. 10P101A.* → P-101A) */
    tag_rule = "tag_rule",
    /** Governed alias or rename table */
    alias_table = "alias_table",
    /** String similarity above the auto-accept threshold */
    fuzzy = "fuzzy",
    /** Confirmed in the review queue */
    human = "human",
};

export enum ESPComponentKind {
    
    pump = "pump",
    intake = "intake",
    seal_section = "seal_section",
    motor = "motor",
    cable = "cable",
    sensor = "sensor",
};
/**
* How a run of a string ended.
*/
export enum EndState {
    
    failed = "failed",
    /** Still in the well; the run life is censored */
    running = "running",
    /** Pulled for a reason unrelated to the string */
    pulled_for_other = "pulled_for_other",
};



export interface Entity {
    /** Stable graph identifier (a CURIE-like local name) */
    id: string,
    /** Human-readable label */
    label?: string,
    /** The names this thing has in each source system (the crosswalk). */
    identifiers?: SourceIdentifier[],
}


/**
 * One name for one thing in one system.
 */
export interface SourceIdentifier {
    /** Source system, e.g. SAP-PM, PI, P&ID, MES, PLM */
    system: string,
    world: string,
    /** What the key is: tag, serial, floc, equipment_no, document ... */
    kind?: string,
    value: string,
}



export interface Organization extends Entity {
    /** operator | oem | supplier | contractor */
    org_kind?: string,
}


/**
 * A refinery, a field, or a factory.
 */
export interface Site extends Entity {
    /** refinery | field | factory */
    site_kind?: string,
    operated_by?: OrganizationId,
    /** IANA zone the local records are written in */
    time_zone?: string,
}


/**
 * A POSITION. Where equipment is needed; defined by the engineering design and survives swaps.
 */
export interface FunctionalLocation extends Entity {
    site?: SiteId,
    parent?: FunctionalLocationId,
    /** What the position does, e.g. crude charge pump */
    function?: string,
    design_datasheet?: DocumentId,
    /** This position is the installed spare of another */
    installed_spare_of?: FunctionalLocationId,
}


/**
 * A UNIT. A serial-numbered thing that can be built, installed, moved, repaired and scrapped.
 */
export interface PhysicalEquipment extends Entity {
    serial: string,
    model?: string,
    manufacturer?: OrganizationId,
    built_on?: date,
    /** Set when this is a component of another unit */
    parent_unit?: PhysicalEquipmentId,
    /** Material lots built into this unit (maker genealogy) */
    build_lots?: MaterialLotId[],
}


/**
 * A unit at a position over a period. The only place unit and position meet.
 */
export interface Installation extends Entity {
    /** Start of validity (inclusive) */
    from_date?: date,
    /** End of validity (exclusive); empty means still current */
    to_date?: date,
    position: FunctionalLocationId,
    unit: PhysicalEquipmentId,
}


/**
 * A measured or computed time series (historian tag, SCADA point).
 */
export interface Signal extends Entity {
    measures_position?: FunctionalLocationId[],
    /** vibration_velocity | motor_temperature | intake_pressure ... */
    quantity?: string,
    /** mm/s | degC | bar ... */
    engineering_unit?: string,
    alarm_high?: number,
    sample_seconds?: number,
}



export interface Document extends Entity {
    /** P&ID | datasheet | completion schematic | procedure */
    doc_kind?: string,
    revision?: string,
    depicts?: FunctionalLocationId[],
    about_unit?: PhysicalEquipmentId[],
    /** Findings or abstract, as written */
    summary?: string,
    issued_on?: date,
}



export interface Event extends Entity {
    occurred_on: date,
}



export interface FailureEvent extends Event {
    mode: string,
    of_unit: PhysicalEquipmentId,
    at_position: FunctionalLocationId,
    installation?: InstallationId,
    description?: string,
}


/**
 * A maintenance notification or malfunction report.
 */
export interface Notification extends Event {
    about_position?: FunctionalLocationId,
    about_unit?: PhysicalEquipmentId,
    /** Free text as typed; treat as untrusted data */
    text?: string,
}


/**
 * A homogeneous batch of a purchased material (bearing set, elastomer compound).
 */
export interface MaterialLot extends Entity {
    material?: string,
    supplier?: OrganizationId,
    introduced_by?: EngineeringChangeId,
}


/**
 * An ECO. The route says how it was approved.
 */
export interface EngineeringChange extends Entity {
    approved_on?: date,
    /** standard | expedited */
    route?: string,
    qualification_test_waived?: boolean,
    change_summary?: string,
}



export interface WarrantyClaim extends Entity {
    raised_by?: OrganizationId,
    covers_units?: PhysicalEquipmentId[],
    opened_on?: date,
}


/**
 * An investigation opened by an alarm or a question. Holds findings and drafts.
 */
export interface Case extends Entity {
    trigger?: string,
    opened_at?: string,
    severity?: string,
}


/**
 * A proposed write to a system of record. Never applied without a named approver.
 */
export interface Draft extends Entity {
    target_system?: string,
    status: string,
    required_role?: string,
    approved_by?: string,
    case?: CaseId,
}


/**
 * Provenance of one identity or relationship link between source records.
 */
export interface LinkAssertion {
    subject: string,
    predicate: string,
    object: string,
    method: string,
    confidence: number,
    /** Rule name or the record pair the link came from */
    evidence?: string,
}


/**
 * A process unit such as a crude distillation unit; positions hang under it.
 */
export interface ProcessUnit extends FunctionalLocation {
    capacity_bpd?: number,
}



export interface PumpPosition extends FunctionalLocation {
    /** Pumped service */
    service?: string,
    rated_flow_m3h?: number,
    /** API 610 type, e.g. BB2 */
    api_type?: string,
}



export interface Stream extends Entity {
    from_position?: FunctionalLocationId,
    to_position?: FunctionalLocationId,
    medium?: string,
}


/**
 * A plant change request; ties engineering changes to positions.
 */
export interface ManagementOfChange extends Entity {
    affects?: FunctionalLocationId[],
    approved_on?: date,
}



export interface OilField extends Site {
}



export interface Well extends FunctionalLocation {
    pad?: string,
    /** esp | gas_lift | rod_pump */
    lift_method?: string,
    producing?: boolean,
}


/**
 * The artificial-lift position in a well (the ESP slot), under the Well.
 */
export interface ESPPosition extends FunctionalLocation {
    setting_depth_m?: number,
}


/**
 * A complete submersible pump string as run in a well.
 */
export interface ESPString extends PhysicalEquipment {
    components?: ESPComponentId[],
}



export interface ESPComponent extends PhysicalEquipment {
    kind: string,
}


/**
 * One run of a string in a well. Run life belongs to the string, not to the well.
 */
export interface RunRecord extends Entity {
    installation?: InstallationId,
    start?: date,
    end?: date,
    end_state: string,
    run_days?: number,
}



export interface Workover extends Event {
    rig?: string,
    pulled_unit?: PhysicalEquipmentId,
    set_unit?: PhysicalEquipmentId,
    at_position?: FunctionalLocationId,
}


/**
 * Production lost or at risk while a well runs degraded or is down.
 */
export interface Deferment {
    well?: WellId,
    barrels_per_day?: number,
    reason?: string,
}



export interface BuildRecord extends Entity {
    unit: PhysicalEquipmentId,
    built_on?: date,
    work_order?: string,
    lots?: MaterialLotId[],
}



export interface TestRecord extends Entity {
    unit?: PhysicalEquipmentId,
    /** performance | leak | press_fit_force */
    test_kind?: string,
    passed?: boolean,
    value?: number,
    engineering_unit?: string,
}



export interface Shipment extends Entity {
    unit?: PhysicalEquipmentId,
    customer?: OrganizationId,
    shipped_on?: date,
}



export interface NonConformance extends Entity {
    lots?: MaterialLotId[],
    opened_on?: date,
    description?: string,
}


/**
 * Corrective-action report (8D). Always created as a draft by agents.
 */
export interface EightD extends Entity {
    covers_claims?: WarrantyClaimId[],
    root_cause?: string,
    containment_units?: PhysicalEquipmentId[],
}



export interface KpiDefinition extends Entity {
    /** The decision the KPI supports */
    question?: string,
    /** unit | position | fleet | lot */
    grain?: string,
    /** How it is computed, in one sentence */
    method?: string,
    /** Standard it follows, if any */
    standard?: string,
    /** Name of the SPARQL file that computes it */
    query?: string,
}



