-- =============================================================================
-- Trade Promotion Management — Kimball dimensional schema
-- Star: fct_promo_plans, fct_promo_performance_tpm, fct_deductions,
--       fct_baseline_volume, fct_retailer_scan
-- Conformed dims: dim_account_tpm, dim_product_tpm, dim_promotion, dim_tactic,
--                 dim_date_tpm, dim_outlet
-- (Suffix `_tpm` is used for dim_account / dim_product / dim_date / fct_promo_performance
--  to avoid collision with merchandising / demand_planning anchors that already
--  publish the unsuffixed names.)
-- =============================================================================

create schema if not exists trade_promotion_management_dim;

-- ---------- DIMS ----------
create table if not exists trade_promotion_management_dim.dim_date_tpm (
    date_key       integer primary key,        -- yyyymmdd
    cal_date       date,
    fiscal_year    smallint,
    fiscal_quarter smallint,
    fiscal_period  smallint,
    week_of_year   smallint,
    day_of_week    smallint,
    day_name       varchar(12),
    is_weekend     boolean,
    is_promo_eligible boolean
);

create table if not exists trade_promotion_management_dim.dim_account_tpm (
    account_sk        bigint primary key,
    account_id        varchar(32) unique,
    account_name      varchar(255),
    parent_account_id varchar(32),
    channel           varchar(32),
    country_iso2      varchar(2),
    gln               varchar(13),
    trade_terms_code  varchar(16),
    status            varchar(16),
    valid_from        timestamp,
    valid_to          timestamp,
    is_current        boolean
);

create table if not exists trade_promotion_management_dim.dim_outlet (
    outlet_sk     bigint primary key,
    outlet_id     varchar(32) unique,
    account_id    varchar(32),
    store_number  varchar(16),
    gln           varchar(13),
    state_region  varchar(8),
    postal_code   varchar(16),
    format        varchar(32),
    lat           numeric(9,6),
    lng           numeric(9,6),
    opened_at     date,
    status        varchar(16)
);

create table if not exists trade_promotion_management_dim.dim_product_tpm (
    product_sk          bigint primary key,
    sku_id              varchar(32) unique,
    gtin                varchar(14),
    brand               varchar(64),
    sub_brand           varchar(64),
    category            varchar(64),
    subcategory         varchar(64),
    pack_size           varchar(32),
    case_pack_qty       smallint,
    list_price_cents    bigint,
    srp_cents           bigint,
    cost_of_goods_cents bigint,
    launch_date         date,
    status              varchar(16)
);

create table if not exists trade_promotion_management_dim.dim_promotion (
    promotion_sk         bigint primary key,
    promotion_id         varchar(32) unique,
    account_id           varchar(32),
    name                 varchar(255),
    fiscal_year          smallint,
    fiscal_quarter       smallint,
    start_date           date,
    end_date             date,
    ship_start_date      date,
    ship_end_date        date,
    status               varchar(16),
    planned_spend_cents  bigint,
    planned_volume_units bigint,
    planned_lift_pct     numeric(5,2),
    forecast_roi         numeric(6,2)
);

create table if not exists trade_promotion_management_dim.dim_tactic (
    tactic_sk               bigint primary key,
    tactic_id               varchar(32) unique,
    promotion_id            varchar(32),
    sku_id                  varchar(32),
    tactic_type             varchar(32),
    discount_per_unit_cents bigint,
    consumer_price_cents    bigint,
    srp_cents               bigint,
    feature_type            varchar(16),
    display_type            varchar(16),
    tpr_only                boolean,
    settlement_method       varchar(16)
);

-- ---------- FACTS ----------
create table if not exists trade_promotion_management_dim.fct_promo_plans (
    plan_event_id        varchar(40) primary key,
    promotion_sk         bigint references trade_promotion_management_dim.dim_promotion(promotion_sk),
    tactic_sk            bigint references trade_promotion_management_dim.dim_tactic(tactic_sk),
    account_sk           bigint references trade_promotion_management_dim.dim_account_tpm(account_sk),
    product_sk           bigint references trade_promotion_management_dim.dim_product_tpm(product_sk),
    plan_date_key        integer references trade_promotion_management_dim.dim_date_tpm(date_key),
    start_date_key       integer references trade_promotion_management_dim.dim_date_tpm(date_key),
    end_date_key         integer references trade_promotion_management_dim.dim_date_tpm(date_key),
    planned_units        bigint,
    planned_spend_cents  bigint,
    planned_lift_pct     numeric(5,2),
    forecast_roi         numeric(6,2),
    plan_version         smallint
);

create table if not exists trade_promotion_management_dim.fct_promo_performance_tpm (
    perf_id                        varchar(40) primary key,
    tactic_sk                      bigint references trade_promotion_management_dim.dim_tactic(tactic_sk),
    promotion_sk                   bigint references trade_promotion_management_dim.dim_promotion(promotion_sk),
    account_sk                     bigint references trade_promotion_management_dim.dim_account_tpm(account_sk),
    product_sk                     bigint references trade_promotion_management_dim.dim_product_tpm(product_sk),
    week_date_key                  integer references trade_promotion_management_dim.dim_date_tpm(date_key),
    actual_units                   bigint,
    baseline_units                 bigint,
    incremental_units              bigint,
    lift_pct                       numeric(6,2),
    cannibalization_units          bigint,
    halo_units                     bigint,
    actual_spend_cents             bigint,
    incremental_gross_profit_cents bigint,
    actual_roi                     numeric(6,2),
    source                         varchar(32)
);

create table if not exists trade_promotion_management_dim.fct_deductions (
    deduction_id        varchar(32) primary key,
    account_sk          bigint references trade_promotion_management_dim.dim_account_tpm(account_sk),
    tactic_sk           bigint references trade_promotion_management_dim.dim_tactic(tactic_sk),
    opened_date_key     integer references trade_promotion_management_dim.dim_date_tpm(date_key),
    resolution_date_key integer references trade_promotion_management_dim.dim_date_tpm(date_key),
    deduction_type      varchar(32),
    amount_cents        bigint,
    open_amount_cents   bigint,
    aging_days          integer,
    status              varchar(16),
    is_disputed         boolean,
    is_paid             boolean,
    is_written_off      boolean,
    match_confidence    numeric(5,4)
);

create table if not exists trade_promotion_management_dim.fct_baseline_volume (
    baseline_id          varchar(32) primary key,
    account_sk           bigint references trade_promotion_management_dim.dim_account_tpm(account_sk),
    product_sk           bigint references trade_promotion_management_dim.dim_product_tpm(product_sk),
    week_date_key        integer references trade_promotion_management_dim.dim_date_tpm(date_key),
    baseline_units       bigint,
    baseline_dollars_cents bigint,
    confidence_band_low  bigint,
    confidence_band_high bigint,
    model_name           varchar(64),
    model_version        varchar(16)
);

create table if not exists trade_promotion_management_dim.fct_retailer_scan (
    scan_id                varchar(40) primary key,
    account_sk             bigint references trade_promotion_management_dim.dim_account_tpm(account_sk),
    outlet_sk              bigint references trade_promotion_management_dim.dim_outlet(outlet_sk),
    product_sk             bigint references trade_promotion_management_dim.dim_product_tpm(product_sk),
    week_date_key          integer references trade_promotion_management_dim.dim_date_tpm(date_key),
    units_sold             bigint,
    dollars_sold_cents     bigint,
    avg_retail_price_cents bigint,
    on_hand_units          integer,
    on_promo_flag          boolean,
    feature_flag           boolean,
    display_flag           boolean,
    tpr_flag               boolean,
    source_doc             varchar(8)
);

-- Helpful indexes
create index if not exists ix_tpm_perf_week     on trade_promotion_management_dim.fct_promo_performance_tpm(week_date_key);
create index if not exists ix_tpm_perf_account  on trade_promotion_management_dim.fct_promo_performance_tpm(account_sk);
create index if not exists ix_tpm_perf_tactic   on trade_promotion_management_dim.fct_promo_performance_tpm(tactic_sk);
create index if not exists ix_tpm_ded_status    on trade_promotion_management_dim.fct_deductions(status);
create index if not exists ix_tpm_scan_week     on trade_promotion_management_dim.fct_retailer_scan(week_date_key);
create index if not exists ix_tpm_scan_account  on trade_promotion_management_dim.fct_retailer_scan(account_sk);
