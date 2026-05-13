-- =============================================================================
-- Procurement & Spend Analytics — Data Vault 2.0 schema
-- Hubs (business keys) + Links (relationships) + Satellites (descriptive,
-- insert-only, time-stamped). Mirrors source-system semantics from SAP Ariba,
-- Coupa, Jaggaer, Ivalua, GEP, Oracle Procurement, Workday Sourcing, Tradeshift,
-- Basware, EcoVadis, Sievo, Resilinc, D&B, BitSight, CDP.
-- =============================================================================

create schema if not exists procurement_spend_analytics_vault;

-- ---------- HUBS ----------
create table if not exists procurement_spend_analytics_vault.h_supplier (
    hk_supplier     varchar(32) primary key,           -- MD5(supplier_id)
    supplier_id     varchar(64) unique,
    duns_number     varchar(9),
    load_dts        timestamp,
    record_source   varchar(64)
);

create table if not exists procurement_spend_analytics_vault.h_category (
    hk_category     varchar(32) primary key,
    category_code   varchar(8) unique,
    load_dts        timestamp,
    record_source   varchar(64)
);

create table if not exists procurement_spend_analytics_vault.h_contract (
    hk_contract     varchar(32) primary key,
    contract_id     varchar(64) unique,
    load_dts        timestamp,
    record_source   varchar(64)
);

create table if not exists procurement_spend_analytics_vault.h_po (
    hk_po           varchar(32) primary key,
    po_id           varchar(64) unique,
    load_dts        timestamp,
    record_source   varchar(64)
);

create table if not exists procurement_spend_analytics_vault.h_po_line (
    hk_po_line      varchar(32) primary key,
    po_line_id      varchar(64) unique,
    load_dts        timestamp,
    record_source   varchar(64)
);

create table if not exists procurement_spend_analytics_vault.h_receipt (
    hk_receipt      varchar(32) primary key,
    receipt_id      varchar(64) unique,
    load_dts        timestamp,
    record_source   varchar(64)
);

create table if not exists procurement_spend_analytics_vault.h_invoice (
    hk_invoice      varchar(32) primary key,
    invoice_id      varchar(64) unique,
    load_dts        timestamp,
    record_source   varchar(64)
);

create table if not exists procurement_spend_analytics_vault.h_risk_assessment (
    hk_risk_assessment varchar(32) primary key,
    assessment_id      varchar(64) unique,
    load_dts           timestamp,
    record_source      varchar(64)
);

create table if not exists procurement_spend_analytics_vault.h_emissions_factor (
    hk_emissions_factor varchar(32) primary key,
    emissions_factor_id varchar(64) unique,
    load_dts            timestamp,
    record_source       varchar(64)
);

create table if not exists procurement_spend_analytics_vault.h_sustainability_attr (
    hk_sustainability_attr varchar(32) primary key,
    sustainability_attr_id varchar(64) unique,
    load_dts               timestamp,
    record_source          varchar(64)
);

create table if not exists procurement_spend_analytics_vault.h_savings_event (
    hk_savings_event   varchar(32) primary key,
    savings_event_id   varchar(64) unique,
    load_dts           timestamp,
    record_source      varchar(64)
);

-- ---------- LINKS ----------
create table if not exists procurement_spend_analytics_vault.l_contract_supplier (
    hk_link         varchar(32) primary key,
    hk_contract     varchar(32) references procurement_spend_analytics_vault.h_contract(hk_contract),
    hk_supplier     varchar(32) references procurement_spend_analytics_vault.h_supplier(hk_supplier),
    load_dts        timestamp,
    record_source   varchar(64)
);

create table if not exists procurement_spend_analytics_vault.l_po_supplier (
    hk_link         varchar(32) primary key,
    hk_po           varchar(32) references procurement_spend_analytics_vault.h_po(hk_po),
    hk_supplier     varchar(32) references procurement_spend_analytics_vault.h_supplier(hk_supplier),
    hk_contract     varchar(32) references procurement_spend_analytics_vault.h_contract(hk_contract),
    hk_category     varchar(32) references procurement_spend_analytics_vault.h_category(hk_category),
    load_dts        timestamp,
    record_source   varchar(64)
);

create table if not exists procurement_spend_analytics_vault.l_po_line_po (
    hk_link         varchar(32) primary key,
    hk_po_line      varchar(32) references procurement_spend_analytics_vault.h_po_line(hk_po_line),
    hk_po           varchar(32) references procurement_spend_analytics_vault.h_po(hk_po),
    hk_category     varchar(32) references procurement_spend_analytics_vault.h_category(hk_category),
    load_dts        timestamp,
    record_source   varchar(64)
);

create table if not exists procurement_spend_analytics_vault.l_receipt_po_line (
    hk_link         varchar(32) primary key,
    hk_receipt      varchar(32) references procurement_spend_analytics_vault.h_receipt(hk_receipt),
    hk_po           varchar(32) references procurement_spend_analytics_vault.h_po(hk_po),
    hk_po_line      varchar(32) references procurement_spend_analytics_vault.h_po_line(hk_po_line),
    load_dts        timestamp,
    record_source   varchar(64)
);

create table if not exists procurement_spend_analytics_vault.l_invoice_po (
    hk_link         varchar(32) primary key,
    hk_invoice      varchar(32) references procurement_spend_analytics_vault.h_invoice(hk_invoice),
    hk_po           varchar(32) references procurement_spend_analytics_vault.h_po(hk_po),
    hk_supplier     varchar(32) references procurement_spend_analytics_vault.h_supplier(hk_supplier),
    load_dts        timestamp,
    record_source   varchar(64)
);

create table if not exists procurement_spend_analytics_vault.l_risk_supplier (
    hk_link             varchar(32) primary key,
    hk_risk_assessment  varchar(32) references procurement_spend_analytics_vault.h_risk_assessment(hk_risk_assessment),
    hk_supplier         varchar(32) references procurement_spend_analytics_vault.h_supplier(hk_supplier),
    load_dts            timestamp,
    record_source       varchar(64)
);

create table if not exists procurement_spend_analytics_vault.l_sustainability_supplier (
    hk_link                 varchar(32) primary key,
    hk_sustainability_attr  varchar(32) references procurement_spend_analytics_vault.h_sustainability_attr(hk_sustainability_attr),
    hk_supplier             varchar(32) references procurement_spend_analytics_vault.h_supplier(hk_supplier),
    load_dts                timestamp,
    record_source           varchar(64)
);

create table if not exists procurement_spend_analytics_vault.l_emfactor_category (
    hk_link                 varchar(32) primary key,
    hk_emissions_factor     varchar(32) references procurement_spend_analytics_vault.h_emissions_factor(hk_emissions_factor),
    hk_category             varchar(32) references procurement_spend_analytics_vault.h_category(hk_category),
    load_dts                timestamp,
    record_source           varchar(64)
);

create table if not exists procurement_spend_analytics_vault.l_savings_supplier (
    hk_link             varchar(32) primary key,
    hk_savings_event    varchar(32) references procurement_spend_analytics_vault.h_savings_event(hk_savings_event),
    hk_supplier         varchar(32) references procurement_spend_analytics_vault.h_supplier(hk_supplier),
    hk_contract         varchar(32) references procurement_spend_analytics_vault.h_contract(hk_contract),
    hk_category         varchar(32) references procurement_spend_analytics_vault.h_category(hk_category),
    load_dts            timestamp,
    record_source       varchar(64)
);

-- ---------- SATELLITES ----------
create table if not exists procurement_spend_analytics_vault.s_supplier_descriptive (
    hk_supplier            varchar(32) references procurement_spend_analytics_vault.h_supplier(hk_supplier),
    load_dts               timestamp,
    legal_name             varchar(255),
    parent_duns            varchar(9),
    tax_id                 varchar(64),
    country_iso2           varchar(2),
    region                 varchar(32),
    industry_naics         varchar(6),
    industry_sic           varchar(4),
    diversity_flags        text,
    ecovadis_score         smallint,
    ecovadis_medal         varchar(8),
    cdp_climate_score      varchar(2),
    sbti_committed         boolean,
    paydex_score           smallint,
    failure_score          smallint,
    cyber_score            smallint,
    critical_flag          boolean,
    sanctions_flag         boolean,
    status                 varchar(16),
    record_source          varchar(64),
    primary key (hk_supplier, load_dts)
);

create table if not exists procurement_spend_analytics_vault.s_contract_descriptive (
    hk_contract              varchar(32) references procurement_spend_analytics_vault.h_contract(hk_contract),
    load_dts                 timestamp,
    contract_type            varchar(32),
    title                    varchar(255),
    effective_date           date,
    expiry_date              date,
    auto_renew               boolean,
    notice_period_days       smallint,
    total_commit_amount      numeric(18,2),
    total_commit_currency    varchar(3),
    payment_terms            varchar(16),
    incoterms                varchar(8),
    rebate_pct               numeric(5,4),
    sustainability_clauses   text,
    kpi_clauses              text,
    status                   varchar(16),
    record_source            varchar(64),
    primary key (hk_contract, load_dts)
);

create table if not exists procurement_spend_analytics_vault.s_po_state (
    hk_po                   varchar(32) references procurement_spend_analytics_vault.h_po(hk_po),
    load_dts                timestamp,
    po_number               varchar(32),
    requisition_ts          timestamp,
    po_issued_ts            timestamp,
    buying_channel          varchar(16),
    total_amount            numeric(18,2),
    total_currency          varchar(3),
    total_amount_base_usd   numeric(18,2),
    payment_terms           varchar(16),
    incoterms               varchar(8),
    status                  varchar(16),
    touchless               boolean,
    maverick_flag           boolean,
    edi_855_received        boolean,
    record_source           varchar(64),
    primary key (hk_po, load_dts)
);

create table if not exists procurement_spend_analytics_vault.s_po_line_payload (
    hk_po_line              varchar(32) references procurement_spend_analytics_vault.h_po_line(hk_po_line),
    load_dts                timestamp,
    line_number             smallint,
    item_id                 varchar(64),
    item_description        varchar(255),
    quantity                numeric(15,4),
    uom                     varchar(8),
    unit_price              numeric(18,6),
    line_amount             numeric(18,2),
    line_currency           varchar(3),
    line_amount_base_usd    numeric(18,2),
    requested_delivery_date date,
    tax_amount              numeric(18,2),
    discount_pct            numeric(5,4),
    scope3_kgco2e           numeric(18,4),
    record_source           varchar(64),
    primary key (hk_po_line, load_dts)
);

create table if not exists procurement_spend_analytics_vault.s_invoice_state (
    hk_invoice               varchar(32) references procurement_spend_analytics_vault.h_invoice(hk_invoice),
    load_dts                 timestamp,
    invoice_number           varchar(64),
    invoice_date             date,
    due_date                 date,
    received_ts              timestamp,
    total_amount             numeric(18,2),
    total_currency           varchar(3),
    total_amount_base_usd    numeric(18,2),
    tax_amount               numeric(18,2),
    match_type               varchar(8),
    matched                  boolean,
    paid_ts                  timestamp,
    paid_amount              numeric(18,2),
    early_pay_discount_taken boolean,
    aging_days               smallint,
    peppol_message_id        varchar(128),
    edi_810_doc_no           varchar(32),
    status                   varchar(16),
    record_source            varchar(64),
    primary key (hk_invoice, load_dts)
);

create table if not exists procurement_spend_analytics_vault.s_risk_assessment_payload (
    hk_risk_assessment   varchar(32) references procurement_spend_analytics_vault.h_risk_assessment(hk_risk_assessment),
    load_dts             timestamp,
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
    mitigation_action    text,
    valid_until          date,
    record_source        varchar(64),
    primary key (hk_risk_assessment, load_dts)
);

create table if not exists procurement_spend_analytics_vault.s_emissions_factor_payload (
    hk_emissions_factor      varchar(32) references procurement_spend_analytics_vault.h_emissions_factor(hk_emissions_factor),
    load_dts                 timestamp,
    source                   varchar(32),
    vintage_year             smallint,
    country_iso2             varchar(2),
    factor_kgco2e_per_usd    numeric(18,6),
    factor_kgco2e_per_unit   numeric(18,6),
    unit                     varchar(16),
    ghg_scope3_category      smallint,
    uncertainty_pct          numeric(5,2),
    record_source            varchar(64),
    primary key (hk_emissions_factor, load_dts)
);

create table if not exists procurement_spend_analytics_vault.s_sustainability_payload (
    hk_sustainability_attr   varchar(32) references procurement_spend_analytics_vault.h_sustainability_attr(hk_sustainability_attr),
    load_dts                 timestamp,
    source                   varchar(32),
    reporting_year           smallint,
    scope1_tco2e             numeric(18,2),
    scope2_market_tco2e      numeric(18,2),
    scope2_location_tco2e    numeric(18,2),
    scope3_tco2e             numeric(18,2),
    renewable_energy_pct     numeric(5,2),
    water_withdrawal_m3      numeric(18,2),
    waste_tonnes             numeric(18,2),
    sbti_target_year         smallint,
    net_zero_target_year     smallint,
    record_source            varchar(64),
    primary key (hk_sustainability_attr, load_dts)
);

create table if not exists procurement_spend_analytics_vault.s_savings_payload (
    hk_savings_event      varchar(32) references procurement_spend_analytics_vault.h_savings_event(hk_savings_event),
    load_dts              timestamp,
    event_type            varchar(16),
    savings_kind          varchar(8),
    committed_amount_usd  numeric(18,2),
    realized_amount_usd   numeric(18,2),
    baseline_method       varchar(32),
    committed_at          timestamp,
    realized_through_ts   timestamp,
    record_source         varchar(64),
    primary key (hk_savings_event, load_dts)
);
