-- =============================================================================
-- Pricing & Promotions — Kimball dimensional schema
-- Star: fct_price_events, fct_promo_performance, fct_markdowns,
--       fct_competitive_observations
-- Conformed dims: dim_product_pricing, dim_store_pricing, dim_promo,
--                 dim_price_event_type, dim_date_pricing
-- Naming note: dimensions suffixed with `_pricing` to avoid collisions with
--   merchandising and other anchors that also publish dim_product / dim_store.
-- =============================================================================

create schema if not exists pricing_and_promotions_dim;

-- ---------- DIMS ----------
create table if not exists pricing_and_promotions_dim.dim_date_pricing (
    date_key       integer primary key,            -- yyyymmdd
    cal_date       date,
    day_of_week    smallint,
    day_name       varchar(12),
    month          smallint,
    month_name     varchar(12),
    quarter        smallint,
    year           smallint,
    iso_week       smallint,
    is_weekend     boolean,
    is_promo_week  boolean
);

create table if not exists pricing_and_promotions_dim.dim_product_pricing (
    product_sk         bigint primary key,
    product_id         varchar(32) unique,
    gtin               varchar(14),
    sku                varchar(32),
    brand              varchar(128),
    category_id        varchar(32),
    subcategory_id     varchar(32),
    lifecycle_stage    varchar(16),
    kvi_class          varchar(8),
    unit_cost          numeric(12,4),
    valid_from         timestamp,
    valid_to           timestamp,
    is_current         boolean
);

create table if not exists pricing_and_promotions_dim.dim_store_pricing (
    store_sk          bigint primary key,
    store_id          varchar(16) unique,
    store_name        varchar(255),
    banner            varchar(64),
    price_zone_id     varchar(16),
    zone_name         varchar(64),
    pricing_strategy  varchar(16),
    region            varchar(64),
    country_iso2      varchar(2),
    format            varchar(32),
    valid_from        timestamp,
    valid_to          timestamp,
    is_current        boolean
);

create table if not exists pricing_and_promotions_dim.dim_promo (
    promo_sk                 bigint primary key,
    promo_id                 varchar(32) unique,
    promo_name               varchar(255),
    mechanic                 varchar(32),
    discount_pct             numeric(5,4),
    discount_amount_minor    bigint,
    start_ts                 timestamp,
    end_ts                   timestamp,
    funding_source           varchar(16),
    vendor_id                varchar(32),
    status                   varchar(16)
);

create table if not exists pricing_and_promotions_dim.dim_price_event_type (
    price_event_type_sk    smallint primary key,
    price_type             varchar(16) unique,        -- regular|promo|markdown|clearance|cost
    is_promotional         boolean,
    is_markdown            boolean,
    description            varchar(255)
);

-- ---------- FACTS ----------
create table if not exists pricing_and_promotions_dim.fct_price_events (
    price_event_id          varchar(32) primary key,
    date_key                integer references pricing_and_promotions_dim.dim_date_pricing(date_key),
    product_sk              bigint references pricing_and_promotions_dim.dim_product_pricing(product_sk),
    store_sk                bigint references pricing_and_promotions_dim.dim_store_pricing(store_sk),
    price_event_type_sk     smallint references pricing_and_promotions_dim.dim_price_event_type(price_event_type_sk),
    amount_minor            bigint,
    currency                varchar(3),
    amount_usd              numeric(15,4),
    prior_30day_low_minor   bigint,
    effective_from          timestamp,
    effective_to            timestamp,
    is_promotional          boolean,
    is_markdown             boolean,
    source_system           varchar(32)
);

create table if not exists pricing_and_promotions_dim.fct_promo_performance (
    promo_line_id            varchar(32) primary key,
    date_key                 integer references pricing_and_promotions_dim.dim_date_pricing(date_key),
    promo_sk                 bigint references pricing_and_promotions_dim.dim_promo(promo_sk),
    product_sk               bigint references pricing_and_promotions_dim.dim_product_pricing(product_sk),
    store_sk                 bigint references pricing_and_promotions_dim.dim_store_pricing(store_sk),
    planned_baseline_units   integer,
    actual_units             integer,
    actual_lift_pct          numeric(6,4),
    planned_funding_minor    bigint,
    actual_funding_minor     bigint,
    incremental_margin_minor bigint,
    promo_roi                numeric(8,4),
    cannibalization_units    integer,
    halo_units               integer,
    is_cannibalized          boolean
);

create table if not exists pricing_and_promotions_dim.fct_markdowns (
    markdown_id                 varchar(32) primary key,
    date_key                    integer references pricing_and_promotions_dim.dim_date_pricing(date_key),
    product_sk                  bigint references pricing_and_promotions_dim.dim_product_pricing(product_sk),
    store_sk                    bigint references pricing_and_promotions_dim.dim_store_pricing(store_sk),
    pre_price_minor             bigint,
    post_price_minor            bigint,
    markdown_depth_pct          numeric(6,4),
    reason_code                 varchar(16),
    optimizer                   varchar(32),
    planned_sell_through_pct    numeric(6,4),
    actual_sell_through_pct     numeric(6,4),
    regret_factor_minor         bigint,                       -- counterfactual_optimal - realized
    triggered_at                timestamp
);

create table if not exists pricing_and_promotions_dim.fct_competitive_observations (
    competitive_obs_id     varchar(32) primary key,
    date_key               integer references pricing_and_promotions_dim.dim_date_pricing(date_key),
    product_sk             bigint references pricing_and_promotions_dim.dim_product_pricing(product_sk),
    competitor_id          varchar(16),
    competitor_name        varchar(128),
    channel                varchar(16),
    observed_price_minor   bigint,
    own_price_minor        bigint,
    cpi                    numeric(8,4),                      -- own / competitor
    on_promo               boolean,
    match_type             varchar(16),
    match_confidence       numeric(4,3),
    source                 varchar(32),
    observed_at            timestamp
);

-- Helpful indexes
create index if not exists ix_pp_fct_price_date     on pricing_and_promotions_dim.fct_price_events(date_key);
create index if not exists ix_pp_fct_price_product  on pricing_and_promotions_dim.fct_price_events(product_sk);
create index if not exists ix_pp_fct_promo_date     on pricing_and_promotions_dim.fct_promo_performance(date_key);
create index if not exists ix_pp_fct_md_product     on pricing_and_promotions_dim.fct_markdowns(product_sk);
create index if not exists ix_pp_fct_comp_product   on pricing_and_promotions_dim.fct_competitive_observations(product_sk);
create index if not exists ix_pp_fct_comp_date      on pricing_and_promotions_dim.fct_competitive_observations(date_key);
