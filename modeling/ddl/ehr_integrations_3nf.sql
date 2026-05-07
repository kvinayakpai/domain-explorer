-- =============================================================================
-- EHR Integrations — 3NF schema
-- Source standard: HL7 FHIR R4 (https://hl7.org/fhir/R4/) + USCDI v3.
-- Each table maps to a single FHIR resource; column names mirror FHIR element
-- paths where practical (relational types substituted for FHIR datatypes).
-- =============================================================================

create schema if not exists ehr_integrations_3nf;

-- ---------------------------------------------------------------------------
-- Reference / party tables
-- ---------------------------------------------------------------------------
create table if not exists ehr_integrations_3nf.organization (
    organization_id          varchar primary key,
    identifier_npi           varchar(10),
    type_code                varchar(32),
    name                     varchar(255) not null,
    telecom_phone            varchar(32),
    address_line             varchar(255),
    address_city             varchar(64),
    address_state            varchar(8),
    address_postal_code      varchar(16),
    part_of_organization_id  varchar references ehr_integrations_3nf.organization(organization_id),
    active                   boolean not null default true
);

create table if not exists ehr_integrations_3nf.location (
    location_id              varchar primary key,
    name                     varchar(255) not null,
    status                   varchar(16),
    mode                     varchar(16),
    type_code                varchar(32),
    managing_organization_id varchar references ehr_integrations_3nf.organization(organization_id),
    address_line             varchar(255),
    address_city             varchar(64),
    address_state            varchar(8),
    position_latitude        numeric(9, 6),
    position_longitude       numeric(9, 6)
);

create table if not exists ehr_integrations_3nf.practitioner (
    practitioner_id           varchar primary key,
    npi                       varchar(10),
    family_name               varchar(128) not null,
    given_names               varchar(255),
    gender                    varchar(16),
    qualification_code        varchar(32),
    qualification_issuer_org_id varchar,
    qualification_period_start date,
    qualification_period_end   date,
    active                    boolean not null default true
);

create table if not exists ehr_integrations_3nf.patient (
    patient_id                varchar primary key,
    identifier_mrn            varchar(64) not null,
    identifier_ssn_hash       varchar(64),
    family_name               varchar(128) not null,
    given_names               varchar(255),
    gender                    varchar(16),
    birth_date                date,
    deceased_date_time        timestamp,
    marital_status_code       varchar(16),
    race_code                 varchar(16),
    ethnicity_code            varchar(16),
    address_line              varchar(255),
    address_city              varchar(64),
    address_state             varchar(8),
    address_postal_code       varchar(16),
    address_country           varchar(2),
    phone_e164                varchar(32),
    email                     varchar(255),
    managing_organization_id  varchar references ehr_integrations_3nf.organization(organization_id),
    language_code             varchar(8)
);

-- ---------------------------------------------------------------------------
-- Clinical encounter
-- ---------------------------------------------------------------------------
create table if not exists ehr_integrations_3nf.encounter (
    encounter_id                          varchar primary key,
    patient_id                            varchar not null references ehr_integrations_3nf.patient(patient_id),
    status                                varchar(16) not null,
    class_code                            varchar(8) not null,
    type_code                             varchar(32),
    priority_code                         varchar(16),
    primary_practitioner_id               varchar references ehr_integrations_3nf.practitioner(practitioner_id),
    service_provider_org_id               varchar references ehr_integrations_3nf.organization(organization_id),
    location_id                           varchar references ehr_integrations_3nf.location(location_id),
    period_start                          timestamp not null,
    period_end                            timestamp,
    length_minutes                        integer,
    hospitalization_admit_source          varchar(16),
    hospitalization_discharge_disposition varchar(16),
    reason_code                           varchar(32)
);

-- ---------------------------------------------------------------------------
-- Clinical resources
-- ---------------------------------------------------------------------------
create table if not exists ehr_integrations_3nf.condition (
    condition_id              varchar primary key,
    patient_id                varchar not null references ehr_integrations_3nf.patient(patient_id),
    encounter_id              varchar references ehr_integrations_3nf.encounter(encounter_id),
    clinical_status_code      varchar(16),
    verification_status_code  varchar(16),
    category_code             varchar(32),
    severity_code             varchar(16),
    code_system               varchar(64) not null,
    code_value                varchar(32) not null,
    code_display              varchar(255),
    onset_date_time           timestamp,
    abatement_date_time       timestamp,
    recorded_date             date,
    recorder_id               varchar
);

create table if not exists ehr_integrations_3nf.observation (
    observation_id              varchar primary key,
    patient_id                  varchar not null references ehr_integrations_3nf.patient(patient_id),
    encounter_id                varchar references ehr_integrations_3nf.encounter(encounter_id),
    status                      varchar(16) not null,
    category_code               varchar(32) not null,
    code_system                 varchar(64) not null,
    code_value                  varchar(32) not null,
    code_display                varchar(255),
    effective_date_time         timestamp not null,
    issued                      timestamp,
    value_quantity_value        numeric(18, 6),
    value_quantity_unit         varchar(16),
    value_codeable_concept_code varchar(32),
    value_string                text,
    interpretation_code         varchar(8),
    reference_range_low         numeric(18, 6),
    reference_range_high        numeric(18, 6),
    performer_id                varchar references ehr_integrations_3nf.practitioner(practitioner_id),
    data_absent_reason_code     varchar(16)
);

create table if not exists ehr_integrations_3nf.medication_request (
    medication_request_id     varchar primary key,
    patient_id                varchar not null references ehr_integrations_3nf.patient(patient_id),
    encounter_id              varchar references ehr_integrations_3nf.encounter(encounter_id),
    requester_id              varchar references ehr_integrations_3nf.practitioner(practitioner_id),
    status                    varchar(16) not null,
    intent                    varchar(16) not null,
    priority                  varchar(16),
    medication_code_system    varchar(64) not null,
    medication_code_value     varchar(32) not null,
    medication_display        varchar(255),
    dose_quantity_value       numeric(12, 4),
    dose_quantity_unit        varchar(16),
    route_code                varchar(16),
    frequency_text            varchar(64),
    authored_on               timestamp not null,
    validity_period_start     timestamp,
    validity_period_end       timestamp,
    dispense_quantity         numeric(12, 4),
    dispense_refills_allowed  smallint,
    substitution_allowed      boolean
);

create table if not exists ehr_integrations_3nf.procedure (
    procedure_id            varchar primary key,
    patient_id              varchar not null references ehr_integrations_3nf.patient(patient_id),
    encounter_id            varchar references ehr_integrations_3nf.encounter(encounter_id),
    status                  varchar(16) not null,
    code_system             varchar(64) not null,
    code_value              varchar(16) not null,
    code_display            varchar(255),
    performed_period_start  timestamp,
    performed_period_end    timestamp,
    performer_id            varchar references ehr_integrations_3nf.practitioner(practitioner_id),
    location_id             varchar references ehr_integrations_3nf.location(location_id),
    outcome_code            varchar(32),
    complication_code       varchar(32)
);

create table if not exists ehr_integrations_3nf.allergy_intolerance (
    allergy_id                  varchar primary key,
    patient_id                  varchar not null references ehr_integrations_3nf.patient(patient_id),
    clinical_status_code        varchar(16),
    verification_status_code    varchar(16),
    type                        varchar(16),
    category                    varchar(16),
    criticality                 varchar(16),
    substance_code_system       varchar(64),
    substance_code_value        varchar(32),
    substance_display           varchar(255),
    reaction_manifestation_code varchar(32),
    reaction_severity           varchar(16),
    onset_date_time             timestamp,
    recorded_date               timestamp
);

create table if not exists ehr_integrations_3nf.immunization (
    immunization_id      varchar primary key,
    patient_id           varchar not null references ehr_integrations_3nf.patient(patient_id),
    encounter_id         varchar references ehr_integrations_3nf.encounter(encounter_id),
    status               varchar(16) not null,
    vaccine_code_system  varchar(64) not null,
    vaccine_code_value   varchar(16) not null,
    occurrence_date_time timestamp not null,
    lot_number           varchar(32),
    expiration_date      date,
    site_code            varchar(16),
    route_code           varchar(16),
    dose_quantity        numeric(8, 3),
    dose_quantity_unit   varchar(16),
    performer_id         varchar references ehr_integrations_3nf.practitioner(practitioner_id)
);

create table if not exists ehr_integrations_3nf.diagnostic_report (
    diagnostic_report_id      varchar primary key,
    patient_id                varchar not null references ehr_integrations_3nf.patient(patient_id),
    encounter_id              varchar references ehr_integrations_3nf.encounter(encounter_id),
    status                    varchar(16) not null,
    category_code             varchar(32),
    code_system               varchar(64) not null,
    code_value                varchar(16) not null,
    code_display              varchar(255),
    effective_date_time       timestamp,
    issued                    timestamp,
    performer_org_id          varchar references ehr_integrations_3nf.organization(organization_id),
    results_interpreter_id    varchar references ehr_integrations_3nf.practitioner(practitioner_id),
    conclusion                text
);

create table if not exists ehr_integrations_3nf.diagnostic_report_observation (
    diagnostic_report_id  varchar not null references ehr_integrations_3nf.diagnostic_report(diagnostic_report_id),
    observation_id        varchar not null references ehr_integrations_3nf.observation(observation_id),
    primary key (diagnostic_report_id, observation_id)
);

-- ---------------------------------------------------------------------------
-- Coverage and consent
-- ---------------------------------------------------------------------------
create table if not exists ehr_integrations_3nf.coverage (
    coverage_id          varchar primary key,
    patient_id           varchar not null references ehr_integrations_3nf.patient(patient_id),
    status               varchar(16) not null,
    type_code            varchar(32),
    subscriber_id        varchar(64),
    payor_org_id         varchar references ehr_integrations_3nf.organization(organization_id),
    relationship_code    varchar(16),
    period_start         date,
    period_end           date,
    plan_group           varchar(32),
    plan_name            varchar(64),
    order_position       smallint,
    network              varchar(64)
);

create table if not exists ehr_integrations_3nf.consent (
    consent_id                varchar primary key,
    patient_id                varchar not null references ehr_integrations_3nf.patient(patient_id),
    status                    varchar(16) not null,
    scope_code                varchar(32) not null,
    category_code             varchar(32) not null,
    date_time                 timestamp not null,
    organization_id           varchar references ehr_integrations_3nf.organization(organization_id),
    source_attachment_uri     varchar(255),
    policy_uri                varchar(255),
    provision_type            varchar(8),
    provision_period_start    timestamp,
    provision_period_end      timestamp,
    provision_purpose_code    varchar(32),
    provision_action_code     varchar(32)
);

-- ---------------------------------------------------------------------------
-- Operational interface envelopes
-- ---------------------------------------------------------------------------
create table if not exists ehr_integrations_3nf.hl7v2_message (
    message_control_id    varchar(64) primary key,
    message_type          varchar(8) not null,
    trigger_event         varchar(8) not null,
    sending_application   varchar(32),
    sending_facility      varchar(32),
    receiving_application varchar(32),
    receiving_facility    varchar(32),
    message_datetime      timestamp not null,
    processing_id         varchar(8),
    version_id            varchar(8),
    ack_status            varchar(8),
    ack_received_at       timestamp,
    payload_uri           varchar(255),
    patient_id            varchar references ehr_integrations_3nf.patient(patient_id),
    encounter_id          varchar references ehr_integrations_3nf.encounter(encounter_id)
);

create table if not exists ehr_integrations_3nf.smart_authorization (
    authorization_id      varchar primary key,
    client_id             varchar(64) not null,
    patient_id            varchar references ehr_integrations_3nf.patient(patient_id),
    practitioner_id       varchar references ehr_integrations_3nf.practitioner(practitioner_id),
    scope                 varchar(255) not null,
    launch_context        varchar(255),
    token_type            varchar(16) not null default 'Bearer',
    issued_at             timestamp not null,
    expires_at            timestamp not null,
    revoked_at            timestamp,
    refresh_token_hash    varchar(64)
);
