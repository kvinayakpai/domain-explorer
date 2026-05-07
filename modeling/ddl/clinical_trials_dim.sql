-- =============================================================================
-- Clinical Trials — dimensional mart
-- Star schema. Facts: enrollment_daily, ae, query, visit, dbl_cycle.
-- =============================================================================

create schema if not exists clinical_trials_dim;

create table if not exists clinical_trials_dim.dim_date (
    date_key      integer primary key,
    date_actual   date not null,
    day_of_week   smallint not null,
    iso_week      smallint not null,
    fiscal_period varchar(8)
);

create table if not exists clinical_trials_dim.dim_study (
    study_key      bigint primary key,
    study_id       varchar not null,
    nct_number     varchar(11),
    phase          varchar(8),
    therapeutic_area varchar(64),
    sponsor_org    varchar(128),
    cro_org        varchar(128),
    valid_from     timestamp not null,
    valid_to       timestamp,
    is_current     boolean not null
);

create table if not exists clinical_trials_dim.dim_site (
    site_key       bigint primary key,
    site_id        varchar not null,
    site_number    varchar(16),
    name           varchar(255),
    country_iso    varchar(2),
    valid_from     timestamp not null,
    valid_to       timestamp,
    is_current     boolean not null
);

create table if not exists clinical_trials_dim.dim_subject (
    subject_key    bigint primary key,
    subject_id     varchar not null,
    arm_code       varchar(8),
    arm            varchar(64),
    sex            varchar(1),
    race_code      varchar(8),
    age_band       varchar(16),
    country_iso    varchar(2),
    valid_from     timestamp not null,
    valid_to       timestamp,
    is_current     boolean not null
);

create table if not exists clinical_trials_dim.dim_meddra (
    meddra_key     bigint primary key,
    pt_code        varchar(16) not null,
    pt_name        varchar(255),
    soc_code       varchar(16),
    soc_name       varchar(255),
    valid_from     timestamp not null,
    valid_to       timestamp,
    is_current     boolean not null
);

create table if not exists clinical_trials_dim.dim_severity (
    severity_key smallint primary key,
    severity_code varchar(8) not null,
    severity_label varchar(32) not null
);

create table if not exists clinical_trials_dim.dim_visit_type (
    visit_type_key smallint primary key,
    epoch          varchar(32) not null,
    visit_label    varchar(64) not null,
    is_milestone   boolean not null
);

-- ---------------------------------------------------------------------------
-- Facts
-- ---------------------------------------------------------------------------

-- Grain: study x site x day enrolment.
create table if not exists clinical_trials_dim.fact_enrollment_daily (
    study_key            bigint not null references clinical_trials_dim.dim_study(study_key),
    site_key             bigint not null references clinical_trials_dim.dim_site(site_key),
    date_key             integer not null references clinical_trials_dim.dim_date(date_key),
    screened_today       integer not null default 0,
    enrolled_today       integer not null default 0,
    randomized_today     integer not null default 0,
    cumulative_enrolled  integer not null,
    cumulative_target    integer not null,
    primary key (study_key, site_key, date_key)
);

-- Grain: one row per AE.
create table if not exists clinical_trials_dim.fact_adverse_event (
    ae_id            varchar primary key,
    subject_key      bigint not null references clinical_trials_dim.dim_subject(subject_key),
    study_key        bigint not null references clinical_trials_dim.dim_study(study_key),
    meddra_key       bigint references clinical_trials_dim.dim_meddra(meddra_key),
    severity_key     smallint references clinical_trials_dim.dim_severity(severity_key),
    onset_date_key   integer not null references clinical_trials_dim.dim_date(date_key),
    end_date_key     integer references clinical_trials_dim.dim_date(date_key),
    is_serious       boolean not null,
    is_related       boolean not null,
    duration_days    integer
);

-- Grain: one row per query.
create table if not exists clinical_trials_dim.fact_data_query (
    query_id         varchar primary key,
    subject_key      bigint not null references clinical_trials_dim.dim_subject(subject_key),
    study_key        bigint not null references clinical_trials_dim.dim_study(study_key),
    site_key         bigint references clinical_trials_dim.dim_site(site_key),
    opened_date_key  integer not null references clinical_trials_dim.dim_date(date_key),
    closed_date_key  integer references clinical_trials_dim.dim_date(date_key),
    resolution_days  integer,
    is_resolved      boolean not null
);

-- Grain: one row per visit.
create table if not exists clinical_trials_dim.fact_visit (
    visit_occurrence_id varchar primary key,
    subject_key         bigint not null references clinical_trials_dim.dim_subject(subject_key),
    study_key           bigint not null references clinical_trials_dim.dim_study(study_key),
    site_key            bigint references clinical_trials_dim.dim_site(site_key),
    visit_type_key      smallint not null references clinical_trials_dim.dim_visit_type(visit_type_key),
    planned_date_key    integer references clinical_trials_dim.dim_date(date_key),
    actual_date_key     integer references clinical_trials_dim.dim_date(date_key),
    out_of_window       boolean not null,
    completed           boolean not null
);

-- Grain: one row per database-lock event.
create table if not exists clinical_trials_dim.fact_database_lock (
    lock_id          varchar primary key,
    study_key        bigint not null references clinical_trials_dim.dim_study(study_key),
    lock_type        varchar(16) not null,
    locked_date_key  integer not null references clinical_trials_dim.dim_date(date_key),
    cutoff_date_key  integer references clinical_trials_dim.dim_date(date_key),
    cycle_days       integer
);
