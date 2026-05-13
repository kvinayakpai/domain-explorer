-- =============================================================================
-- Pricing & Promotions — 3NF schema
-- Source standards (verbatim where the spec names a field):
--   GS1 GTIN-14 — product key (https://www.gs1.org/standards/id-keys/gtin)
--   X12 EDI 832 — Price/Sales Catalog
--   X12 EDI 879 — Price Change
--   X12 EDI 880/881 — Grocery Promotion Announcement
--   EU Directive 2019/2161 (Omnibus) — prior 30-day low for promo claims
--   EU Directive 98/6/EC — unit price disclosure
--   FTC 16 CFR §233 — pricing accuracy
-- Vendor field hints map to: Revionics Lifecycle Pricing, PROS Pricing,
--   Blue Yonder Pricing & Promotion (formerly JDA), Oracle Retail Pricing
--   Cloud Service (RPCS), Eagle Eye AIR, NielsenIQ Discover, Numerator,
--   Wiser / Price2Spy / Skuuudle / DataWeave.
-- =============================================================================

create schema if not exists pricing_and_promotions;

-- Product master. GTIN-keyed where available, with KVI classification.
create table if not exists pricing_and_promotions.product (
    product_id         varchar(32) primary key,
    gtin               varchar(14),                          -- GS1 GTIN-14
    sku                varchar(32),
    name               varchar(255),
    brand              varchar(128),
    category_id        varchar(32),
    subcategory_id     varchar(32),
    lifecycle_stage    varchar(16),                          -- intro|grow|core|decline|clearance
    kvi_class          varchar(8),                           -- KVI|KVC|background|traffic|premium
    unit_cost          numeric(12,4),
    created_at         timestamp
);

-- Selling location. Stores roll up to price zones.
create table if not exists pricing_and_promotions.store (
    store_id          varchar(16) primary key,
    store_name        varchar(255),
    banner            varchar(64),
    price_zone_id     varchar(16),
    region            varchar(64),
    country_iso2      varchar(2),
    format            varchar(32),                           -- hypermarket|supermarket|convenience|specialty|ecom
    open_date         date,
    status            varchar(16)
);

-- Group of stores under a single regular-price policy.
create table if not exists pricing_and_promotions.price_zone (
    price_zone_id     varchar(16) primary key,
    zone_name         varchar(64),
    pricing_strategy  varchar(16),                           -- EDLP|hi-lo|hybrid
    tier              varchar(16)                            -- premium|mainstream|value
);

-- Time-effective regular / promo / markdown / clearance prices.
-- Immutable history under EDI 879 conventions; resolution decided downstream.
create table if not exists pricing_and_promotions.price (
    price_id                 varchar(32) primary key,
    product_id               varchar(32) references pricing_and_promotions.product(product_id),
    store_id                 varchar(16) references pricing_and_promotions.store(store_id),
    price_zone_id            varchar(16) references pricing_and_promotions.price_zone(price_zone_id),
    price_type               varchar(16),                    -- regular|promo|markdown|clearance|cost
    amount                   numeric(12,4),
    currency                 varchar(3),
    effective_from           timestamp,
    effective_to             timestamp,
    source_system            varchar(32),                    -- RMS|RPCS|Revionics|PROS|BlueYonder|POS
    prior_30day_low_minor    bigint,                         -- EU Omnibus prior-30-day low
    status                   varchar(16)
);

-- Promo header.
create table if not exists pricing_and_promotions.promo (
    promo_id                 varchar(32) primary key,
    promo_name               varchar(255),
    mechanic                 varchar(32),                    -- pct_off|dollar_off|bogo|multibuy|tpr|loyalty|coupon
    discount_pct             numeric(5,4),
    discount_amount_minor    bigint,
    start_ts                 timestamp,
    end_ts                   timestamp,
    funding_source           varchar(16),                    -- retailer|vendor|jbp|coop
    trade_spend_minor        bigint,
    vendor_id                varchar(32),
    status                   varchar(16),                    -- planned|active|completed|cancelled
    created_at               timestamp
);

-- SKU-level participation in a promo.
create table if not exists pricing_and_promotions.promo_line (
    promo_line_id            varchar(32) primary key,
    promo_id                 varchar(32) references pricing_and_promotions.promo(promo_id),
    product_id               varchar(32) references pricing_and_promotions.product(product_id),
    store_id                 varchar(16) references pricing_and_promotions.store(store_id),
    planned_baseline_units   integer,
    planned_lift_pct         numeric(6,4),
    planned_funding_minor    bigint,
    actual_units             integer,
    actual_funding_minor     bigint,
    cannibalization_flag     boolean
);

-- Lifecycle markdown event. Reason-coded; optimizer-attributed.
create table if not exists pricing_and_promotions.markdown (
    markdown_id                 varchar(32) primary key,
    product_id                  varchar(32) references pricing_and_promotions.product(product_id),
    store_id                    varchar(16) references pricing_and_promotions.store(store_id),
    pre_price_minor             bigint,
    post_price_minor            bigint,
    markdown_depth_pct          numeric(6,4),
    reason_code                 varchar(16),                 -- seasonal|excess_inventory|damage|defective|clearance|competitor
    optimizer                   varchar(32),                 -- Revionics|BlueYonder|PROS|Oracle_RPCS|manual
    triggered_at                timestamp,
    effective_from              timestamp,
    effective_to                timestamp,
    planned_sell_through_pct    numeric(6,4),
    actual_sell_through_pct     numeric(6,4)
);

-- Externally observed competitor price snapshot.
create table if not exists pricing_and_promotions.competitive_price (
    competitive_price_id    varchar(32) primary key,
    product_id              varchar(32) references pricing_and_promotions.product(product_id),
    competitor_id           varchar(16),
    competitor_name         varchar(128),
    channel                 varchar(16),                     -- in_store|web|app|marketplace
    observed_price_minor    bigint,
    currency                varchar(3),
    on_promo                boolean,
    match_type              varchar(16),                     -- exact_gtin|equivalent|like_for_like
    match_confidence        numeric(4,3),
    source                  varchar(32),                     -- Wiser|Price2Spy|Skuuudle|DataWeave|Numerator|NielsenIQ|manual
    observed_at             timestamp
);

-- Sales fact — POS receipts at SKU × store × day grain.
create table if not exists pricing_and_promotions.sales_fact (
    sales_id                 varchar(32) primary key,
    product_id               varchar(32) references pricing_and_promotions.product(product_id),
    store_id                 varchar(16) references pricing_and_promotions.store(store_id),
    sale_date                date,
    units_sold               integer,
    gross_revenue_minor      bigint,
    discount_minor           bigint,
    net_revenue_minor        bigint,
    cogs_minor               bigint,
    on_promo                 boolean,
    promo_id                 varchar(32),
    realized_price_minor     bigint
);

-- Per-cluster own- and cross-price elasticity estimates.
create table if not exists pricing_and_promotions.elasticity_estimate (
    estimate_id                    varchar(32) primary key,
    product_id                     varchar(32) references pricing_and_promotions.product(product_id),
    cluster_id                     varchar(16),
    own_price_elasticity           numeric(6,4),
    cross_price_elasticity_top1    numeric(6,4),
    cross_product_id_top1          varchar(32),
    confidence_interval_low        numeric(6,4),
    confidence_interval_high       numeric(6,4),
    model_version                  varchar(32),
    fit_window_start               date,
    fit_window_end                 date,
    estimated_at                   timestamp
);

-- Helpful indexes on time and cardinality.
create index if not exists ix_pp_price_product       on pricing_and_promotions.price(product_id);
create index if not exists ix_pp_price_store         on pricing_and_promotions.price(store_id);
create index if not exists ix_pp_price_effective     on pricing_and_promotions.price(effective_from, effective_to);
create index if not exists ix_pp_promoline_promo     on pricing_and_promotions.promo_line(promo_id);
create index if not exists ix_pp_promoline_product   on pricing_and_promotions.promo_line(product_id);
create index if not exists ix_pp_markdown_product    on pricing_and_promotions.markdown(product_id);
create index if not exists ix_pp_competitive_prod    on pricing_and_promotions.competitive_price(product_id);
create index if not exists ix_pp_competitive_obs     on pricing_and_promotions.competitive_price(observed_at);
create index if not exists ix_pp_sales_product_date  on pricing_and_promotions.sales_fact(product_id, sale_date);
create index if not exists ix_pp_elast_product       on pricing_and_promotions.elasticity_estimate(product_id);
