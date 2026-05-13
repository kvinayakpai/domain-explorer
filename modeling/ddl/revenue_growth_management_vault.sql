-- =============================================================================
-- Revenue Growth Management — Data Vault 2.0 schema
-- Hubs (business keys) + Links (relationships) + Satellites (descriptive,
-- insert-only, time-stamped). Mirrors the SAP CCM / Vistex / Pricefx /
-- Model N source contract. Designed for the gross-to-net waterfall, mix
-- attribution, and price realization analytics layers.
-- =============================================================================

create schema if not exists revenue_growth_management_vault;

-- ---------- HUBS ----------
create table if not exists revenue_growth_management_vault.h_account (
    hk_account       varchar(32) primary key,         -- MD5(account_id)
    account_id       varchar(64) unique,
    load_dts         timestamp,
    record_source    varchar(64)
);

create table if not exists revenue_growth_management_vault.h_product (
    hk_product       varchar(32) primary key,         -- MD5(sku_id)
    sku_id           varchar(64) unique,
    load_dts         timestamp,
    record_source    varchar(64)
);

create table if not exists revenue_growth_management_vault.h_pack (
    hk_pack          varchar(32) primary key,
    pack_id          varchar(64) unique,
    load_dts         timestamp,
    record_source    varchar(64)
);

create table if not exists revenue_growth_management_vault.h_promo_plan (
    hk_promo_plan    varchar(32) primary key,
    promo_plan_id    varchar(64) unique,
    load_dts         timestamp,
    record_source    varchar(64)
);

create table if not exists revenue_growth_management_vault.h_deal (
    hk_deal          varchar(32) primary key,
    deal_id          varchar(64) unique,
    load_dts         timestamp,
    record_source    varchar(64)
);

create table if not exists revenue_growth_management_vault.h_price_list (
    hk_price_list    varchar(32) primary key,
    price_list_id    varchar(64) unique,
    load_dts         timestamp,
    record_source    varchar(64)
);

create table if not exists revenue_growth_management_vault.h_segment (
    hk_segment       varchar(32) primary key,
    segment_id       varchar(64) unique,
    load_dts         timestamp,
    record_source    varchar(64)
);

create table if not exists revenue_growth_management_vault.h_sales_txn (
    hk_sales_txn     varchar(32) primary key,
    transaction_id   varchar(64) unique,
    load_dts         timestamp,
    record_source    varchar(64)
);

-- ---------- LINKS ----------
create table if not exists revenue_growth_management_vault.l_pack_product (
    hk_link        varchar(32) primary key,
    hk_pack        varchar(32) references revenue_growth_management_vault.h_pack(hk_pack),
    hk_product     varchar(32) references revenue_growth_management_vault.h_product(hk_product),
    load_dts       timestamp,
    record_source  varchar(64)
);

create table if not exists revenue_growth_management_vault.l_account_pack_price (
    hk_link        varchar(32) primary key,
    hk_account     varchar(32) references revenue_growth_management_vault.h_account(hk_account),
    hk_pack        varchar(32) references revenue_growth_management_vault.h_pack(hk_pack),
    hk_price_list  varchar(32) references revenue_growth_management_vault.h_price_list(hk_price_list),
    load_dts       timestamp,
    record_source  varchar(64)
);

create table if not exists revenue_growth_management_vault.l_deal_plan (
    hk_link        varchar(32) primary key,
    hk_deal        varchar(32) references revenue_growth_management_vault.h_deal(hk_deal),
    hk_promo_plan  varchar(32) references revenue_growth_management_vault.h_promo_plan(hk_promo_plan),
    hk_account     varchar(32) references revenue_growth_management_vault.h_account(hk_account),
    hk_pack        varchar(32) references revenue_growth_management_vault.h_pack(hk_pack),
    load_dts       timestamp,
    record_source  varchar(64)
);

create table if not exists revenue_growth_management_vault.l_sales_attribution (
    hk_link        varchar(32) primary key,
    hk_sales_txn   varchar(32) references revenue_growth_management_vault.h_sales_txn(hk_sales_txn),
    hk_deal        varchar(32) references revenue_growth_management_vault.h_deal(hk_deal),
    hk_account     varchar(32) references revenue_growth_management_vault.h_account(hk_account),
    hk_pack        varchar(32) references revenue_growth_management_vault.h_pack(hk_pack),
    load_dts       timestamp,
    record_source  varchar(64)
);

-- ---------- SATELLITES ----------
create table if not exists revenue_growth_management_vault.s_account_descriptive (
    hk_account       varchar(32) references revenue_growth_management_vault.h_account(hk_account),
    load_dts         timestamp,
    account_name     varchar(255),
    channel          varchar(32),
    channel_tier     varchar(16),
    country_iso2     varchar(2),
    gln              varchar(13),
    status           varchar(16),
    record_source    varchar(64),
    primary key (hk_account, load_dts)
);

create table if not exists revenue_growth_management_vault.s_product_descriptive (
    hk_product       varchar(32) references revenue_growth_management_vault.h_product(hk_product),
    load_dts         timestamp,
    gtin             varchar(14),
    brand            varchar(64),
    sub_brand        varchar(64),
    category         varchar(64),
    subcategory      varchar(64),
    cogs_cents       bigint,
    lifecycle_stage  varchar(16),
    innovation_flag  boolean,
    status           varchar(16),
    record_source    varchar(64),
    primary key (hk_product, load_dts)
);

create table if not exists revenue_growth_management_vault.s_pack_descriptive (
    hk_pack                      varchar(32) references revenue_growth_management_vault.h_pack(hk_pack),
    load_dts                     timestamp,
    pack_name                    varchar(128),
    pack_size_count              smallint,
    pack_format                  varchar(32),
    ppa_tier                     varchar(16),
    ladder_rank                  smallint,
    benchmark_net_price_cents    bigint,
    benchmark_margin_cents       bigint,
    status                       varchar(16),
    record_source                varchar(64),
    primary key (hk_pack, load_dts)
);

create table if not exists revenue_growth_management_vault.s_price_history (
    hk_price_list    varchar(32) references revenue_growth_management_vault.h_price_list(hk_price_list),
    load_dts         timestamp,
    list_price_cents bigint,
    srp_cents        bigint,
    currency         varchar(3),
    effective_from   date,
    effective_to     date,
    source_system    varchar(32),
    status           varchar(16),
    record_source    varchar(64),
    primary key (hk_price_list, load_dts)
);

create table if not exists revenue_growth_management_vault.s_promo_plan_state (
    hk_promo_plan              varchar(32) references revenue_growth_management_vault.h_promo_plan(hk_promo_plan),
    load_dts                   timestamp,
    name                       varchar(255),
    brand                      varchar(64),
    fiscal_year                smallint,
    fiscal_quarter             smallint,
    planned_net_revenue_cents  bigint,
    planned_trade_spend_cents  bigint,
    planned_volume_units       bigint,
    forecast_roi               numeric(6,2),
    status                     varchar(16),
    record_source              varchar(64),
    primary key (hk_promo_plan, load_dts)
);

create table if not exists revenue_growth_management_vault.s_deal_econ (
    hk_deal                  varchar(32) references revenue_growth_management_vault.h_deal(hk_deal),
    load_dts                 timestamp,
    tactic_type              varchar(32),
    mechanic                 varchar(32),
    discount_per_unit_cents  bigint,
    rebate_pct               numeric(6,4),
    deal_floor_cents         bigint,
    planned_units            bigint,
    planned_spend_cents      bigint,
    actual_units             bigint,
    actual_spend_cents       bigint,
    forward_buy_cost_cents   bigint,
    start_date               date,
    end_date                 date,
    settlement_method        varchar(16),
    status                   varchar(16),
    record_source            varchar(64),
    primary key (hk_deal, load_dts)
);

create table if not exists revenue_growth_management_vault.s_sales_gtn (
    hk_sales_txn                varchar(32) references revenue_growth_management_vault.h_sales_txn(hk_sales_txn),
    load_dts                    timestamp,
    invoice_date                date,
    units                       bigint,
    gross_revenue_cents         bigint,
    off_invoice_cents           bigint,
    rebate_accrual_cents        bigint,
    scan_down_cents             bigint,
    bill_back_cents             bigint,
    mcb_cents                   bigint,
    slotting_cents              bigint,
    marketing_dev_funds_cents   bigint,
    net_revenue_cents           bigint,
    cogs_cents                  bigint,
    currency                    varchar(3),
    source_system               varchar(32),
    record_source               varchar(64),
    primary key (hk_sales_txn, load_dts)
);

create table if not exists revenue_growth_management_vault.s_baseline (
    hk_pack                       varchar(32) references revenue_growth_management_vault.h_pack(hk_pack),
    hk_account                    varchar(32) references revenue_growth_management_vault.h_account(hk_account),
    load_dts                      timestamp,
    week_start_date               date,
    baseline_units                bigint,
    baseline_net_revenue_cents    bigint,
    model_name                    varchar(64),
    model_version                 varchar(16),
    confidence_band_low_units     bigint,
    confidence_band_high_units    bigint,
    record_source                 varchar(64),
    primary key (hk_pack, hk_account, load_dts, week_start_date)
);

create table if not exists revenue_growth_management_vault.s_segment_target (
    hk_segment                          varchar(32) references revenue_growth_management_vault.h_segment(hk_segment),
    load_dts                            timestamp,
    channel                             varchar(32),
    ppa_tier                            varchar(16),
    category                            varchar(64),
    target_share_pct                    numeric(6,4),
    target_net_revenue_per_unit_cents   bigint,
    record_source                       varchar(64),
    primary key (hk_segment, load_dts)
);
