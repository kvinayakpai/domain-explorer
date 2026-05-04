-- =============================================================================
-- Payments — dimensional mart (excerpt)
-- Star schema for analytics consumption.
-- =============================================================================

create schema if not exists payments_dim;

create table if not exists payments_dim.dim_date (
    date_key         integer primary key,
    date_actual      date not null,
    day_of_week      smallint not null,
    fiscal_quarter   varchar(8)
);

create table if not exists payments_dim.dim_merchant (
    merchant_key     bigint primary key,
    merchant_id      varchar not null,
    legal_name       varchar not null,
    mcc              varchar(4),
    country_iso2     varchar(2),
    valid_from       timestamp not null,
    valid_to         timestamp,
    is_current       boolean not null
);

create table if not exists payments_dim.dim_rail (
    rail_key         smallint primary key,
    rail_code        varchar(16) not null,
    rail_name        varchar(64) not null
);

create table if not exists payments_dim.fact_payment_daily (
    date_key         integer not null references payments_dim.dim_date(date_key),
    merchant_key     bigint not null references payments_dim.dim_merchant(merchant_key),
    rail_key         smallint not null references payments_dim.dim_rail(rail_key),
    auth_count       bigint not null,
    approved_count   bigint not null,
    declined_count   bigint not null,
    total_amount     numeric(20, 2) not null,
    interchange_amt  numeric(20, 2) not null,
    primary key (date_key, merchant_key, rail_key)
);
