-- =============================================================================
-- Procurement & Spend Analytics — 3NF schema
-- Source standards (verbatim where the spec names a field):
--   UNSPSC v26 — canonical category taxonomy (Segment/Family/Class/Commodity).
--   GHG Protocol Scope 3 — Cat. 1 (Purchased Goods & Services), Cat. 2 (Capital).
--   ISO 14064 — GHG quantification and reporting.
--   ISO 20400 — Sustainable procurement (clause flow).
--   Open Peppol BIS Billing 3.0 — pan-European e-invoicing envelope.
--   EDI X12 850 / 855 / 856 / 810 / 820 — PO / PO Ack / ASN / Invoice / Remit.
--   D-U-N-S (Dun & Bradstreet) and LEI (ISO 17442) — supplier spine.
--   Incoterms 2020 — DDP / FOB / EXW / ...
-- Vendors reflected in source IDs and integration semantics:
--   SAP Ariba, Coupa, Jaggaer, Ivalua, GEP SMART, Oracle Procurement Cloud,
--   Workday Strategic Sourcing, Tradeshift, Basware, Zycus, EcoVadis, Sievo,
--   Spendkey, Resilinc, Sphera, D&B, BitSight, CDP, SBTi.
-- =============================================================================

create schema if not exists procurement_spend_analytics;

-- ---------- Reference: UNSPSC-anchored category taxonomy ----------
create table if not exists procurement_spend_analytics.category_taxonomy (
    category_code         varchar(8) primary key,        -- UNSPSC 8-digit
    segment_code          varchar(2),
    family_code           varchar(4),
    class_code            varchar(6),
    commodity_code        varchar(8),
    segment_name          varchar(128),
    family_name           varchar(128),
    class_name            varchar(128),
    commodity_name        varchar(128),
    direct_or_indirect    varchar(8),                    -- direct|indirect
    capex_or_opex         varchar(5),                    -- capex|opex
    internal_category_id  varchar(64),                   -- tenant cross-walk
    scope3_category       smallint                       -- GHG Scope 3 cat 1..15
);

-- ---------- Supplier master ----------
create table if not exists procurement_spend_analytics.supplier (
    supplier_id          varchar(64) primary key,
    duns_number          varchar(9),                     -- D&B DUNS
    lei                  varchar(20),                    -- ISO 17442 LEI
    legal_name           varchar(255),
    parent_duns          varchar(9),                     -- corporate-family roll-up
    tax_id               varchar(64),                    -- VAT/EIN/GSTIN
    country_iso2         varchar(2),
    region               varchar(32),                    -- NA|EMEA|APAC|LATAM|MEA
    industry_naics       varchar(6),
    industry_sic         varchar(4),
    diversity_flags      text,                           -- JSON: MBE|WBE|VBE|...
    ecovadis_score       smallint,                       -- 0..100
    ecovadis_medal       varchar(8),                     -- bronze|silver|gold|platinum
    cdp_climate_score    varchar(2),                     -- A..D-
    sbti_committed       boolean,
    paydex_score         smallint,                       -- D&B Paydex 0..100
    failure_score        smallint,                       -- D&B Failure Score
    cyber_score          smallint,                       -- BitSight/RiskRecon 250..900
    critical_flag        boolean,
    sanctions_flag       boolean,
    status               varchar(16),                    -- active|onboarding|blocked|...
    onboarded_at         timestamp,
    last_assessment_at   timestamp
);

-- ---------- Master / framework contract ----------
create table if not exists procurement_spend_analytics.contract (
    contract_id              varchar(64) primary key,
    supplier_id              varchar(64) references procurement_spend_analytics.supplier(supplier_id),
    contract_type            varchar(32),                -- framework|spot|MSA|SOW|catalog|rebate|service_agreement
    parent_contract_id       varchar(64) references procurement_spend_analytics.contract(contract_id),
    title                    varchar(255),
    effective_date           date,
    expiry_date              date,
    auto_renew               boolean,
    notice_period_days       smallint,
    total_commit_amount      numeric(18,2),
    total_commit_currency    varchar(3),
    payment_terms            varchar(16),                -- NET30|NET45|2_10_NET30|...
    incoterms                varchar(8),                 -- Incoterms 2020
    rebate_pct               numeric(5,4),
    rebate_trigger_amount    numeric(18,2),
    sustainability_clauses   text,                       -- JSON
    kpi_clauses              text,                       -- JSON
    contract_value_realized  numeric(18,2),
    status                   varchar(16),                -- draft|active|expired|terminated|renewed
    owner_buyer              varchar(64),
    meta_extracted_at        timestamp
);

-- ---------- Purchase order header ----------
create table if not exists procurement_spend_analytics.purchase_order (
    po_id                   varchar(64) primary key,
    po_number               varchar(32),
    supplier_id             varchar(64) references procurement_spend_analytics.supplier(supplier_id),
    contract_id             varchar(64) references procurement_spend_analytics.contract(contract_id),
    requester_user_id       varchar(64),
    buyer_user_id           varchar(64),
    cost_center             varchar(32),
    gl_account              varchar(16),
    legal_entity            varchar(32),
    plant_id                varchar(32),
    requisition_id          varchar(64),
    requisition_ts          timestamp,
    po_issued_ts            timestamp,
    buying_channel          varchar(16),                 -- catalog|punchout|free_text|marketplace|pcard|auto
    total_amount            numeric(18,2),
    total_currency          varchar(3),
    total_amount_base_usd   numeric(18,2),
    payment_terms           varchar(16),
    incoterms               varchar(8),
    status                  varchar(16),                 -- draft|approved|sent|...|closed
    touchless               boolean,
    maverick_flag           boolean,
    edi_855_received        boolean,
    category_code           varchar(8) references procurement_spend_analytics.category_taxonomy(category_code)
);

-- ---------- PO line — spend cube fact at natural grain ----------
create table if not exists procurement_spend_analytics.po_line (
    po_line_id              varchar(64) primary key,
    po_id                   varchar(64) references procurement_spend_analytics.purchase_order(po_id),
    line_number             smallint,
    item_id                 varchar(64),
    item_description        varchar(255),
    category_code           varchar(8) references procurement_spend_analytics.category_taxonomy(category_code),
    quantity                numeric(15,4),
    uom                     varchar(8),                  -- UN/CEFACT rec.20 codes
    unit_price              numeric(18,6),
    line_amount             numeric(18,2),
    line_currency           varchar(3),
    line_amount_base_usd    numeric(18,2),
    requested_delivery_date date,
    tax_amount              numeric(18,2),
    discount_pct            numeric(5,4),
    scope3_kgco2e           numeric(18,4)                -- Attributed Scope 3 emissions
);

-- ---------- Goods / services receipt ----------
create table if not exists procurement_spend_analytics.receipt (
    receipt_id           varchar(64) primary key,
    po_id                varchar(64) references procurement_spend_analytics.purchase_order(po_id),
    po_line_id           varchar(64) references procurement_spend_analytics.po_line(po_line_id),
    receipt_ts           timestamp,
    quantity_received    numeric(15,4),
    receiver_user_id     varchar(64),
    plant_id             varchar(32),
    gr_document_no       varchar(32),
    status               varchar(16)                     -- draft|posted|reversed
);

-- ---------- AP invoice ----------
create table if not exists procurement_spend_analytics.invoice (
    invoice_id                varchar(64) primary key,
    supplier_id               varchar(64) references procurement_spend_analytics.supplier(supplier_id),
    invoice_number            varchar(64),
    po_id                     varchar(64) references procurement_spend_analytics.purchase_order(po_id),
    invoice_date              date,
    due_date                  date,
    received_ts               timestamp,
    total_amount              numeric(18,2),
    total_currency            varchar(3),
    total_amount_base_usd     numeric(18,2),
    tax_amount                numeric(18,2),
    match_type                varchar(8),                -- two_way|three_way|exception|none
    matched                   boolean,
    paid_ts                   timestamp,
    paid_amount               numeric(18,2),
    early_pay_discount_taken  boolean,
    aging_days                smallint,
    peppol_message_id         varchar(128),              -- Peppol BIS 3.0
    edi_810_doc_no            varchar(32),
    status                    varchar(16)                -- received|matched|paid|on_hold|disputed|void
);

-- ---------- Supplier risk assessment snapshot ----------
create table if not exists procurement_spend_analytics.supplier_risk_assessment (
    assessment_id        varchar(64) primary key,
    supplier_id          varchar(64) references procurement_spend_analytics.supplier(supplier_id),
    assessment_ts        timestamp,
    source               varchar(32),                    -- resilinc|dnb|bitsight|ecovadis|...
    overall_score        numeric(5,2),                   -- 0..100 (lower = riskier per Resilinc convention; tenant may invert)
    financial_score      smallint,
    operational_score    smallint,
    geographic_score     smallint,
    cyber_score          smallint,
    compliance_score     smallint,
    sustainability_score smallint,
    tier                 varchar(8),                     -- low|medium|high|critical
    mitigation_action    text,
    assessor_user_id     varchar(64),
    valid_until          date
);

-- ---------- Emissions factor reference ----------
create table if not exists procurement_spend_analytics.emissions_factor (
    emissions_factor_id        varchar(64) primary key,
    source                     varchar(32),              -- exiobase|usio|ecoinvent|cdp_supplier|primary_supplier_data
    vintage_year               smallint,
    category_code              varchar(8) references procurement_spend_analytics.category_taxonomy(category_code),
    country_iso2               varchar(2),
    factor_kgco2e_per_usd      numeric(18,6),
    factor_kgco2e_per_unit     numeric(18,6),
    unit                       varchar(16),
    ghg_scope3_category        smallint,                 -- 1..15
    uncertainty_pct            numeric(5,2),
    last_updated               timestamp
);

-- ---------- Supplier-disclosed sustainability attributes ----------
create table if not exists procurement_spend_analytics.sustainability_attribute (
    sustainability_attr_id     varchar(64) primary key,
    supplier_id                varchar(64) references procurement_spend_analytics.supplier(supplier_id),
    source                     varchar(32),              -- ecovadis|cdp_supply_chain|sbti|msci_esg|sp_sustainable1|primary
    reporting_year             smallint,
    scope1_tco2e               numeric(18,2),
    scope2_market_tco2e        numeric(18,2),
    scope2_location_tco2e      numeric(18,2),
    scope3_tco2e               numeric(18,2),
    renewable_energy_pct       numeric(5,2),
    water_withdrawal_m3        numeric(18,2),
    waste_tonnes               numeric(18,2),
    sbti_target_year           smallint,
    net_zero_target_year       smallint,
    observed_at                timestamp
);

-- ---------- Savings tracking ledger ----------
create table if not exists procurement_spend_analytics.savings_event (
    savings_event_id      varchar(64) primary key,
    supplier_id           varchar(64) references procurement_spend_analytics.supplier(supplier_id),
    contract_id           varchar(64) references procurement_spend_analytics.contract(contract_id),
    category_code         varchar(8)  references procurement_spend_analytics.category_taxonomy(category_code),
    event_type            varchar(16),                   -- negotiation|consolidation|reverse_auction|...
    savings_kind          varchar(8),                    -- hard|soft|avoidance
    committed_amount_usd  numeric(18,2),
    realized_amount_usd   numeric(18,2),
    baseline_method       varchar(32),                   -- prior_price|index|RFP_avg|benchmark|cost_model
    signed_off_by         varchar(64),
    committed_at          timestamp,
    realized_through_ts   timestamp
);

-- ---------- Indexes ----------
create index if not exists ix_supplier_duns        on procurement_spend_analytics.supplier(duns_number);
create index if not exists ix_supplier_parent      on procurement_spend_analytics.supplier(parent_duns);
create index if not exists ix_contract_supplier    on procurement_spend_analytics.contract(supplier_id, expiry_date);
create index if not exists ix_po_supplier          on procurement_spend_analytics.purchase_order(supplier_id, po_issued_ts);
create index if not exists ix_po_contract          on procurement_spend_analytics.purchase_order(contract_id);
create index if not exists ix_po_category          on procurement_spend_analytics.purchase_order(category_code);
create index if not exists ix_pol_po               on procurement_spend_analytics.po_line(po_id);
create index if not exists ix_pol_category         on procurement_spend_analytics.po_line(category_code);
create index if not exists ix_receipt_po           on procurement_spend_analytics.receipt(po_id, receipt_ts);
create index if not exists ix_invoice_supplier     on procurement_spend_analytics.invoice(supplier_id, invoice_date);
create index if not exists ix_invoice_po           on procurement_spend_analytics.invoice(po_id);
create index if not exists ix_risk_supplier        on procurement_spend_analytics.supplier_risk_assessment(supplier_id, assessment_ts);
create index if not exists ix_emfactor_cat         on procurement_spend_analytics.emissions_factor(category_code, vintage_year);
create index if not exists ix_susattr_supplier     on procurement_spend_analytics.sustainability_attribute(supplier_id, reporting_year);
create index if not exists ix_savings_supplier     on procurement_spend_analytics.savings_event(supplier_id, committed_at);
