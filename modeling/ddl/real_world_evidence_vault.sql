-- =============================================================================
-- Real-World Evidence — Data Vault 2.0
-- Hubs: person, visit, condition, drug, measurement, provider. Bitemporal sat
-- enables audit of vocabulary version applied to each fact at load time.
-- =============================================================================

create schema if not exists real_world_evidence_vault;

create table if not exists real_world_evidence_vault.hub_person (
    person_hk bytea primary key,
    person_bk varchar not null,
    load_dts  timestamp not null,
    rec_src   varchar not null
);

create table if not exists real_world_evidence_vault.hub_visit (
    visit_hk bytea primary key,
    visit_bk varchar not null,
    load_dts timestamp not null,
    rec_src  varchar not null
);

create table if not exists real_world_evidence_vault.hub_condition (
    condition_hk bytea primary key,
    condition_bk varchar not null,
    load_dts     timestamp not null,
    rec_src      varchar not null
);

create table if not exists real_world_evidence_vault.hub_drug (
    drug_hk bytea primary key,
    drug_bk varchar not null,
    load_dts timestamp not null,
    rec_src  varchar not null
);

create table if not exists real_world_evidence_vault.hub_measurement (
    measurement_hk bytea primary key,
    measurement_bk varchar not null,
    load_dts       timestamp not null,
    rec_src        varchar not null
);

create table if not exists real_world_evidence_vault.hub_provider (
    provider_hk bytea primary key,
    provider_bk varchar not null,
    load_dts    timestamp not null,
    rec_src     varchar not null
);

create table if not exists real_world_evidence_vault.hub_concept (
    concept_hk   bytea primary key,
    concept_id   integer not null,
    vocabulary_id varchar(20) not null,
    load_dts     timestamp not null,
    rec_src      varchar not null
);

-- ---------------------------------------------------------------------------
-- Links
-- ---------------------------------------------------------------------------
create table if not exists real_world_evidence_vault.link_visit_person (
    link_hk   bytea primary key,
    person_hk bytea not null references real_world_evidence_vault.hub_person(person_hk),
    visit_hk  bytea not null references real_world_evidence_vault.hub_visit(visit_hk),
    load_dts  timestamp not null,
    rec_src   varchar not null
);

create table if not exists real_world_evidence_vault.link_condition_person (
    link_hk      bytea primary key,
    person_hk    bytea not null references real_world_evidence_vault.hub_person(person_hk),
    condition_hk bytea not null references real_world_evidence_vault.hub_condition(condition_hk),
    visit_hk     bytea references real_world_evidence_vault.hub_visit(visit_hk),
    concept_hk   bytea references real_world_evidence_vault.hub_concept(concept_hk),
    load_dts     timestamp not null,
    rec_src      varchar not null
);

create table if not exists real_world_evidence_vault.link_drug_person (
    link_hk    bytea primary key,
    person_hk  bytea not null references real_world_evidence_vault.hub_person(person_hk),
    drug_hk    bytea not null references real_world_evidence_vault.hub_drug(drug_hk),
    visit_hk   bytea references real_world_evidence_vault.hub_visit(visit_hk),
    concept_hk bytea references real_world_evidence_vault.hub_concept(concept_hk),
    load_dts   timestamp not null,
    rec_src    varchar not null
);

create table if not exists real_world_evidence_vault.link_measurement_person (
    link_hk        bytea primary key,
    person_hk      bytea not null references real_world_evidence_vault.hub_person(person_hk),
    measurement_hk bytea not null references real_world_evidence_vault.hub_measurement(measurement_hk),
    visit_hk       bytea references real_world_evidence_vault.hub_visit(visit_hk),
    concept_hk     bytea references real_world_evidence_vault.hub_concept(concept_hk),
    load_dts       timestamp not null,
    rec_src        varchar not null
);

-- ---------------------------------------------------------------------------
-- Satellites (bitemporal)
-- ---------------------------------------------------------------------------
create table if not exists real_world_evidence_vault.sat_person_demographics (
    person_hk             bytea not null references real_world_evidence_vault.hub_person(person_hk),
    load_dts              timestamp not null,
    load_end_dts          timestamp,
    hash_diff             bytea not null,
    gender_concept_id     integer not null,
    year_of_birth         smallint not null,
    race_concept_id       integer,
    ethnicity_concept_id  integer,
    rec_src               varchar not null,
    primary key (person_hk, load_dts)
);

create table if not exists real_world_evidence_vault.sat_visit_state (
    visit_hk                  bytea not null references real_world_evidence_vault.hub_visit(visit_hk),
    load_dts                  timestamp not null,
    load_end_dts              timestamp,
    hash_diff                 bytea not null,
    visit_concept_id          integer not null,
    visit_start_date          date not null,
    visit_end_date            date not null,
    visit_type_concept_id     integer not null,
    admitted_from_concept_id  integer,
    discharged_to_concept_id  integer,
    rec_src                   varchar not null,
    primary key (visit_hk, load_dts)
);

create table if not exists real_world_evidence_vault.sat_condition_state (
    link_hk                      bytea not null,
    load_dts                     timestamp not null,
    load_end_dts                 timestamp,
    hash_diff                    bytea not null,
    condition_concept_id         integer not null,
    condition_start_date         date not null,
    condition_end_date           date,
    condition_type_concept_id    integer not null,
    condition_status_concept_id  integer,
    condition_source_value       varchar(50),
    condition_source_concept_id  integer,
    rec_src                      varchar not null,
    primary key (link_hk, load_dts)
);

create table if not exists real_world_evidence_vault.sat_drug_exposure (
    link_hk                      bytea not null,
    load_dts                     timestamp not null,
    load_end_dts                 timestamp,
    hash_diff                    bytea not null,
    drug_concept_id              integer not null,
    drug_exposure_start_date     date not null,
    drug_exposure_end_date       date not null,
    drug_type_concept_id         integer not null,
    quantity                     numeric(18, 6),
    days_supply                  integer,
    refills                      integer,
    route_concept_id             integer,
    drug_source_value            varchar(50),
    rec_src                      varchar not null,
    primary key (link_hk, load_dts)
);

create table if not exists real_world_evidence_vault.sat_measurement_value (
    link_hk                  bytea not null,
    load_dts                 timestamp not null,
    load_end_dts             timestamp,
    hash_diff                bytea not null,
    measurement_concept_id   integer not null,
    measurement_date         date not null,
    value_as_number          numeric(18, 6),
    value_as_concept_id      integer,
    unit_concept_id          integer,
    range_low                numeric(18, 6),
    range_high               numeric(18, 6),
    measurement_source_value varchar(50),
    rec_src                  varchar not null,
    primary key (link_hk, load_dts)
);

create table if not exists real_world_evidence_vault.sat_concept_descriptive (
    concept_hk        bytea not null references real_world_evidence_vault.hub_concept(concept_hk),
    load_dts          timestamp not null,
    load_end_dts      timestamp,
    hash_diff         bytea not null,
    concept_name      varchar(255) not null,
    domain_id         varchar(20) not null,
    concept_class_id  varchar(20) not null,
    standard_concept  varchar(1),
    concept_code      varchar(50) not null,
    valid_start_date  date not null,
    valid_end_date    date not null,
    invalid_reason    varchar(1),
    rec_src           varchar not null,
    primary key (concept_hk, load_dts)
);
