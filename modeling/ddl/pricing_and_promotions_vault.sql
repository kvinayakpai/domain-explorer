-- =============================================================================
-- Pricing & Promotions — Data Vault 2.0 schema
-- Hubs (business keys) + Links (relationships) + Satellites (descriptive,
-- insert-only, time-stamped). Mirrors the EDI 832/879/880 + retail-pricing
-- source contract across Revionics, PROS, Blue Yonder, Oracle RPCS, and
-- vendor competitive feeds (Wiser / Numerator / NielsenIQ).
-- =============================================================================

create schema if not exists pricing_and_promotions_vault;

-- ---------- HUBS ----------
create table if not exists pricing_and_promotions_vault.h_product (
    hk_product     varchar(32) primary key,            -- MD5(product_id)
    product_id     varchar(32) unique,
    gtin           varchar(14),
    load_dts       timestamp,
    record_source  varchar(64)
);

create table if not exists pricing_and_promotions_vault.h_store (
    hk_store       varchar(32) primary key,
    store_id       varchar(16) unique,
    load_dts       timestamp,
    record_source  varchar(64)
);

create table if not exists pricing_and_promotions_vault.h_promo (
    hk_promo       varchar(32) primary key,
    promo_id       varchar(32) unique,
    load_dts       timestamp,
    record_source  varchar(64)
);

create table if not exists pricing_and_promotions_vault.h_markdown (
    hk_markdown    varchar(32) primary key,
    markdown_id    varchar(32) unique,
    load_dts       timestamp,
    record_source  varchar(64)
);

create table if not exists pricing_and_promotions_vault.h_competitor (
    hk_competitor  varchar(32) primary key,
    competitor_id  varchar(16) unique,
    load_dts       timestamp,
    record_source  varchar(64)
);

-- ---------- LINKS ----------
create table if not exists pricing_and_promotions_vault.l_product_store_price (
    hk_link        varchar(32) primary key,
    hk_product     varchar(32) references pricing_and_promotions_vault.h_product(hk_product),
    hk_store       varchar(32) references pricing_and_promotions_vault.h_store(hk_store),
    price_id       varchar(32),
    effective_from timestamp,
    load_dts       timestamp,
    record_source  varchar(64)
);

create table if not exists pricing_and_promotions_vault.l_product_promo (
    hk_link        varchar(32) primary key,
    hk_product     varchar(32) references pricing_and_promotions_vault.h_product(hk_product),
    hk_promo       varchar(32) references pricing_and_promotions_vault.h_promo(hk_promo),
    hk_store       varchar(32) references pricing_and_promotions_vault.h_store(hk_store),
    promo_line_id  varchar(32),
    load_dts       timestamp,
    record_source  varchar(64)
);

create table if not exists pricing_and_promotions_vault.l_product_store_markdown (
    hk_link        varchar(32) primary key,
    hk_product     varchar(32) references pricing_and_promotions_vault.h_product(hk_product),
    hk_store       varchar(32) references pricing_and_promotions_vault.h_store(hk_store),
    hk_markdown    varchar(32) references pricing_and_promotions_vault.h_markdown(hk_markdown),
    load_dts       timestamp,
    record_source  varchar(64)
);

create table if not exists pricing_and_promotions_vault.l_product_competitor (
    hk_link             varchar(32) primary key,
    hk_product          varchar(32) references pricing_and_promotions_vault.h_product(hk_product),
    hk_competitor       varchar(32) references pricing_and_promotions_vault.h_competitor(hk_competitor),
    competitive_price_id varchar(32),
    load_dts            timestamp,
    record_source       varchar(64)
);

-- ---------- SATELLITES ----------
create table if not exists pricing_and_promotions_vault.s_product_descriptive (
    hk_product        varchar(32) references pricing_and_promotions_vault.h_product(hk_product),
    load_dts          timestamp,
    name              varchar(255),
    brand             varchar(128),
    category_id       varchar(32),
    subcategory_id    varchar(32),
    lifecycle_stage   varchar(16),
    kvi_class         varchar(8),
    unit_cost         numeric(12,4),
    record_source     varchar(64),
    primary key (hk_product, load_dts)
);

create table if not exists pricing_and_promotions_vault.s_store_descriptive (
    hk_store          varchar(32) references pricing_and_promotions_vault.h_store(hk_store),
    load_dts          timestamp,
    store_name        varchar(255),
    banner            varchar(64),
    price_zone_id     varchar(16),
    pricing_strategy  varchar(16),
    region            varchar(64),
    country_iso2      varchar(2),
    format            varchar(32),
    status            varchar(16),
    record_source     varchar(64),
    primary key (hk_store, load_dts)
);

-- The mutable price history — insert-only by load_dts.
create table if not exists pricing_and_promotions_vault.s_price_history (
    hk_product               varchar(32) references pricing_and_promotions_vault.h_product(hk_product),
    hk_store                 varchar(32) references pricing_and_promotions_vault.h_store(hk_store),
    load_dts                 timestamp,
    price_type               varchar(16),
    amount                   numeric(12,4),
    currency                 varchar(3),
    effective_from           timestamp,
    effective_to             timestamp,
    source_system            varchar(32),
    prior_30day_low_minor    bigint,
    record_source            varchar(64),
    primary key (hk_product, hk_store, load_dts, price_type)
);

create table if not exists pricing_and_promotions_vault.s_promo_terms (
    hk_promo                  varchar(32) references pricing_and_promotions_vault.h_promo(hk_promo),
    load_dts                  timestamp,
    promo_name                varchar(255),
    mechanic                  varchar(32),
    discount_pct              numeric(5,4),
    discount_amount_minor     bigint,
    start_ts                  timestamp,
    end_ts                    timestamp,
    funding_source            varchar(16),
    trade_spend_minor         bigint,
    vendor_id                 varchar(32),
    status                    varchar(16),
    record_source             varchar(64),
    primary key (hk_promo, load_dts)
);

create table if not exists pricing_and_promotions_vault.s_markdown_reason (
    hk_markdown                 varchar(32) references pricing_and_promotions_vault.h_markdown(hk_markdown),
    load_dts                    timestamp,
    pre_price_minor             bigint,
    post_price_minor            bigint,
    markdown_depth_pct          numeric(6,4),
    reason_code                 varchar(16),
    optimizer                   varchar(32),
    planned_sell_through_pct    numeric(6,4),
    actual_sell_through_pct     numeric(6,4),
    triggered_at                timestamp,
    effective_from              timestamp,
    effective_to                timestamp,
    record_source               varchar(64),
    primary key (hk_markdown, load_dts)
);

create table if not exists pricing_and_promotions_vault.s_competitive_observation (
    hk_link                varchar(32) references pricing_and_promotions_vault.l_product_competitor(hk_link),
    load_dts               timestamp,
    channel                varchar(16),
    observed_price_minor   bigint,
    currency               varchar(3),
    on_promo               boolean,
    match_type             varchar(16),
    match_confidence       numeric(4,3),
    source                 varchar(32),
    observed_at            timestamp,
    record_source          varchar(64),
    primary key (hk_link, load_dts)
);
