-- =============================================================================
-- P&C Claims — dimensional mart (excerpt)
-- Star schema for claims analytics: leakage, severity, cycle time, loss triangles.
-- =============================================================================

create schema if not exists p_and_c_claims_dim;

create table if not exists p_and_c_claims_dim.dim_date (
    date_key             integer primary key,
    date_actual          date not null,
    day_of_week          smallint not null,
    fiscal_quarter       varchar(8),
    accident_year        smallint not null
);

create table if not exists p_and_c_claims_dim.dim_policy (
    policy_key           bigint primary key,
    policy_id            varchar not null,
    product_code         varchar(16) not null,
    state_iso            varchar(2) not null,
    effective_date       date not null,
    expiration_date      date not null,
    valid_from           timestamp not null,
    valid_to             timestamp,
    is_current           boolean not null
);

create table if not exists p_and_c_claims_dim.dim_policyholder (
    policyholder_key     bigint primary key,
    policyholder_id      varchar not null,
    legal_name           varchar not null,
    party_type           varchar(16) not null,
    state_iso            varchar(2),
    valid_from           timestamp not null,
    valid_to             timestamp,
    is_current           boolean not null
);

create table if not exists p_and_c_claims_dim.dim_loss_type (
    loss_type_key        smallint primary key,
    loss_type_code       varchar(16) not null,
    loss_type_name       varchar(64) not null,
    coverage_line        varchar(32) not null
);

create table if not exists p_and_c_claims_dim.dim_adjuster (
    adjuster_key         bigint primary key,
    adjuster_id          varchar not null,
    full_name            varchar not null,
    team                 varchar(32) not null,
    is_siu               boolean not null,
    license_state_iso    varchar(2) not null
);

create table if not exists p_and_c_claims_dim.dim_geography (
    geo_key              integer primary key,
    state_iso            varchar(2) not null,
    msa_code             varchar(8),
    zip_code             varchar(10),
    region               varchar(16)
);

create table if not exists p_and_c_claims_dim.dim_channel (
    channel_key          smallint primary key,
    channel_code         varchar(16) not null,
    channel_name         varchar(32) not null
);

create table if not exists p_and_c_claims_dim.dim_claim_status (
    status_key           smallint primary key,
    status_code          varchar(16) not null,
    status_name          varchar(32) not null,
    is_closed            boolean not null
);

create table if not exists p_and_c_claims_dim.fact_claim_event (
    claim_event_key      bigint primary key,
    claim_id             varchar not null,
    fnol_date_key        integer not null references p_and_c_claims_dim.dim_date(date_key),
    closed_date_key      integer references p_and_c_claims_dim.dim_date(date_key),
    policy_key           bigint not null references p_and_c_claims_dim.dim_policy(policy_key),
    policyholder_key     bigint not null references p_and_c_claims_dim.dim_policyholder(policyholder_key),
    loss_type_key        smallint not null references p_and_c_claims_dim.dim_loss_type(loss_type_key),
    adjuster_key         bigint references p_and_c_claims_dim.dim_adjuster(adjuster_key),
    geo_key              integer references p_and_c_claims_dim.dim_geography(geo_key),
    channel_key          smallint references p_and_c_claims_dim.dim_channel(channel_key),
    status_key           smallint not null references p_and_c_claims_dim.dim_claim_status(status_key),
    initial_reserve      numeric(14, 2) not null,
    current_reserve      numeric(14, 2) not null,
    paid_to_date         numeric(14, 2) not null,
    recovered_amount     numeric(14, 2) not null default 0,
    cycle_time_days      integer,
    leakage_amount       numeric(14, 2)
);

create table if not exists p_and_c_claims_dim.fact_claim_payment_daily (
    date_key             integer not null references p_and_c_claims_dim.dim_date(date_key),
    policy_key           bigint not null references p_and_c_claims_dim.dim_policy(policy_key),
    loss_type_key        smallint not null references p_and_c_claims_dim.dim_loss_type(loss_type_key),
    geo_key              integer not null references p_and_c_claims_dim.dim_geography(geo_key),
    payment_count        bigint not null,
    paid_amount          numeric(14, 2) not null,
    lae_amount           numeric(14, 2) not null,
    primary key (date_key, policy_key, loss_type_key, geo_key)
);

create table if not exists p_and_c_claims_dim.fact_loss_triangle (
    accident_year        smallint not null,
    development_period   smallint not null,
    loss_type_key        smallint not null references p_and_c_claims_dim.dim_loss_type(loss_type_key),
    paid_cumulative      numeric(14, 2) not null,
    incurred_cumulative  numeric(14, 2) not null,
    open_count           integer not null,
    primary key (accident_year, development_period, loss_type_key)
);
