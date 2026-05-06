-- =============================================================================
-- Domain Explorer — Postgres schema (illustrative)
--
-- This file is *generated* (and hand-curated) from the 3NF DDLs under
-- ``modeling/ddl/<subdomain>_3nf.sql``. It is a reference for what the
-- physical Postgres landing zones look like — not an exact mirror of the
-- denormalised tables that ``synthetic-data/load_to_postgres.py`` actually
-- creates from CSV.
--
-- Two sets of schemas:
--   1. Runtime schemas (one per anchor subdomain) — these get populated by
--      ``load_to_postgres.py`` from the generated CSVs. Tables are created
--      automatically by pandas.to_sql, so this file just declares the
--      schemas for them.
--   2. 3NF schemas (suffixed ``_3nf``) — full reference DDL for the
--      normalised landing zones. Run these if you want a richer schema to
--      target with custom ETL.
--
--   psql "$DATABASE_URL" -f synthetic-data/postgres_schema.sql
-- =============================================================================

-- ---------------------------------------------------------------------------
-- 1. Runtime schemas (one per anchor; populated from CSVs by load_to_postgres.py)
-- ---------------------------------------------------------------------------

CREATE SCHEMA IF NOT EXISTS payments;
CREATE SCHEMA IF NOT EXISTS p_and_c_claims;
CREATE SCHEMA IF NOT EXISTS merchandising;
CREATE SCHEMA IF NOT EXISTS demand_planning;
CREATE SCHEMA IF NOT EXISTS hotel_revenue_management;
CREATE SCHEMA IF NOT EXISTS mes_quality;
CREATE SCHEMA IF NOT EXISTS pharmacovigilance;


-- ---------------------------------------------------------------------------
-- 2. 3NF reference schemas (suffix _3nf)
-- ---------------------------------------------------------------------------

-- =============================================================================
-- Payments — 3NF schema (excerpt)
-- =============================================================================

create schema if not exists payments_3nf;

create table if not exists payments_3nf.merchant (
    merchant_id      varchar primary key,
    legal_name       varchar not null,
    mcc              varchar(4),
    country_iso2     varchar(2),
    onboarded_at     timestamp not null,
    is_active        boolean not null default true
);

create table if not exists payments_3nf.card_token (
    token_id         varchar primary key,
    masked_pan       varchar(19) not null,
    bin              varchar(8) not null,
    last4            varchar(4) not null,
    network          varchar(16) not null,
    issuer_country   varchar(2)
);

create table if not exists payments_3nf.transaction (
    transaction_id   varchar primary key,
    merchant_id      varchar not null references payments_3nf.merchant(merchant_id),
    token_id         varchar references payments_3nf.card_token(token_id),
    rail             varchar(16) not null,
    amount_minor     bigint not null,
    currency         varchar(3) not null,
    initiated_at     timestamp not null,
    status           varchar(16) not null
);

create table if not exists payments_3nf.authorization (
    auth_id          varchar primary key,
    transaction_id   varchar not null references payments_3nf.transaction(transaction_id),
    response_code    varchar(8) not null,
    approved         boolean not null,
    auth_ts          timestamp not null
);

create table if not exists payments_3nf.settlement (
    settlement_id    varchar primary key,
    transaction_id   varchar not null references payments_3nf.transaction(transaction_id),
    settled_amount_minor bigint not null,
    settled_at       timestamp not null,
    interchange_minor bigint
);

create table if not exists payments_3nf.dispute (
    dispute_id       varchar primary key,
    transaction_id   varchar not null references payments_3nf.transaction(transaction_id),
    reason_code      varchar(16) not null,
    opened_at        timestamp not null,
    resolved_at      timestamp,
    outcome          varchar(16)
);


-- =============================================================================
-- P&C Claims — 3NF schema (excerpt)
-- =============================================================================

create schema if not exists p_and_c_claims_3nf;

create table if not exists p_and_c_claims_3nf.policy (
    policy_id            varchar primary key,
    policyholder_id      varchar not null,
    product_code         varchar(16) not null,
    effective_date       date not null,
    expiration_date      date not null,
    premium_amount       numeric(14, 2) not null,
    state_iso            varchar(2) not null,
    is_active            boolean not null default true
);

create table if not exists p_and_c_claims_3nf.claim (
    claim_id             varchar primary key,
    policy_id            varchar not null references p_and_c_claims_3nf.policy(policy_id),
    fnol_ts              timestamp not null,
    loss_date            date not null,
    loss_type            varchar(32) not null,
    loss_state_iso       varchar(2) not null,
    severity             varchar(16) not null,
    status               varchar(16) not null,
    closed_ts            timestamp
);

create table if not exists p_and_c_claims_3nf.payout (
    payout_id            varchar primary key,
    claim_id             varchar not null references p_and_c_claims_3nf.claim(claim_id),
    payee_party_id       varchar not null,
    payment_method       varchar(16) not null,
    amount               numeric(14, 2) not null,
    issued_ts            timestamp not null,
    cleared_ts           timestamp
);


-- =============================================================================
-- Merchandising — 3NF schema (excerpt)
-- =============================================================================

create schema if not exists merchandising_3nf;

create table if not exists merchandising_3nf.sku (
    sku_id               varchar primary key,
    style_id             varchar not null,
    description          varchar,
    is_active            boolean not null default true
);

create table if not exists merchandising_3nf.store (
    store_id             varchar primary key,
    store_name           varchar not null,
    region_code          varchar(8) not null,
    open_date            date not null
);

create table if not exists merchandising_3nf.sales_transaction (
    tx_id                varchar primary key,
    store_id             varchar not null references merchandising_3nf.store(store_id),
    tx_ts                timestamp not null,
    customer_id          varchar,
    payment_method       varchar(16) not null,
    total_amount         numeric(12, 2) not null
);

create table if not exists merchandising_3nf.sales_line (
    tx_id                varchar not null references merchandising_3nf.sales_transaction(tx_id),
    line_no              smallint not null,
    sku_id               varchar not null references merchandising_3nf.sku(sku_id),
    quantity             integer not null,
    unit_price           numeric(10, 2) not null,
    discount_amount      numeric(10, 2) not null default 0,
    primary key (tx_id, line_no)
);


-- =============================================================================
-- Demand Planning — 3NF schema (excerpt)
-- =============================================================================

create schema if not exists demand_planning_3nf;

create table if not exists demand_planning_3nf.product (
    product_id           varchar primary key,
    product_name         varchar not null,
    category_id          varchar not null,
    uom                  varchar(8) not null,
    is_active            boolean not null default true
);

create table if not exists demand_planning_3nf.location (
    location_id          varchar primary key,
    location_name        varchar not null,
    location_type        varchar(16) not null,
    region_code          varchar(8) not null
);

create table if not exists demand_planning_3nf.statistical_forecast (
    forecast_run_id      varchar not null,
    product_id           varchar not null references demand_planning_3nf.product(product_id),
    location_id          varchar not null references demand_planning_3nf.location(location_id),
    period_id            varchar not null,
    forecast_qty         numeric(14, 2) not null,
    model_code           varchar(16) not null,
    generated_at         timestamp not null,
    primary key (forecast_run_id, product_id, location_id, period_id)
);


-- =============================================================================
-- Hotel Revenue Management — 3NF schema (excerpt)
-- =============================================================================

create schema if not exists hotel_revenue_management_3nf;

create table if not exists hotel_revenue_management_3nf.property (
    property_id          varchar primary key,
    property_name        varchar not null,
    chain_code           varchar(8),
    city                 varchar not null,
    country_iso2         varchar(2) not null,
    timezone             varchar(64) not null,
    total_rooms          integer not null
);

create table if not exists hotel_revenue_management_3nf.reservation (
    reservation_id       varchar primary key,
    property_id          varchar not null references hotel_revenue_management_3nf.property(property_id),
    arrival_date         date not null,
    departure_date       date not null,
    booking_ts           timestamp not null,
    cancelled_ts         timestamp,
    booking_status       varchar(16) not null,
    total_amount         numeric(12, 2) not null,
    currency             varchar(3) not null
);

create table if not exists hotel_revenue_management_3nf.inventory_balance (
    property_id          varchar not null references hotel_revenue_management_3nf.property(property_id),
    room_type_code       varchar(16) not null,
    stay_date            date not null,
    rooms_available      integer not null,
    rooms_held           integer not null,
    rooms_sold           integer not null,
    overbooking_limit    smallint not null default 0,
    primary key (property_id, room_type_code, stay_date)
);


-- =============================================================================
-- MES & Quality — 3NF schema (excerpt)
-- =============================================================================

create schema if not exists mes_quality_3nf;

create table if not exists mes_quality_3nf.plant (
    plant_id             varchar primary key,
    plant_name           varchar not null,
    country_iso2         varchar(2) not null,
    timezone             varchar(64) not null
);

create table if not exists mes_quality_3nf.work_order (
    wo_id                varchar primary key,
    plant_id             varchar not null references mes_quality_3nf.plant(plant_id),
    planned_qty          integer not null,
    actual_qty           integer,
    planned_start        timestamp not null,
    actual_start         timestamp,
    actual_end           timestamp,
    status               varchar(16) not null
);

create table if not exists mes_quality_3nf.sensor_reading (
    tag                  varchar not null,
    ts                   timestamp not null,
    value                numeric(14, 4) not null,
    quality_code         smallint not null,
    primary key (tag, ts)
);


-- =============================================================================
-- Pharmacovigilance — 3NF schema (excerpt)
-- =============================================================================

create schema if not exists pharmacovigilance_3nf;

create table if not exists pharmacovigilance_3nf.product (
    product_id           varchar primary key,
    brand_name           varchar not null,
    inn                  varchar not null,
    atc_code             varchar(8),
    therapeutic_area     varchar(64),
    is_marketed          boolean not null default true
);

create table if not exists pharmacovigilance_3nf.icsr (
    icsr_id              varchar primary key,
    case_version         smallint not null,
    case_state           varchar(16) not null,
    seriousness          varchar(16) not null,
    expectedness         varchar(16),
    causality            varchar(16),
    intake_country       varchar(2),
    closed_at            timestamp
);

create table if not exists pharmacovigilance_3nf.signal_record (
    signal_id            varchar primary key,
    product_id           varchar not null references pharmacovigilance_3nf.product(product_id),
    pt_code              varchar(16) not null,
    detected_at          timestamp not null,
    detection_method     varchar(32) not null,
    disproportionality   numeric(8, 4),
    status               varchar(16) not null
);

-- end of file
