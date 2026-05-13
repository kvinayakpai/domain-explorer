-- =============================================================================
-- Trade Promotion Management — 3NF schema
-- Source standards (verbatim where the spec names a field):
--   ASC X12 EDI 852 — Product Activity Data (POS movement, on-hand inventory)
--   ASC X12 EDI 867 — Product Transfer & Resale Report (sell-through to consumer)
--   ASC X12 EDI 810 — Invoice (off-invoice claim origin)
--   ASC X12 EDI 820 — Payment Order / Remittance (deduction settlement)
--     https://www.x12.org/products/transaction-sets
--   GS1 GTIN-14 / GLN — product + location identification.
--   SAP TPM (S/4HANA CRM Trade Promotion Management) — Promotion, Tactic, Funds.
--   Exceedra TPx, BluePlanner Live Trade Management, Anaplan TPM — model lineage.
--   IRI/Circana Unify, NielsenIQ Connect, Numerator Promo Insights — baseline /
--   syndicated POS / panel sources for lift_observation.
--   NRF AROTS — trade-promo data interchange profile.
--   ISO 8601 — date format for promo windows.
-- =============================================================================

create schema if not exists trade_promotion_management;

-- Retailer / customer hierarchy at headquarter level.
create table if not exists trade_promotion_management.account (
    account_id          varchar(32) primary key,
    account_name        varchar(255),
    parent_account_id   varchar(32),
    channel             varchar(32),                 -- grocery|mass|club|drug|convenience|dollar|ecom|food_service
    country_iso2        varchar(2),
    gln                 varchar(13),                  -- GS1 Global Location Number
    trade_terms_code    varchar(16),                  -- off-invoice/scan-down/mixed
    status              varchar(16),
    created_at          timestamp
);

-- Store-level outlet (one row per banner store).
create table if not exists trade_promotion_management.customer_outlet (
    outlet_id        varchar(32) primary key,
    account_id       varchar(32) references trade_promotion_management.account(account_id),
    store_number     varchar(16),
    gln              varchar(13),
    country_iso2     varchar(2),
    state_region     varchar(8),
    postal_code      varchar(16),
    format           varchar(32),                     -- supercenter|grocery|club|express|c-store
    lat              numeric(9,6),
    lng              numeric(9,6),
    opened_at        date,
    status           varchar(16)
);

-- Manufacturer SKU.
create table if not exists trade_promotion_management.product (
    sku_id              varchar(32) primary key,
    gtin                varchar(14) unique,           -- GS1 GTIN-14
    brand               varchar(64),
    sub_brand           varchar(64),
    category            varchar(64),
    subcategory         varchar(64),
    pack_size           varchar(32),
    case_pack_qty       smallint,
    list_price_cents    bigint,                       -- minor units
    srp_cents           bigint,
    cost_of_goods_cents bigint,
    launch_date         date,
    status              varchar(16)
);

-- A planned trade promotion at the account × brand × time window grain.
create table if not exists trade_promotion_management.promotion (
    promotion_id          varchar(32) primary key,
    account_id            varchar(32) references trade_promotion_management.account(account_id),
    name                  varchar(255),
    fiscal_year           smallint,
    fiscal_quarter        smallint,
    start_date            date,                       -- ISO 8601
    end_date              date,
    ship_start_date       date,
    ship_end_date         date,
    status                varchar(16),                 -- draft|approved|active|closed|cancelled
    planned_spend_cents   bigint,
    planned_volume_units  bigint,
    planned_lift_pct      numeric(5,2),
    forecast_roi          numeric(6,2),
    created_by            varchar(64),
    created_at            timestamp,
    approved_at           timestamp
);

-- One tactical execution under a promotion.
create table if not exists trade_promotion_management.promo_tactic (
    tactic_id                 varchar(32) primary key,
    promotion_id              varchar(32) references trade_promotion_management.promotion(promotion_id),
    sku_id                    varchar(32) references trade_promotion_management.product(sku_id),
    tactic_type               varchar(32),             -- off_invoice|scan_down|bill_back|mcb|edlp|trade_allowance|display|feature|tpr|coupon|bogo
    discount_per_unit_cents   bigint,
    consumer_price_cents      bigint,
    srp_cents                 bigint,
    planned_units             bigint,
    planned_spend_cents       bigint,
    actual_units              bigint,
    actual_spend_cents        bigint,
    lift_expected_pct         numeric(5,2),
    feature_type              varchar(16),             -- ad_block|insert|email|in_app|none
    display_type              varchar(16),             -- endcap|aisle_violator|pallet_drop|cooler|none
    tpr_only                  boolean,
    settlement_method         varchar(16)              -- off_invoice|deduction|check|emc|edi820
);

-- A retailer-issued chargeback claim against a manufacturer invoice.
create table if not exists trade_promotion_management.deduction (
    deduction_id              varchar(32) primary key,
    account_id                varchar(32) references trade_promotion_management.account(account_id),
    invoice_id                varchar(64),             -- EDI 810 origin
    claim_number              varchar(64),
    tactic_id                 varchar(32) references trade_promotion_management.promo_tactic(tactic_id),
    deduction_type            varchar(32),             -- promo|shortage|damages|pricing|compliance|slotting|mcb|other
    amount_cents              bigint,
    open_amount_cents         bigint,
    opened_date               date,
    aging_days                integer,
    status                    varchar(16),             -- open|matched|disputed|paid|written_off|chargeback_lost
    dispute_reason            varchar(64),
    resolution_date           date,
    validation_evidence_uri   text                      -- pointer to scan/photo evidence
);

-- Statistical baseline volume estimate per account × SKU × week.
create table if not exists trade_promotion_management.baseline_forecast (
    baseline_id            varchar(32) primary key,
    account_id             varchar(32) references trade_promotion_management.account(account_id),
    sku_id                 varchar(32) references trade_promotion_management.product(sku_id),
    week_start_date        date,
    baseline_units         bigint,
    baseline_dollars_cents bigint,
    model_name             varchar(64),                 -- circana_unify|niq_baseline|tpro_predictive|inhouse_glm
    model_version          varchar(16),
    confidence_band_low    bigint,
    confidence_band_high   bigint,
    generated_at           timestamp
);

-- Observed (post-event) incremental lift.
create table if not exists trade_promotion_management.lift_observation (
    lift_observation_id            varchar(32) primary key,
    tactic_id                      varchar(32) references trade_promotion_management.promo_tactic(tactic_id),
    account_id                     varchar(32) references trade_promotion_management.account(account_id),
    sku_id                         varchar(32) references trade_promotion_management.product(sku_id),
    week_start_date                date,
    actual_units                   bigint,
    baseline_units                 bigint,
    incremental_units              bigint,
    lift_pct                       numeric(6,2),
    cannibalization_units          bigint,
    halo_units                     bigint,
    incremental_gross_profit_cents bigint,
    actual_roi                     numeric(6,2),
    source                         varchar(32)          -- circana|niq|numerator|inhouse|retailer_scan
);

-- Weekly retailer POS scan and on-hand inventory feed (EDI 852/867).
create table if not exists trade_promotion_management.retailer_scan_data (
    scan_id                 varchar(40) primary key,
    account_id              varchar(32) references trade_promotion_management.account(account_id),
    outlet_id               varchar(32) references trade_promotion_management.customer_outlet(outlet_id),
    sku_id                  varchar(32) references trade_promotion_management.product(sku_id),
    gtin                    varchar(14),
    week_start_date         date,
    units_sold              bigint,
    dollars_sold_cents      bigint,
    avg_retail_price_cents  bigint,
    on_hand_units           integer,
    on_promo_flag           boolean,
    feature_flag            boolean,
    display_flag            boolean,
    tpr_flag                boolean,
    source_doc              varchar(8),                 -- EDI 852|EDI 867|niq|circana|numerator|first_party
    ingested_at             timestamp
);

-- Annual trade-spend fund pool by customer × brand × tactic-class.
create table if not exists trade_promotion_management.trade_fund (
    fund_id                varchar(32) primary key,
    account_id             varchar(32) references trade_promotion_management.account(account_id),
    brand                  varchar(64),
    fiscal_year            smallint,
    fund_type              varchar(16),                  -- accrual|lump_sum|pay_for_performance|mcb_pool
    planned_amount_cents   bigint,
    committed_amount_cents bigint,
    spent_amount_cents     bigint,
    balance_cents          bigint,
    status                 varchar(16)
);

-- Helpful indexes on time and cardinality.
create index if not exists ix_tpm_outlet_account     on trade_promotion_management.customer_outlet(account_id);
create index if not exists ix_tpm_promo_account      on trade_promotion_management.promotion(account_id);
create index if not exists ix_tpm_tactic_promo       on trade_promotion_management.promo_tactic(promotion_id);
create index if not exists ix_tpm_tactic_sku         on trade_promotion_management.promo_tactic(sku_id);
create index if not exists ix_tpm_ded_account        on trade_promotion_management.deduction(account_id);
create index if not exists ix_tpm_ded_tactic         on trade_promotion_management.deduction(tactic_id);
create index if not exists ix_tpm_baseline_week      on trade_promotion_management.baseline_forecast(week_start_date);
create index if not exists ix_tpm_lift_tactic        on trade_promotion_management.lift_observation(tactic_id);
create index if not exists ix_tpm_scan_week          on trade_promotion_management.retailer_scan_data(week_start_date);
create index if not exists ix_tpm_scan_account_sku   on trade_promotion_management.retailer_scan_data(account_id, sku_id);
create index if not exists ix_tpm_fund_account       on trade_promotion_management.trade_fund(account_id);
