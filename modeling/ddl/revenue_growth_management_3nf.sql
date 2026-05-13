-- =============================================================================
-- Revenue Growth Management — 3NF schema
-- Source standards (verbatim where the spec names a field):
--   GS1 GTIN-14 / GLN — product + location identification
--   ASC X12 EDI 832 — Price/Sales Catalog (list price exchange)
--     https://www.x12.org/products/transaction-sets
--   IFRS 15 — Revenue from Contracts with Customers
--     (variable consideration / gross-to-net accrual policy)
--     https://www.ifrs.org/issued-standards/list-of-standards/ifrs-15-revenue-from-contracts-with-customers/
--   SAP S/4HANA Revenue Management + Condition Contract Management (CCM)
--   Vistex Solutions for Revenue Optimization (price/rebate/deal record)
--   Pricefx PriceBuilder / PromotionManager / RebateManager
--   Model N Revenue Management Cloud (CPG channel incentive)
--   PROS RGM (Smart CPQ + RealPrice + Guidance) — B2B price guidance
--   Anaplan PM (Connected Planning for Pricing & Mix)
--   Periscope by McKinsey RGM Apps; BCG OS RGM Toolkit
--   Zilliant Price IQ / Deal Manager; Vendavo Profit Analyzer
--   Plytix PIM; Circana Unify / Liquid Data; NielsenIQ Connect
-- =============================================================================

create schema if not exists revenue_growth_management;

-- Retailer / customer headquarter — channel ladder anchor.
create table if not exists revenue_growth_management.account (
    account_id          varchar(32) primary key,
    account_name        varchar(255),
    parent_account_id   varchar(32),
    channel             varchar(32),                 -- grocery|mass|club|drug|convenience|dollar|ecom|food_service
    channel_tier        varchar(16),                  -- premium|mainstream|value
    country_iso2        varchar(2),
    gln                 varchar(13),                  -- GS1 GLN
    status              varchar(16),
    created_at          timestamp
);

-- Manufacturer brand × sub-brand × variant — merchandising key.
create table if not exists revenue_growth_management.product (
    sku_id              varchar(32) primary key,
    gtin                varchar(14) unique,           -- GS1 GTIN-14
    brand               varchar(64),
    sub_brand           varchar(64),
    category            varchar(64),
    subcategory         varchar(64),
    cogs_cents          bigint,
    launch_date         date,
    lifecycle_stage     varchar(16),                  -- intro|grow|core|decline|discontinued
    innovation_flag     boolean,                       -- launched in trailing 24 months
    status              varchar(16)
);

-- Price-pack architecture entity — the PPA ladder grain.
create table if not exists revenue_growth_management.pack (
    pack_id                       varchar(32) primary key,
    sku_id                        varchar(32) references revenue_growth_management.product(sku_id),
    pack_name                     varchar(128),
    pack_size_count               smallint,
    pack_format                   varchar(32),        -- can|bottle_pet|bottle_glass|carton|pouch|multipack|value_pack|super_pack
    ppa_tier                      varchar(16),        -- entry|mainstream|premium|value|super
    ladder_rank                   smallint,
    benchmark_net_price_cents     bigint,
    benchmark_margin_cents        bigint,
    launch_date                   date,
    status                        varchar(16)
);

-- List (wholesale) + recommended retail price per pack × account × effective window.
-- Bi-temporal: every change is an insert. Mirrors SAP CCM condition contract + Vistex price-list.
create table if not exists revenue_growth_management.price_list (
    price_list_id       varchar(40) primary key,
    account_id          varchar(32) references revenue_growth_management.account(account_id),
    pack_id             varchar(32) references revenue_growth_management.pack(pack_id),
    list_price_cents    bigint,
    srp_cents           bigint,
    currency            varchar(3),
    effective_from      date,
    effective_to        date,
    recorded_at         timestamp,                    -- bi-temporal warehouse landing time
    source_system       varchar(32),                   -- SAP_CCM|Vistex|Pricefx|Model_N|EDI_832|manual
    status              varchar(16)
);

-- Atomic list-price change events. Grain of the price-realization study.
create table if not exists revenue_growth_management.price_event (
    price_event_id          varchar(40) primary key,
    account_id              varchar(32) references revenue_growth_management.account(account_id),
    pack_id                 varchar(32) references revenue_growth_management.pack(pack_id),
    event_type              varchar(16),               -- list_increase|list_decrease|srp_change|cost_change|currency_revaluation
    prior_list_price_cents  bigint,
    new_list_price_cents    bigint,
    prior_srp_cents         bigint,
    new_srp_cents           bigint,
    currency                varchar(3),
    announced_at            timestamp,
    effective_from          date,
    source_system           varchar(32),
    approver_role           varchar(32)                 -- VP_RGM|RGM_Director|CCO
);

-- Strategic promo plan header.
create table if not exists revenue_growth_management.promo_plan (
    promo_plan_id              varchar(32) primary key,
    account_id                 varchar(32) references revenue_growth_management.account(account_id),
    name                       varchar(255),
    brand                      varchar(64),
    fiscal_year                smallint,
    fiscal_quarter             smallint,
    planned_net_revenue_cents  bigint,
    planned_trade_spend_cents  bigint,
    planned_volume_units       bigint,
    forecast_roi               numeric(6,2),
    status                     varchar(16),
    created_by                 varchar(64),
    created_at                 timestamp,
    approved_at                timestamp
);

-- Tactical deal under a promo_plan.
create table if not exists revenue_growth_management.deal (
    deal_id                    varchar(40) primary key,
    promo_plan_id              varchar(32) references revenue_growth_management.promo_plan(promo_plan_id),
    account_id                 varchar(32) references revenue_growth_management.account(account_id),
    pack_id                    varchar(32) references revenue_growth_management.pack(pack_id),
    tactic_type                varchar(32),             -- off_invoice|scan_down|bill_back|mcb|tpr|feature|display|multibuy|bogo|coupon|loyalty|edlp
    mechanic                   varchar(32),             -- pct_off|dollar_off|2_for_X|case_allowance|conditional_rebate
    discount_per_unit_cents    bigint,
    rebate_pct                 numeric(6,4),
    deal_floor_cents           bigint,
    planned_units              bigint,
    planned_spend_cents        bigint,
    actual_units               bigint,
    actual_spend_cents         bigint,
    forward_buy_cost_cents     bigint,
    start_date                 date,
    end_date                   date,
    settlement_method          varchar(16),             -- off_invoice|deduction|check|emc|edi820
    status                     varchar(16)
);

-- Statistical baseline (no-promo counterfactual).
create table if not exists revenue_growth_management.baseline (
    baseline_id                  varchar(40) primary key,
    account_id                   varchar(32) references revenue_growth_management.account(account_id),
    pack_id                      varchar(32) references revenue_growth_management.pack(pack_id),
    week_start_date              date,
    baseline_units               bigint,
    baseline_net_revenue_cents   bigint,
    model_name                   varchar(64),           -- circana_unify|niq_baseline|periscope_glm|inhouse_ml|pricefx_optimizer
    model_version                varchar(16),
    confidence_band_low_units    bigint,
    confidence_band_high_units   bigint,
    generated_at                 timestamp
);

-- Channel × tier × category segment for mix attribution.
create table if not exists revenue_growth_management.mix_segment (
    segment_id                          varchar(32) primary key,
    channel                             varchar(32),
    ppa_tier                            varchar(16),
    category                            varchar(64),
    target_share_pct                    numeric(6,4),
    target_net_revenue_per_unit_cents   bigint
);

-- Invoiced shipment fact at account × pack × day grain.
create table if not exists revenue_growth_management.sales_transaction (
    transaction_id              varchar(40) primary key,
    account_id                  varchar(32) references revenue_growth_management.account(account_id),
    pack_id                     varchar(32) references revenue_growth_management.pack(pack_id),
    deal_id                     varchar(40) references revenue_growth_management.deal(deal_id),
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
    source_system               varchar(32)
);

-- Helpful indexes on time and cardinality.
create index if not exists ix_rgm_price_list_pack_eff   on revenue_growth_management.price_list(pack_id, effective_from);
create index if not exists ix_rgm_price_event_pack_eff  on revenue_growth_management.price_event(pack_id, effective_from);
create index if not exists ix_rgm_deal_promo            on revenue_growth_management.deal(promo_plan_id);
create index if not exists ix_rgm_deal_account_pack     on revenue_growth_management.deal(account_id, pack_id);
create index if not exists ix_rgm_baseline_account_pack on revenue_growth_management.baseline(account_id, pack_id, week_start_date);
create index if not exists ix_rgm_sales_account_pack    on revenue_growth_management.sales_transaction(account_id, pack_id, invoice_date);
create index if not exists ix_rgm_sales_deal            on revenue_growth_management.sales_transaction(deal_id);
