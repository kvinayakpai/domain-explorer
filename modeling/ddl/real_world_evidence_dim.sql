-- =============================================================================
-- Real-World Evidence — dimensional mart
-- Star schema. Facts: visit, condition, drug_exposure, cohort_membership.
-- Conformed dim: person, concept, care_site, payer, date.
-- =============================================================================

create schema if not exists real_world_evidence_dim;

create table if not exists real_world_evidence_dim.dim_date (
    date_key      integer primary key,
    date_actual   date not null,
    day_of_week   smallint not null,
    iso_week      smallint not null,
    fiscal_period varchar(8)
);

create table if not exists real_world_evidence_dim.dim_person (
    person_key     bigint primary key,
    person_id      bigint not null,
    gender_code    varchar(8),
    age_band       varchar(16),
    race_code      varchar(16),
    ethnicity_code varchar(16),
    state          varchar(2),
    valid_from     timestamp not null,
    valid_to       timestamp,
    is_current     boolean not null
);

create table if not exists real_world_evidence_dim.dim_concept (
    concept_key       bigint primary key,
    concept_id        integer not null,
    concept_name      varchar(255),
    domain_id         varchar(20),
    vocabulary_id     varchar(20),
    standard_concept  varchar(1),
    valid_from        timestamp not null,
    valid_to          timestamp,
    is_current        boolean not null
);

create table if not exists real_world_evidence_dim.dim_care_site (
    care_site_key bigint primary key,
    care_site_id  bigint not null,
    place_of_service varchar(32),
    state         varchar(2),
    valid_from    timestamp not null,
    valid_to      timestamp,
    is_current    boolean not null
);

create table if not exists real_world_evidence_dim.dim_payer (
    payer_key       bigint primary key,
    payer_concept_id integer not null,
    payer_name      varchar(255),
    plan_concept_id integer,
    valid_from      timestamp not null,
    valid_to        timestamp,
    is_current      boolean not null
);

create table if not exists real_world_evidence_dim.dim_cohort (
    cohort_key            bigint primary key,
    cohort_definition_id  integer not null,
    cohort_definition_name varchar(255),
    valid_from            timestamp not null,
    valid_to              timestamp,
    is_current            boolean not null
);

-- ---------------------------------------------------------------------------
-- Facts
-- ---------------------------------------------------------------------------

-- Grain: one row per visit.
create table if not exists real_world_evidence_dim.fact_visit (
    visit_occurrence_id    bigint primary key,
    person_key             bigint not null references real_world_evidence_dim.dim_person(person_key),
    visit_concept_key      bigint not null references real_world_evidence_dim.dim_concept(concept_key),
    care_site_key          bigint references real_world_evidence_dim.dim_care_site(care_site_key),
    visit_start_date_key   integer not null references real_world_evidence_dim.dim_date(date_key),
    visit_end_date_key     integer references real_world_evidence_dim.dim_date(date_key),
    length_of_stay_days    integer,
    is_inpatient           boolean not null,
    is_emergency           boolean not null
);

-- Grain: one row per condition occurrence.
create table if not exists real_world_evidence_dim.fact_condition (
    condition_occurrence_id  bigint primary key,
    person_key               bigint not null references real_world_evidence_dim.dim_person(person_key),
    condition_concept_key    bigint not null references real_world_evidence_dim.dim_concept(concept_key),
    visit_occurrence_id      bigint references real_world_evidence_dim.fact_visit(visit_occurrence_id),
    condition_start_date_key integer not null references real_world_evidence_dim.dim_date(date_key),
    condition_end_date_key   integer references real_world_evidence_dim.dim_date(date_key),
    duration_days            integer,
    is_chronic               boolean not null
);

-- Grain: one row per drug exposure.
create table if not exists real_world_evidence_dim.fact_drug_exposure (
    drug_exposure_id    bigint primary key,
    person_key          bigint not null references real_world_evidence_dim.dim_person(person_key),
    drug_concept_key    bigint not null references real_world_evidence_dim.dim_concept(concept_key),
    visit_occurrence_id bigint references real_world_evidence_dim.fact_visit(visit_occurrence_id),
    start_date_key      integer not null references real_world_evidence_dim.dim_date(date_key),
    end_date_key        integer references real_world_evidence_dim.dim_date(date_key),
    days_supply         integer,
    quantity            numeric(18, 6),
    refills             integer,
    is_persistent       boolean not null default false
);

-- Grain: one row per cohort entry.
create table if not exists real_world_evidence_dim.fact_cohort_membership (
    cohort_key        bigint not null references real_world_evidence_dim.dim_cohort(cohort_key),
    person_key        bigint not null references real_world_evidence_dim.dim_person(person_key),
    entry_date_key    integer not null references real_world_evidence_dim.dim_date(date_key),
    exit_date_key     integer references real_world_evidence_dim.dim_date(date_key),
    follow_up_days    integer,
    primary key (cohort_key, person_key, entry_date_key)
);

-- Grain: person x measurement (lab) granular.
create table if not exists real_world_evidence_dim.fact_measurement (
    measurement_id        bigint primary key,
    person_key            bigint not null references real_world_evidence_dim.dim_person(person_key),
    measurement_concept_key bigint not null references real_world_evidence_dim.dim_concept(concept_key),
    visit_occurrence_id   bigint references real_world_evidence_dim.fact_visit(visit_occurrence_id),
    measurement_date_key  integer not null references real_world_evidence_dim.dim_date(date_key),
    value_as_number       numeric(18, 6),
    is_abnormal           boolean
);

-- Grain: cohort x measurement summary (cube-ready).
create table if not exists real_world_evidence_dim.fact_outcome_summary (
    cohort_key        bigint not null references real_world_evidence_dim.dim_cohort(cohort_key),
    outcome_concept_key bigint not null references real_world_evidence_dim.dim_concept(concept_key),
    snapshot_date_key integer not null references real_world_evidence_dim.dim_date(date_key),
    person_count      integer not null,
    outcome_count     integer not null,
    incidence_rate    numeric(12, 6),
    primary key (cohort_key, outcome_concept_key, snapshot_date_key)
);
