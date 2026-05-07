-- =============================================================================
-- Real-World Evidence — 3NF schema
-- Source standard: OHDSI OMOP Common Data Model v5.4
-- (https://ohdsi.github.io/CommonDataModel/cdm54.html). Table and column names
-- mirror the OMOP spec verbatim.
-- =============================================================================

create schema if not exists real_world_evidence_3nf;

create table if not exists real_world_evidence_3nf.location (
    location_id            bigint primary key,
    address_1              varchar(50),
    address_2              varchar(50),
    city                   varchar(50),
    state                  varchar(2),
    zip                    varchar(9),
    county                 varchar(20),
    country_concept_id     integer,
    country_source_value   varchar(80),
    location_source_value  varchar(50),
    latitude               numeric(8, 6),
    longitude              numeric(9, 6)
);

create table if not exists real_world_evidence_3nf.care_site (
    care_site_id                  bigint primary key,
    care_site_name                varchar(255),
    place_of_service_concept_id   integer,
    location_id                   bigint references real_world_evidence_3nf.location(location_id),
    care_site_source_value        varchar(50),
    place_of_service_source_value varchar(50)
);

create table if not exists real_world_evidence_3nf.provider (
    provider_id                   bigint primary key,
    provider_name                 varchar(255),
    npi                           varchar(20),
    dea                           varchar(20),
    specialty_concept_id          integer,
    care_site_id                  bigint references real_world_evidence_3nf.care_site(care_site_id),
    year_of_birth                 smallint,
    gender_concept_id             integer,
    provider_source_value         varchar(50),
    specialty_source_value        varchar(50),
    specialty_source_concept_id   integer,
    gender_source_value           varchar(50),
    gender_source_concept_id      integer
);

create table if not exists real_world_evidence_3nf.person (
    person_id                  bigint primary key,
    gender_concept_id          integer not null,
    year_of_birth              smallint not null,
    month_of_birth             smallint,
    day_of_birth               smallint,
    birth_datetime             timestamp,
    race_concept_id            integer not null,
    ethnicity_concept_id       integer not null,
    location_id                bigint references real_world_evidence_3nf.location(location_id),
    provider_id                bigint references real_world_evidence_3nf.provider(provider_id),
    care_site_id               bigint references real_world_evidence_3nf.care_site(care_site_id),
    person_source_value        varchar(50),
    gender_source_value        varchar(50),
    gender_source_concept_id   integer,
    race_source_value          varchar(50),
    race_source_concept_id     integer,
    ethnicity_source_value     varchar(50),
    ethnicity_source_concept_id integer
);

create table if not exists real_world_evidence_3nf.observation_period (
    observation_period_id        bigint primary key,
    person_id                    bigint not null references real_world_evidence_3nf.person(person_id),
    observation_period_start_date date not null,
    observation_period_end_date  date not null,
    period_type_concept_id       integer not null
);

create table if not exists real_world_evidence_3nf.visit_occurrence (
    visit_occurrence_id            bigint primary key,
    person_id                      bigint not null references real_world_evidence_3nf.person(person_id),
    visit_concept_id               integer not null,
    visit_start_date               date not null,
    visit_start_datetime           timestamp,
    visit_end_date                 date not null,
    visit_end_datetime             timestamp,
    visit_type_concept_id          integer not null,
    provider_id                    bigint references real_world_evidence_3nf.provider(provider_id),
    care_site_id                   bigint references real_world_evidence_3nf.care_site(care_site_id),
    visit_source_value             varchar(50),
    visit_source_concept_id        integer,
    admitted_from_concept_id       integer,
    admitted_from_source_value     varchar(50),
    discharged_to_concept_id       integer,
    discharged_to_source_value     varchar(50),
    preceding_visit_occurrence_id  bigint
);

create table if not exists real_world_evidence_3nf.condition_occurrence (
    condition_occurrence_id       bigint primary key,
    person_id                     bigint not null references real_world_evidence_3nf.person(person_id),
    condition_concept_id          integer not null,
    condition_start_date          date not null,
    condition_start_datetime      timestamp,
    condition_end_date            date,
    condition_end_datetime        timestamp,
    condition_type_concept_id     integer not null,
    condition_status_concept_id   integer,
    stop_reason                   varchar(20),
    provider_id                   bigint references real_world_evidence_3nf.provider(provider_id),
    visit_occurrence_id           bigint references real_world_evidence_3nf.visit_occurrence(visit_occurrence_id),
    visit_detail_id               bigint,
    condition_source_value        varchar(50),
    condition_source_concept_id   integer,
    condition_status_source_value varchar(50)
);

create table if not exists real_world_evidence_3nf.drug_exposure (
    drug_exposure_id              bigint primary key,
    person_id                     bigint not null references real_world_evidence_3nf.person(person_id),
    drug_concept_id               integer not null,
    drug_exposure_start_date      date not null,
    drug_exposure_start_datetime  timestamp,
    drug_exposure_end_date        date not null,
    drug_exposure_end_datetime    timestamp,
    verbatim_end_date             date,
    drug_type_concept_id          integer not null,
    stop_reason                   varchar(20),
    refills                       integer,
    quantity                      numeric(18, 6),
    days_supply                   integer,
    sig                           text,
    route_concept_id              integer,
    lot_number                    varchar(50),
    provider_id                   bigint references real_world_evidence_3nf.provider(provider_id),
    visit_occurrence_id           bigint references real_world_evidence_3nf.visit_occurrence(visit_occurrence_id),
    visit_detail_id               bigint,
    drug_source_value             varchar(50),
    drug_source_concept_id        integer,
    route_source_value            varchar(50),
    dose_unit_source_value        varchar(50)
);

create table if not exists real_world_evidence_3nf.procedure_occurrence (
    procedure_occurrence_id    bigint primary key,
    person_id                  bigint not null references real_world_evidence_3nf.person(person_id),
    procedure_concept_id       integer not null,
    procedure_date             date not null,
    procedure_datetime         timestamp,
    procedure_end_date         date,
    procedure_end_datetime     timestamp,
    procedure_type_concept_id  integer not null,
    modifier_concept_id        integer,
    quantity                   integer,
    provider_id                bigint references real_world_evidence_3nf.provider(provider_id),
    visit_occurrence_id        bigint references real_world_evidence_3nf.visit_occurrence(visit_occurrence_id),
    visit_detail_id            bigint,
    procedure_source_value     varchar(50),
    procedure_source_concept_id integer,
    modifier_source_value      varchar(50)
);

create table if not exists real_world_evidence_3nf.measurement (
    measurement_id              bigint primary key,
    person_id                   bigint not null references real_world_evidence_3nf.person(person_id),
    measurement_concept_id      integer not null,
    measurement_date            date not null,
    measurement_datetime        timestamp,
    measurement_time            varchar(10),
    measurement_type_concept_id integer not null,
    operator_concept_id         integer,
    value_as_number             numeric(18, 6),
    value_as_concept_id         integer,
    unit_concept_id             integer,
    range_low                   numeric(18, 6),
    range_high                  numeric(18, 6),
    provider_id                 bigint references real_world_evidence_3nf.provider(provider_id),
    visit_occurrence_id         bigint references real_world_evidence_3nf.visit_occurrence(visit_occurrence_id),
    visit_detail_id             bigint,
    measurement_source_value    varchar(50),
    measurement_source_concept_id integer,
    unit_source_value           varchar(50),
    unit_source_concept_id      integer,
    value_source_value          varchar(50)
);

create table if not exists real_world_evidence_3nf.observation (
    observation_id              bigint primary key,
    person_id                   bigint not null references real_world_evidence_3nf.person(person_id),
    observation_concept_id      integer not null,
    observation_date            date not null,
    observation_datetime        timestamp,
    observation_type_concept_id integer not null,
    value_as_number             numeric(18, 6),
    value_as_string             varchar(60),
    value_as_concept_id         integer,
    qualifier_concept_id        integer,
    unit_concept_id             integer,
    provider_id                 bigint references real_world_evidence_3nf.provider(provider_id),
    visit_occurrence_id         bigint references real_world_evidence_3nf.visit_occurrence(visit_occurrence_id),
    visit_detail_id             bigint,
    observation_source_value    varchar(50),
    observation_source_concept_id integer,
    unit_source_value           varchar(50),
    qualifier_source_value      varchar(50),
    value_source_value          varchar(50),
    observation_event_id        bigint,
    obs_event_field_concept_id  integer
);

create table if not exists real_world_evidence_3nf.death (
    person_id                bigint primary key references real_world_evidence_3nf.person(person_id),
    death_date               date not null,
    death_datetime           timestamp,
    death_type_concept_id    integer not null,
    cause_concept_id         integer,
    cause_source_value       varchar(50),
    cause_source_concept_id  integer
);

create table if not exists real_world_evidence_3nf.payer_plan_period (
    payer_plan_period_id          bigint primary key,
    person_id                     bigint not null references real_world_evidence_3nf.person(person_id),
    payer_plan_period_start_date  date not null,
    payer_plan_period_end_date    date not null,
    payer_concept_id              integer,
    payer_source_value            varchar(50),
    plan_concept_id               integer,
    plan_source_value             varchar(50),
    sponsor_concept_id            integer,
    sponsor_source_value          varchar(50),
    family_source_value           varchar(50),
    stop_reason_concept_id        integer,
    stop_reason_source_value      varchar(50)
);

create table if not exists real_world_evidence_3nf.cost (
    cost_id                       bigint primary key,
    cost_event_id                 bigint not null,
    cost_domain_id                varchar(20) not null,
    cost_type_concept_id          integer not null,
    currency_concept_id           integer,
    total_charge                  numeric(20, 4),
    total_cost                    numeric(20, 4),
    total_paid                    numeric(20, 4),
    paid_by_payer                 numeric(20, 4),
    paid_by_patient               numeric(20, 4),
    paid_patient_copay            numeric(20, 4),
    paid_patient_coinsurance      numeric(20, 4),
    paid_patient_deductible       numeric(20, 4),
    paid_by_primary               numeric(20, 4),
    paid_ingredient_cost          numeric(20, 4),
    paid_dispensing_fee           numeric(20, 4),
    payer_plan_period_id          bigint references real_world_evidence_3nf.payer_plan_period(payer_plan_period_id),
    amount_allowed                numeric(20, 4),
    revenue_code_concept_id       integer,
    revenue_code_source_value     varchar(50),
    drg_concept_id                integer,
    drg_source_value              varchar(3)
);

create table if not exists real_world_evidence_3nf.concept (
    concept_id        integer primary key,
    concept_name      varchar(255) not null,
    domain_id         varchar(20) not null,
    vocabulary_id     varchar(20) not null,
    concept_class_id  varchar(20) not null,
    standard_concept  varchar(1),
    concept_code      varchar(50) not null,
    valid_start_date  date not null,
    valid_end_date    date not null,
    invalid_reason    varchar(1)
);

create table if not exists real_world_evidence_3nf.concept_relationship (
    concept_id_1     integer not null references real_world_evidence_3nf.concept(concept_id),
    concept_id_2     integer not null references real_world_evidence_3nf.concept(concept_id),
    relationship_id  varchar(20) not null,
    valid_start_date date not null,
    valid_end_date   date not null,
    invalid_reason   varchar(1),
    primary key (concept_id_1, concept_id_2, relationship_id)
);

create table if not exists real_world_evidence_3nf.cohort_definition (
    cohort_definition_id          integer primary key,
    cohort_definition_name        varchar(255) not null,
    cohort_definition_description text,
    definition_type_concept_id    integer not null,
    cohort_definition_syntax      text,
    subject_concept_id            integer,
    cohort_initiation_date        date
);

create table if not exists real_world_evidence_3nf.cohort (
    cohort_definition_id  integer not null references real_world_evidence_3nf.cohort_definition(cohort_definition_id),
    subject_id            bigint not null,
    cohort_start_date     date not null,
    cohort_end_date       date,
    primary key (cohort_definition_id, subject_id, cohort_start_date)
);
