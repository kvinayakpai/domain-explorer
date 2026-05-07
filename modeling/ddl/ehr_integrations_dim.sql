-- =============================================================================
-- EHR Integrations — dimensional mart
-- Star schema oriented around the *integration* fact (HL7 message throughput,
-- FHIR API call latency, ADT lag) and the *clinical* fact (encounter activity).
-- Grain stated per fact table.
-- =============================================================================

create schema if not exists ehr_integrations_dim;

create table if not exists ehr_integrations_dim.dim_date (
    date_key     integer primary key,
    date_actual  date not null,
    day_of_week  smallint not null,
    iso_week     smallint not null,
    fiscal_period varchar(8)
);

create table if not exists ehr_integrations_dim.dim_time (
    time_key     integer primary key,
    hour_of_day  smallint not null,
    minute_of_hour smallint not null
);

-- SCD2 — patient demographic snapshot
create table if not exists ehr_integrations_dim.dim_patient (
    patient_key       bigint primary key,
    patient_id        varchar not null,
    mrn               varchar(64) not null,
    family_name       varchar(128),
    gender            varchar(16),
    birth_date        date,
    age_band          varchar(16),
    race_code         varchar(16),
    ethnicity_code    varchar(16),
    address_postal_code varchar(16),
    valid_from        timestamp not null,
    valid_to          timestamp,
    is_current        boolean not null
);

-- SCD2 — practitioner
create table if not exists ehr_integrations_dim.dim_practitioner (
    practitioner_key  bigint primary key,
    practitioner_id   varchar not null,
    npi               varchar(10),
    family_name       varchar(128),
    given_names       varchar(255),
    qualification_code varchar(32),
    valid_from        timestamp not null,
    valid_to          timestamp,
    is_current        boolean not null
);

-- SCD2 — organization (facility)
create table if not exists ehr_integrations_dim.dim_organization (
    organization_key bigint primary key,
    organization_id  varchar not null,
    type_code        varchar(32),
    name             varchar(255),
    address_state    varchar(8),
    valid_from       timestamp not null,
    valid_to         timestamp,
    is_current       boolean not null
);

-- Conformed dim — terminology code (LOINC / SNOMED / RxNorm / ICD-10)
create table if not exists ehr_integrations_dim.dim_terminology_code (
    terminology_key bigint primary key,
    code_system     varchar(64) not null,
    code_value      varchar(32) not null,
    code_display    varchar(255),
    parent_concept  varchar(32),
    valid_from      timestamp not null,
    valid_to        timestamp,
    is_current      boolean not null
);

create table if not exists ehr_integrations_dim.dim_encounter_class (
    encounter_class_key smallint primary key,
    class_code          varchar(8) not null,
    class_label         varchar(32) not null
);

create table if not exists ehr_integrations_dim.dim_message_type (
    message_type_key smallint primary key,
    message_type     varchar(8) not null,
    trigger_event    varchar(8) not null,
    label            varchar(64) not null
);

-- ---------------------------------------------------------------------------
-- Facts
-- ---------------------------------------------------------------------------

-- Grain: one row per Encounter (clinical fact).
create table if not exists ehr_integrations_dim.fact_encounter (
    encounter_id            varchar primary key,
    patient_key             bigint not null references ehr_integrations_dim.dim_patient(patient_key),
    practitioner_key        bigint references ehr_integrations_dim.dim_practitioner(practitioner_key),
    organization_key        bigint references ehr_integrations_dim.dim_organization(organization_key),
    encounter_class_key     smallint not null references ehr_integrations_dim.dim_encounter_class(encounter_class_key),
    start_date_key          integer not null references ehr_integrations_dim.dim_date(date_key),
    end_date_key            integer references ehr_integrations_dim.dim_date(date_key),
    length_minutes          integer,
    observation_count       integer not null default 0,
    medication_request_count integer not null default 0,
    procedure_count         integer not null default 0,
    diagnostic_report_count integer not null default 0,
    is_readmission_30d      boolean not null default false
);

-- Grain: one row per HL7 v2 message (integration fact).
create table if not exists ehr_integrations_dim.fact_hl7_message (
    message_control_id  varchar(64) primary key,
    message_type_key    smallint not null references ehr_integrations_dim.dim_message_type(message_type_key),
    sending_org_key     bigint references ehr_integrations_dim.dim_organization(organization_key),
    receiving_org_key   bigint references ehr_integrations_dim.dim_organization(organization_key),
    sent_date_key       integer not null references ehr_integrations_dim.dim_date(date_key),
    sent_time_key       integer references ehr_integrations_dim.dim_time(time_key),
    ack_lag_seconds     integer,
    ack_status          varchar(8),
    payload_bytes       integer,
    is_replayed         boolean not null default false
);

-- Grain: one row per FHIR API request (integration fact).
create table if not exists ehr_integrations_dim.fact_fhir_request (
    request_id          varchar primary key,
    resource_type       varchar(32) not null,
    interaction         varchar(16) not null,
    issued_date_key     integer not null references ehr_integrations_dim.dim_date(date_key),
    issued_time_key     integer references ehr_integrations_dim.dim_time(time_key),
    client_id           varchar(64),
    smart_scope         varchar(255),
    response_status     smallint not null,
    response_ms         integer not null,
    bytes_returned      integer,
    is_bulk_export      boolean not null default false
);

-- Grain: daily aggregate of patient match jobs.
create table if not exists ehr_integrations_dim.fact_match_daily (
    date_key            integer not null references ehr_integrations_dim.dim_date(date_key),
    candidate_pairs     integer not null,
    auto_matched        integer not null,
    queued_for_steward  integer not null,
    rejected            integer not null,
    duplicate_clusters  integer not null,
    primary key (date_key)
);
