-- =============================================================================
-- Trade Promotion Management — Data Vault 2.0 schema
-- Hubs (business keys) + Links (relationships) + Satellites (descriptive,
-- insert-only, time-stamped). Mirrors SAP TPM / Exceedra / BluePlanner /
-- retailer EDI 852/867 source contracts.
-- =============================================================================

create schema if not exists trade_promotion_management_vault;

-- ---------- HUBS ----------
create table if not exists trade_promotion_management_vault.h_account (
    hk_account     varchar(32) primary key,
    account_id     varchar(64) unique,
    load_dts       timestamp,
    record_source  varchar(64)
);

create table if not exists trade_promotion_management_vault.h_outlet (
    hk_outlet      varchar(32) primary key,
    outlet_id      varchar(64) unique,
    load_dts       timestamp,
    record_source  varchar(64)
);

create table if not exists trade_promotion_management_vault.h_product (
    hk_product     varchar(32) primary key,
    sku_id         varchar(64) unique,
    gtin           varchar(14),
    load_dts       timestamp,
    record_source  varchar(64)
);

create table if not exists trade_promotion_management_vault.h_promotion (
    hk_promotion   varchar(32) primary key,
    promotion_id   varchar(64) unique,
    load_dts       timestamp,
    record_source  varchar(64)
);

create table if not exists trade_promotion_management_vault.h_tactic (
    hk_tactic      varchar(32) primary key,
    tactic_id      varchar(64) unique,
    load_dts       timestamp,
    record_source  varchar(64)
);

create table if not exists trade_promotion_management_vault.h_deduction (
    hk_deduction   varchar(32) primary key,
    deduction_id   varchar(64) unique,
    load_dts       timestamp,
    record_source  varchar(64)
);

create table if not exists trade_promotion_management_vault.h_fund (
    hk_fund        varchar(32) primary key,
    fund_id        varchar(64) unique,
    load_dts       timestamp,
    record_source  varchar(64)
);

-- ---------- LINKS ----------
create table if not exists trade_promotion_management_vault.l_outlet_account (
    hk_link        varchar(32) primary key,
    hk_outlet      varchar(32) references trade_promotion_management_vault.h_outlet(hk_outlet),
    hk_account     varchar(32) references trade_promotion_management_vault.h_account(hk_account),
    load_dts       timestamp,
    record_source  varchar(64)
);

create table if not exists trade_promotion_management_vault.l_promotion_account (
    hk_link        varchar(32) primary key,
    hk_promotion   varchar(32) references trade_promotion_management_vault.h_promotion(hk_promotion),
    hk_account     varchar(32) references trade_promotion_management_vault.h_account(hk_account),
    load_dts       timestamp,
    record_source  varchar(64)
);

create table if not exists trade_promotion_management_vault.l_tactic_promotion (
    hk_link        varchar(32) primary key,
    hk_tactic      varchar(32) references trade_promotion_management_vault.h_tactic(hk_tactic),
    hk_promotion   varchar(32) references trade_promotion_management_vault.h_promotion(hk_promotion),
    hk_product     varchar(32) references trade_promotion_management_vault.h_product(hk_product),
    load_dts       timestamp,
    record_source  varchar(64)
);

create table if not exists trade_promotion_management_vault.l_deduction_tactic (
    hk_link        varchar(32) primary key,
    hk_deduction   varchar(32) references trade_promotion_management_vault.h_deduction(hk_deduction),
    hk_tactic      varchar(32) references trade_promotion_management_vault.h_tactic(hk_tactic),
    hk_account     varchar(32) references trade_promotion_management_vault.h_account(hk_account),
    match_confidence numeric(5,4),
    load_dts       timestamp,
    record_source  varchar(64)
);

create table if not exists trade_promotion_management_vault.l_scan_outlet_product (
    hk_link        varchar(32) primary key,
    hk_outlet      varchar(32) references trade_promotion_management_vault.h_outlet(hk_outlet),
    hk_product     varchar(32) references trade_promotion_management_vault.h_product(hk_product),
    week_start_date date,
    load_dts       timestamp,
    record_source  varchar(64)
);

create table if not exists trade_promotion_management_vault.l_fund_account (
    hk_link        varchar(32) primary key,
    hk_fund        varchar(32) references trade_promotion_management_vault.h_fund(hk_fund),
    hk_account     varchar(32) references trade_promotion_management_vault.h_account(hk_account),
    load_dts       timestamp,
    record_source  varchar(64)
);

-- ---------- SATELLITES ----------
create table if not exists trade_promotion_management_vault.s_account_descriptive (
    hk_account        varchar(32) references trade_promotion_management_vault.h_account(hk_account),
    load_dts          timestamp,
    account_name      varchar(255),
    parent_account_id varchar(32),
    channel           varchar(32),
    country_iso2      varchar(2),
    gln               varchar(13),
    trade_terms_code  varchar(16),
    status            varchar(16),
    record_source     varchar(64),
    primary key (hk_account, load_dts)
);

create table if not exists trade_promotion_management_vault.s_product_descriptive (
    hk_product        varchar(32) references trade_promotion_management_vault.h_product(hk_product),
    load_dts          timestamp,
    brand             varchar(64),
    sub_brand         varchar(64),
    category          varchar(64),
    subcategory       varchar(64),
    pack_size         varchar(32),
    case_pack_qty     smallint,
    list_price_cents  bigint,
    srp_cents         bigint,
    cost_of_goods_cents bigint,
    status            varchar(16),
    record_source     varchar(64),
    primary key (hk_product, load_dts)
);

create table if not exists trade_promotion_management_vault.s_promotion_state (
    hk_promotion         varchar(32) references trade_promotion_management_vault.h_promotion(hk_promotion),
    load_dts             timestamp,
    name                 varchar(255),
    fiscal_year          smallint,
    fiscal_quarter       smallint,
    start_date           date,
    end_date             date,
    status               varchar(16),
    planned_spend_cents  bigint,
    planned_volume_units bigint,
    planned_lift_pct     numeric(5,2),
    forecast_roi         numeric(6,2),
    record_source        varchar(64),
    primary key (hk_promotion, load_dts)
);

create table if not exists trade_promotion_management_vault.s_tactic_descriptive (
    hk_tactic              varchar(32) references trade_promotion_management_vault.h_tactic(hk_tactic),
    load_dts               timestamp,
    tactic_type            varchar(32),
    discount_per_unit_cents bigint,
    consumer_price_cents   bigint,
    srp_cents              bigint,
    planned_units          bigint,
    planned_spend_cents    bigint,
    actual_units           bigint,
    actual_spend_cents     bigint,
    lift_expected_pct      numeric(5,2),
    feature_type           varchar(16),
    display_type           varchar(16),
    tpr_only               boolean,
    settlement_method      varchar(16),
    record_source          varchar(64),
    primary key (hk_tactic, load_dts)
);

create table if not exists trade_promotion_management_vault.s_deduction_state (
    hk_deduction          varchar(32) references trade_promotion_management_vault.h_deduction(hk_deduction),
    load_dts              timestamp,
    invoice_id            varchar(64),
    claim_number          varchar(64),
    deduction_type        varchar(32),
    amount_cents          bigint,
    open_amount_cents     bigint,
    opened_date           date,
    aging_days            integer,
    status                varchar(16),
    dispute_reason        varchar(64),
    resolution_date       date,
    record_source         varchar(64),
    primary key (hk_deduction, load_dts)
);

create table if not exists trade_promotion_management_vault.s_baseline_forecast (
    hk_link                  varchar(32),                -- FK to a baseline-link if introduced; here the natural key is composite
    hk_account               varchar(32) references trade_promotion_management_vault.h_account(hk_account),
    hk_product               varchar(32) references trade_promotion_management_vault.h_product(hk_product),
    week_start_date          date,
    load_dts                 timestamp,
    baseline_units           bigint,
    baseline_dollars_cents   bigint,
    model_name               varchar(64),
    model_version            varchar(16),
    confidence_band_low      bigint,
    confidence_band_high     bigint,
    record_source            varchar(64),
    primary key (hk_account, hk_product, week_start_date, model_name, load_dts)
);

create table if not exists trade_promotion_management_vault.s_lift_observation (
    hk_tactic                      varchar(32) references trade_promotion_management_vault.h_tactic(hk_tactic),
    hk_account                     varchar(32) references trade_promotion_management_vault.h_account(hk_account),
    hk_product                     varchar(32) references trade_promotion_management_vault.h_product(hk_product),
    week_start_date                date,
    load_dts                       timestamp,
    actual_units                   bigint,
    baseline_units                 bigint,
    incremental_units              bigint,
    lift_pct                       numeric(6,2),
    cannibalization_units          bigint,
    halo_units                     bigint,
    incremental_gross_profit_cents bigint,
    actual_roi                     numeric(6,2),
    source                         varchar(32),
    record_source                  varchar(64),
    primary key (hk_tactic, hk_account, hk_product, week_start_date, load_dts)
);

create table if not exists trade_promotion_management_vault.s_scan_data (
    hk_outlet              varchar(32) references trade_promotion_management_vault.h_outlet(hk_outlet),
    hk_product             varchar(32) references trade_promotion_management_vault.h_product(hk_product),
    week_start_date        date,
    load_dts               timestamp,
    units_sold             bigint,
    dollars_sold_cents     bigint,
    avg_retail_price_cents bigint,
    on_hand_units          integer,
    on_promo_flag          boolean,
    feature_flag           boolean,
    display_flag           boolean,
    tpr_flag               boolean,
    source_doc             varchar(8),
    record_source          varchar(64),
    primary key (hk_outlet, hk_product, week_start_date, load_dts)
);

create table if not exists trade_promotion_management_vault.s_fund_state (
    hk_fund                varchar(32) references trade_promotion_management_vault.h_fund(hk_fund),
    load_dts               timestamp,
    brand                  varchar(64),
    fiscal_year            smallint,
    fund_type              varchar(16),
    planned_amount_cents   bigint,
    committed_amount_cents bigint,
    spent_amount_cents     bigint,
    balance_cents          bigint,
    status                 varchar(16),
    record_source          varchar(64),
    primary key (hk_fund, load_dts)
);
