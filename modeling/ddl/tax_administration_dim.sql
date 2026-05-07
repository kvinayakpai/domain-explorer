-- =============================================================================
-- Tax Administration — dimensional mart
-- Star schema. Facts: filing_daily, refund, audit_outcome, lien_aging.
-- =============================================================================

create schema if not exists tax_administration_dim;

create table if not exists tax_administration_dim.dim_date (
    date_key      integer primary key,
    date_actual   date not null,
    day_of_week   smallint not null,
    iso_week      smallint not null,
    fiscal_period varchar(8)
);

create table if not exists tax_administration_dim.dim_taxpayer (
    taxpayer_key   bigint primary key,
    taxpayer_id    varchar not null,
    entity_type    varchar(16),
    filing_status  varchar(16),
    state_code     varchar(2),
    country_iso    varchar(2),
    valid_from     timestamp not null,
    valid_to       timestamp,
    is_current     boolean not null
);

create table if not exists tax_administration_dim.dim_form (
    form_key   smallint primary key,
    form_code  varchar(8) not null,
    form_name  varchar(64) not null,
    audience   varchar(16)
);

create table if not exists tax_administration_dim.dim_tax_year (
    tax_year_key smallint primary key,
    tax_year     smallint not null,
    is_current   boolean not null
);

create table if not exists tax_administration_dim.dim_state (
    state_key  smallint primary key,
    state_code varchar(2) not null,
    state_name varchar(64) not null,
    region     varchar(32)
);

create table if not exists tax_administration_dim.dim_audit_program (
    audit_program_key smallint primary key,
    selection_program varchar(32) not null,
    audit_type        varchar(16) not null
);

-- ---------------------------------------------------------------------------
-- Facts
-- ---------------------------------------------------------------------------

-- Grain: form_code x tax_year x state x date.
create table if not exists tax_administration_dim.fact_filing_daily (
    form_key            smallint not null references tax_administration_dim.dim_form(form_key),
    tax_year_key        smallint not null references tax_administration_dim.dim_tax_year(tax_year_key),
    state_key           smallint references tax_administration_dim.dim_state(state_key),
    submitted_date_key  integer not null references tax_administration_dim.dim_date(date_key),
    submitted_count     integer not null,
    accepted_count      integer not null,
    rejected_count      integer not null,
    amended_count       integer not null,
    total_tax           numeric(20, 2),
    total_refund        numeric(20, 2),
    primary key (form_key, tax_year_key, state_key, submitted_date_key)
);

-- Grain: one row per refund disbursement.
create table if not exists tax_administration_dim.fact_refund (
    refund_id          varchar primary key,
    taxpayer_key       bigint not null references tax_administration_dim.dim_taxpayer(taxpayer_key),
    form_key           smallint not null references tax_administration_dim.dim_form(form_key),
    tax_year_key       smallint not null references tax_administration_dim.dim_tax_year(tax_year_key),
    submitted_date_key integer not null references tax_administration_dim.dim_date(date_key),
    disbursed_date_key integer references tax_administration_dim.dim_date(date_key),
    refund_amount      numeric(15, 2) not null,
    cycle_days         integer,
    held_for_review    boolean not null default false,
    disbursement_method varchar(16)
);

-- Grain: one row per audit case closed.
create table if not exists tax_administration_dim.fact_audit_outcome (
    audit_case_id        varchar primary key,
    taxpayer_key         bigint not null references tax_administration_dim.dim_taxpayer(taxpayer_key),
    audit_program_key    smallint not null references tax_administration_dim.dim_audit_program(audit_program_key),
    tax_year_key         smallint not null references tax_administration_dim.dim_tax_year(tax_year_key),
    opened_date_key      integer not null references tax_administration_dim.dim_date(date_key),
    closed_date_key      integer references tax_administration_dim.dim_date(date_key),
    risk_score           numeric(6, 4),
    no_change            boolean not null,
    adjusted_tax_amount  numeric(15, 2)
);

-- Grain: one row per active lien per snapshot date.
create table if not exists tax_administration_dim.fact_lien_aging (
    lien_id          varchar not null,
    taxpayer_key     bigint not null references tax_administration_dim.dim_taxpayer(taxpayer_key),
    snapshot_date_key integer not null references tax_administration_dim.dim_date(date_key),
    lien_amount      numeric(15, 2) not null,
    age_days         integer not null,
    state_key        smallint references tax_administration_dim.dim_state(state_key),
    status           varchar(16) not null,
    primary key (lien_id, snapshot_date_key)
);

-- Grain: information return mismatch summary by tax_year x form.
create table if not exists tax_administration_dim.fact_aur_match (
    form_key           smallint not null references tax_administration_dim.dim_form(form_key),
    tax_year_key       smallint not null references tax_administration_dim.dim_tax_year(tax_year_key),
    info_returns_total integer not null,
    matched_count      integer not null,
    unmatched_count    integer not null,
    notice_issued_count integer not null,
    primary key (form_key, tax_year_key)
);
