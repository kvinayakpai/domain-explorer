-- =============================================================================
-- EHR Integrations — Data Vault 2.0
-- FHIR R4 resources promoted to hubs/links/satellites with bitemporal sats so
-- the historical state of any resource version is reconstructable.
-- =============================================================================

create schema if not exists ehr_integrations_vault;

-- ---------------------------------------------------------------------------
-- Hubs
-- ---------------------------------------------------------------------------
create table if not exists ehr_integrations_vault.hub_patient (
    patient_hk    bytea primary key,
    patient_bk    varchar not null,
    load_dts      timestamp not null,
    rec_src       varchar not null
);

create table if not exists ehr_integrations_vault.hub_practitioner (
    practitioner_hk bytea primary key,
    practitioner_bk varchar not null,
    load_dts        timestamp not null,
    rec_src         varchar not null
);

create table if not exists ehr_integrations_vault.hub_organization (
    organization_hk bytea primary key,
    organization_bk varchar not null,
    load_dts        timestamp not null,
    rec_src         varchar not null
);

create table if not exists ehr_integrations_vault.hub_encounter (
    encounter_hk  bytea primary key,
    encounter_bk  varchar not null,
    load_dts      timestamp not null,
    rec_src       varchar not null
);

create table if not exists ehr_integrations_vault.hub_observation (
    observation_hk bytea primary key,
    observation_bk varchar not null,
    load_dts       timestamp not null,
    rec_src        varchar not null
);

-- ---------------------------------------------------------------------------
-- Links
-- ---------------------------------------------------------------------------
create table if not exists ehr_integrations_vault.link_encounter_patient (
    link_hk         bytea primary key,
    encounter_hk    bytea not null references ehr_integrations_vault.hub_encounter(encounter_hk),
    patient_hk      bytea not null references ehr_integrations_vault.hub_patient(patient_hk),
    load_dts        timestamp not null,
    rec_src         varchar not null
);

create table if not exists ehr_integrations_vault.link_encounter_practitioner (
    link_hk         bytea primary key,
    encounter_hk    bytea not null references ehr_integrations_vault.hub_encounter(encounter_hk),
    practitioner_hk bytea not null references ehr_integrations_vault.hub_practitioner(practitioner_hk),
    role_code       varchar(16) not null,
    load_dts        timestamp not null,
    rec_src         varchar not null
);

create table if not exists ehr_integrations_vault.link_observation_encounter (
    link_hk         bytea primary key,
    observation_hk  bytea not null references ehr_integrations_vault.hub_observation(observation_hk),
    encounter_hk    bytea not null references ehr_integrations_vault.hub_encounter(encounter_hk),
    patient_hk      bytea not null references ehr_integrations_vault.hub_patient(patient_hk),
    load_dts        timestamp not null,
    rec_src         varchar not null
);

create table if not exists ehr_integrations_vault.link_medication_request (
    link_hk         bytea primary key,
    patient_hk      bytea not null references ehr_integrations_vault.hub_patient(patient_hk),
    encounter_hk    bytea references ehr_integrations_vault.hub_encounter(encounter_hk),
    practitioner_hk bytea references ehr_integrations_vault.hub_practitioner(practitioner_hk),
    medication_request_bk varchar not null,
    load_dts        timestamp not null,
    rec_src         varchar not null
);

create table if not exists ehr_integrations_vault.link_coverage (
    link_hk         bytea primary key,
    patient_hk      bytea not null references ehr_integrations_vault.hub_patient(patient_hk),
    payor_hk        bytea not null references ehr_integrations_vault.hub_organization(organization_hk),
    coverage_bk     varchar not null,
    load_dts        timestamp not null,
    rec_src         varchar not null
);

-- ---------------------------------------------------------------------------
-- Satellites (bitemporal — load_dts + load_end_dts; FHIR meta.lastUpdated)
-- ---------------------------------------------------------------------------
create table if not exists ehr_integrations_vault.sat_patient_demographics (
    patient_hk           bytea not null references ehr_integrations_vault.hub_patient(patient_hk),
    load_dts             timestamp not null,
    load_end_dts         timestamp,
    hash_diff            bytea not null,
    family_name          varchar(128) not null,
    given_names          varchar(255),
    gender               varchar(16),
    birth_date           date,
    deceased_date_time   timestamp,
    marital_status_code  varchar(16),
    race_code            varchar(16),
    ethnicity_code       varchar(16),
    address_line         varchar(255),
    address_city         varchar(64),
    address_state        varchar(8),
    address_postal_code  varchar(16),
    phone_e164           varchar(32),
    email                varchar(255),
    rec_src              varchar not null,
    primary key (patient_hk, load_dts)
);

create table if not exists ehr_integrations_vault.sat_practitioner_descriptive (
    practitioner_hk             bytea not null references ehr_integrations_vault.hub_practitioner(practitioner_hk),
    load_dts                    timestamp not null,
    load_end_dts                timestamp,
    hash_diff                   bytea not null,
    npi                         varchar(10),
    family_name                 varchar(128) not null,
    given_names                 varchar(255),
    gender                      varchar(16),
    qualification_code          varchar(32),
    qualification_period_start  date,
    qualification_period_end    date,
    active                      boolean not null default true,
    rec_src                     varchar not null,
    primary key (practitioner_hk, load_dts)
);

create table if not exists ehr_integrations_vault.sat_encounter_state (
    encounter_hk                          bytea not null references ehr_integrations_vault.hub_encounter(encounter_hk),
    load_dts                              timestamp not null,
    load_end_dts                          timestamp,
    hash_diff                             bytea not null,
    status                                varchar(16) not null,
    class_code                            varchar(8) not null,
    type_code                             varchar(32),
    period_start                          timestamp not null,
    period_end                            timestamp,
    length_minutes                        integer,
    hospitalization_admit_source          varchar(16),
    hospitalization_discharge_disposition varchar(16),
    rec_src                               varchar not null,
    primary key (encounter_hk, load_dts)
);

create table if not exists ehr_integrations_vault.sat_observation_value (
    observation_hk              bytea not null references ehr_integrations_vault.hub_observation(observation_hk),
    load_dts                    timestamp not null,
    load_end_dts                timestamp,
    hash_diff                   bytea not null,
    status                      varchar(16) not null,
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
    rec_src                     varchar not null,
    primary key (observation_hk, load_dts)
);

create table if not exists ehr_integrations_vault.sat_medication_request_state (
    link_hk                  bytea not null,
    load_dts                 timestamp not null,
    load_end_dts             timestamp,
    hash_diff                bytea not null,
    status                   varchar(16) not null,
    intent                   varchar(16) not null,
    medication_code_system   varchar(64) not null,
    medication_code_value    varchar(32) not null,
    medication_display       varchar(255),
    dose_quantity_value      numeric(12, 4),
    dose_quantity_unit       varchar(16),
    route_code               varchar(16),
    frequency_text           varchar(64),
    authored_on              timestamp not null,
    validity_period_start    timestamp,
    validity_period_end      timestamp,
    dispense_quantity        numeric(12, 4),
    dispense_refills_allowed smallint,
    substitution_allowed     boolean,
    rec_src                  varchar not null,
    primary key (link_hk, load_dts)
);

create table if not exists ehr_integrations_vault.sat_coverage_state (
    link_hk        bytea not null,
    load_dts       timestamp not null,
    load_end_dts   timestamp,
    hash_diff      bytea not null,
    status         varchar(16) not null,
    type_code      varchar(32),
    subscriber_id  varchar(64),
    relationship_code varchar(16),
    period_start   date,
    period_end     date,
    plan_group     varchar(32),
    plan_name      varchar(64),
    order_position smallint,
    network        varchar(64),
    rec_src        varchar not null,
    primary key (link_hk, load_dts)
);

create table if not exists ehr_integrations_vault.sat_consent_state (
    patient_hk             bytea not null references ehr_integrations_vault.hub_patient(patient_hk),
    consent_bk             varchar not null,
    load_dts               timestamp not null,
    load_end_dts           timestamp,
    hash_diff              bytea not null,
    status                 varchar(16) not null,
    scope_code             varchar(32) not null,
    category_code          varchar(32) not null,
    provision_type         varchar(8),
    provision_period_start timestamp,
    provision_period_end   timestamp,
    provision_purpose_code varchar(32),
    rec_src                varchar not null,
    primary key (patient_hk, consent_bk, load_dts)
);

create table if not exists ehr_integrations_vault.sat_hl7v2_message (
    message_control_id    varchar(64) primary key,
    load_dts              timestamp not null,
    hash_diff             bytea not null,
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
    rec_src               varchar not null
);
