-- =============================================================================
-- Procurement & Spend Analytics — Kimball dimensional schema
-- Star: fct_purchase_orders, fct_invoices_psa, fct_supplier_risk,
--       fct_emissions_attribution, fct_savings
-- Conformed dims: dim_supplier, dim_contract, dim_category_taxonomy,
--                 dim_date_psa, dim_currency, dim_buying_channel
-- _psa suffix avoids collision with other anchors' dims/facts.
-- =============================================================================

create schema if not exists procurement_spend_analytics_dim;

-- ---------- DIMS ----------
create table if not exists procurement_spend_analytics_dim.dim_date_psa (
    date_key      integer primary key,                 -- yyyymmdd
    cal_date      date,
    day_of_week   smallint,
    day_name      varchar(12),
    month         smallint,
    month_name    varchar(12),
    quarter       smallint,
    year          smallint,
    fiscal_year   smallint,
    is_weekend    boolean,
    is_period_end boolean
);

create table if not exists procurement_spend_analytics_dim.dim_currency (
    currency_sk         bigint primary key,
    currency_code       varchar(3) unique,             -- ISO 4217
    currency_name       varchar(64),
    minor_unit          smallint,
    fx_rate_to_usd      numeric(18,8),
    fx_rate_as_of       date
);

create table if not exists procurement_spend_analytics_dim.dim_supplier (
    supplier_sk          bigint primary key,
    supplier_id          varchar(64) unique,
    duns_number          varchar(9),
    lei                  varchar(20),
    legal_name           varchar(255),
    parent_duns          varchar(9),
    country_iso2         varchar(2),
    region               varchar(32),
    industry_naics       varchar(6),
    diversity_flags      text,
    ecovadis_score       smallint,
    ecovadis_medal       varchar(8),
    cdp_climate_score    varchar(2),
    sbti_committed       boolean,
    paydex_score         smallint,
    failure_score        smallint,
    cyber_score          smallint,
    critical_flag        boolean,
    sanctions_flag       boolean,
    status               varchar(16),
    valid_from           timestamp,
    valid_to             timestamp,
    is_current           boolean
);

create table if not exists procurement_spend_analytics_dim.dim_category_taxonomy (
    category_sk          bigint primary key,
    category_code        varchar(8) unique,
    segment_code         varchar(2),
    family_code          varchar(4),
    class_code           varchar(6),
    commodity_code       varchar(8),
    segment_name         varchar(128),
    family_name          varchar(128),
    class_name           varchar(128),
    commodity_name       varchar(128),
    direct_or_indirect   varchar(8),
    capex_or_opex        varchar(5),
    scope3_category      smallint
);

create table if not exists procurement_spend_analytics_dim.dim_contract (
    contract_sk            bigint primary key,
    contract_id            varchar(64) unique,
    supplier_sk            bigint references procurement_spend_analytics_dim.dim_supplier(supplier_sk),
    contract_type          varchar(32),
    title                  varchar(255),
    effective_date         date,
    expiry_date            date,
    auto_renew             boolean,
    payment_terms          varchar(16),
    incoterms              varchar(8),
    rebate_pct             numeric(5,4),
    total_commit_amount    numeric(18,2),
    total_commit_currency  varchar(3),
    has_sustainability_clauses boolean,
    has_kpi_clauses        boolean,
    status                 varchar(16)
);

create table if not exists procurement_spend_analytics_dim.dim_buying_channel (
    channel_sk    bigint primary key,
    channel_code  varchar(16) unique,                  -- catalog|punchout|free_text|marketplace|pcard|auto
    channel_name  varchar(64),
    is_touchless_default boolean
);

-- ---------- FACTS ----------

-- One row per PO header — header-grain fact for spend cube, cycle time, touchless%.
create table if not exists procurement_spend_analytics_dim.fct_purchase_orders (
    po_id                   varchar(64) primary key,
    date_key                integer  references procurement_spend_analytics_dim.dim_date_psa(date_key),
    supplier_sk             bigint   references procurement_spend_analytics_dim.dim_supplier(supplier_sk),
    contract_sk             bigint   references procurement_spend_analytics_dim.dim_contract(contract_sk),
    category_sk             bigint   references procurement_spend_analytics_dim.dim_category_taxonomy(category_sk),
    channel_sk              bigint   references procurement_spend_analytics_dim.dim_buying_channel(channel_sk),
    currency_sk             bigint   references procurement_spend_analytics_dim.dim_currency(currency_sk),
    requisition_ts          timestamp,
    po_issued_ts            timestamp,
    cycle_time_hours        numeric(10,2),             -- po_issued_ts - requisition_ts
    total_amount            numeric(18,2),
    total_amount_base_usd   numeric(18,2),
    line_count              smallint,
    touchless               boolean,
    maverick_flag           boolean,
    payment_terms           varchar(16),
    status                  varchar(16)
);

-- One row per AP invoice — invoice grain for AP aging, match-rate, early-pay-discount%.
create table if not exists procurement_spend_analytics_dim.fct_invoices_psa (
    invoice_id                varchar(64) primary key,
    date_key                  integer  references procurement_spend_analytics_dim.dim_date_psa(date_key),
    supplier_sk               bigint   references procurement_spend_analytics_dim.dim_supplier(supplier_sk),
    contract_sk               bigint   references procurement_spend_analytics_dim.dim_contract(contract_sk),
    currency_sk               bigint   references procurement_spend_analytics_dim.dim_currency(currency_sk),
    invoice_date              date,
    due_date                  date,
    paid_ts                   timestamp,
    total_amount              numeric(18,2),
    total_amount_base_usd     numeric(18,2),
    tax_amount                numeric(18,2),
    match_type                varchar(8),
    matched                   boolean,
    early_pay_discount_taken  boolean,
    aging_days                smallint,
    paid_late_days            smallint,
    status                    varchar(16)
);

-- One row per supplier_risk_assessment — risk-trend mart.
create table if not exists procurement_spend_analytics_dim.fct_supplier_risk (
    assessment_id        varchar(64) primary key,
    date_key             integer references procurement_spend_analytics_dim.dim_date_psa(date_key),
    supplier_sk          bigint  references procurement_spend_analytics_dim.dim_supplier(supplier_sk),
    assessment_ts        timestamp,
    source               varchar(32),
    overall_score        numeric(5,2),
    financial_score      smallint,
    operational_score    smallint,
    geographic_score     smallint,
    cyber_score          smallint,
    compliance_score     smallint,
    sustainability_score smallint,
    tier                 varchar(8),
    is_critical_tier     boolean,
    delta_vs_prior       numeric(5,2)
);

-- One row per po_line — Scope 3 attribution mart at line grain.
create table if not exists procurement_spend_analytics_dim.fct_emissions_attribution (
    po_line_id              varchar(64) primary key,
    date_key                integer references procurement_spend_analytics_dim.dim_date_psa(date_key),
    supplier_sk             bigint  references procurement_spend_analytics_dim.dim_supplier(supplier_sk),
    category_sk             bigint  references procurement_spend_analytics_dim.dim_category_taxonomy(category_sk),
    currency_sk             bigint  references procurement_spend_analytics_dim.dim_currency(currency_sk),
    line_amount_base_usd    numeric(18,2),
    factor_source           varchar(32),               -- primary|activity|spend_based
    factor_vintage_year     smallint,
    scope3_kgco2e           numeric(18,4),
    kgco2e_per_usd          numeric(18,6),
    uncertainty_pct         numeric(5,2),
    scope3_category         smallint
);

-- One row per savings_event — savings ledger mart.
create table if not exists procurement_spend_analytics_dim.fct_savings (
    savings_event_id      varchar(64) primary key,
    date_key              integer references procurement_spend_analytics_dim.dim_date_psa(date_key),
    supplier_sk           bigint  references procurement_spend_analytics_dim.dim_supplier(supplier_sk),
    contract_sk           bigint  references procurement_spend_analytics_dim.dim_contract(contract_sk),
    category_sk           bigint  references procurement_spend_analytics_dim.dim_category_taxonomy(category_sk),
    event_type            varchar(16),
    savings_kind          varchar(8),
    committed_amount_usd  numeric(18,2),
    realized_amount_usd   numeric(18,2),
    realization_pct       numeric(5,4)
);

-- Indexes
create index if not exists ix_fct_po_supplier        on procurement_spend_analytics_dim.fct_purchase_orders(supplier_sk, date_key);
create index if not exists ix_fct_po_category        on procurement_spend_analytics_dim.fct_purchase_orders(category_sk);
create index if not exists ix_fct_inv_supplier       on procurement_spend_analytics_dim.fct_invoices_psa(supplier_sk, date_key);
create index if not exists ix_fct_risk_supplier      on procurement_spend_analytics_dim.fct_supplier_risk(supplier_sk, assessment_ts);
create index if not exists ix_fct_emiss_supplier     on procurement_spend_analytics_dim.fct_emissions_attribution(supplier_sk, date_key);
create index if not exists ix_fct_emiss_category     on procurement_spend_analytics_dim.fct_emissions_attribution(category_sk);
create index if not exists ix_fct_savings_supplier   on procurement_spend_analytics_dim.fct_savings(supplier_sk, date_key);
