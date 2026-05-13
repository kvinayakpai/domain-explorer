-- =============================================================================
-- Loss Prevention — 3NF schema (Retail)
-- Source standards & products:
--   NCR Voyix Loss Prevention Analytics, Oracle Retail XStore LP (XBR),
--   Sensormatic Solutions (Johnson Controls) EAS / ShrinkVision,
--   Auror ORC platform, Appriss Retail Verify, Profitect (Zebra),
--   Aptos LP, Tyco RFID / Detego Cloud, Indyme, ALTO Alliance,
--   Zebra Reflexis (LP audit/task), Honeywell Connected Retail,
--   RetailNext Aurora, Datalogic scan-aware LP, NCR Counterpoint.
-- Compliance:
--   PII tokenization at column level (employee/suspect/customer hashes),
--   NIST SP 800-53 Rev. 5 audit logging, PCI DSS v4.0 for card-adjacent fields,
--   ALTO Alliance Information Sharing Standard for retailer-LE share.
-- =============================================================================

create schema if not exists loss_prevention;

-- Selling location where exceptions and incidents originate.
create table if not exists loss_prevention.store (
    store_id            varchar(16) primary key,
    store_name          varchar(255),
    banner              varchar(64),
    region              varchar(64),
    country_iso2        varchar(2),
    format              varchar(32),                       -- hypermarket|supermarket|specialty|convenience|ecom_dc
    lp_staffing_tier    varchar(8),                        -- T1|T2|T3
    eas_enabled         boolean,
    rfid_enabled        boolean,
    status              varchar(16)
);

-- Associate / contractor. PII-restricted; raw HRIS id lives only in HR.
create table if not exists loss_prevention.employee (
    employee_id          varchar(16) primary key,
    employee_ref_hash    varchar(64),                       -- SHA-256(HR-id + tenant_salt)
    home_store_id        varchar(16) references loss_prevention.store(store_id),
    role                 varchar(32),
    hire_date            date,
    termination_date     date,
    status               varchar(16)                        -- active|terminated|investigation|on_leave
);

-- Item master driving shrink attribution + CRAVED scoring.
create table if not exists loss_prevention.item (
    item_id             varchar(32) primary key,
    gtin                varchar(14),
    department          varchar(64),
    category            varchar(64),
    unit_cost_minor     bigint,
    unit_retail_minor   bigint,
    craved_score        numeric(4,2),                       -- 0..10
    eas_protected       boolean,
    rfid_tagged         boolean
);

-- POS receipt header — auxiliary join for exceptions.
create table if not exists loss_prevention.pos_transaction (
    transaction_id        varchar(32) primary key,
    store_id              varchar(16) references loss_prevention.store(store_id),
    register_id           varchar(16),
    employee_id           varchar(16) references loss_prevention.employee(employee_id),
    customer_ref_hash     varchar(64),                      -- SHA-256(loyalty_id + salt)
    txn_ts                timestamp,
    tender_type           varchar(16),
    gross_amount_minor    bigint,
    discount_amount_minor bigint,
    refund_amount_minor   bigint,
    net_amount_minor      bigint,
    item_count            integer,
    void_flag             boolean,
    no_sale_flag          boolean
);

-- One detected POS exception. Normalized vendor score in [0,1].
create table if not exists loss_prevention.pos_exception (
    exception_id          varchar(32) primary key,
    transaction_id        varchar(32) references loss_prevention.pos_transaction(transaction_id),
    store_id              varchar(16) references loss_prevention.store(store_id),
    employee_id           varchar(16) references loss_prevention.employee(employee_id),
    exception_type        varchar(32),                      -- sweethearting|refund_no_receipt|void_after_tender|no_sale|cash_skim|price_override|barcode_swap|discount_abuse
    exception_score       numeric(5,3),                     -- 0..1 normalized
    source_system         varchar(32),                      -- NCR_Voyix_LP|Oracle_XBR|Profitect|Aptos_LP|Sensormatic|Datalogic|NCR_Counterpoint|Honeywell
    detected_at           timestamp,
    status                varchar(16),                      -- open|under_review|investigation|closed_unfounded|closed_confirmed
    amount_at_risk_minor  bigint,
    video_segment_ref     text                              -- signed URI to cold-storage clip; bytes never in warehouse
);

-- Discrete loss / theft event.
create table if not exists loss_prevention.incident (
    incident_id             varchar(32) primary key,
    store_id                varchar(16) references loss_prevention.store(store_id),
    incident_type           varchar(32),                    -- external_shoplift|internal_theft|orc_boost|burglary|robbery|return_abuse|refund_fraud|cargo_theft
    incident_ts             timestamp,
    reported_by_employee_id varchar(16) references loss_prevention.employee(employee_id),
    detected_via            varchar(32),                    -- exception_alert|cctv_review|tip|customer_report|audit|inventory_count
    suspect_id              varchar(32),
    gross_loss_minor        bigint,
    recovered_minor         bigint,
    net_loss_minor          bigint,
    nibrs_code              varchar(8),                     -- FBI NIBRS
    status                  varchar(16)                     -- open|investigating|closed_recovered|closed_prosecuted|closed_writeoff|closed_unfounded
);

-- Person of interest; PII tokenized.
create table if not exists loss_prevention.suspect (
    suspect_id              varchar(32) primary key,
    suspect_ref_hash        varchar(64),                    -- SHA-256({name,dob} + salt)
    alias_count             smallint,
    first_seen_at           timestamp,
    last_seen_at            timestamp,
    orc_flag                boolean,
    orc_ring_id             varchar(32),
    known_vehicle_ref_hash  varchar(64),                    -- SHA-256(plate+state+salt)
    auror_offender_id       varchar(64),                    -- Auror cross-retailer link
    alto_packet_id          varchar(64)                     -- ALTO Alliance shared-case id
);

-- Investigation case. Chain-of-custody pointer to encrypted case-management.
create table if not exists loss_prevention.investigation (
    investigation_id          varchar(32) primary key,
    incident_id               varchar(32) references loss_prevention.incident(incident_id),
    opened_by_employee_id     varchar(16) references loss_prevention.employee(employee_id),
    opened_at                 timestamp,
    closed_at                 timestamp,
    investigation_type        varchar(32),                  -- internal|external|orc|refund_fraud|sweethearting_audit|cargo
    status                    varchar(16),                  -- open|in_progress|closed_recovered|closed_prosecuted|closed_writeoff|closed_unfounded
    evidence_count            integer,
    video_evidence_minutes    integer,
    prosecution_referred      boolean,
    alto_shared               boolean,
    case_packet_uri           text                           -- pointer to encrypted bucket
);

-- Money / goods recovered.
create table if not exists loss_prevention.recovery (
    recovery_id                varchar(32) primary key,
    incident_id                varchar(32) references loss_prevention.incident(incident_id),
    investigation_id           varchar(32) references loss_prevention.investigation(investigation_id),
    recovered_amount_minor     bigint,
    recovery_type              varchar(32),                 -- cash|merchandise|civil_demand|restitution|insurance_payout
    recovered_at               timestamp,
    recovered_by_employee_id   varchar(16) references loss_prevention.employee(employee_id)
);

-- Per-transaction or per-customer fraud score (Appriss Retail / internal model).
create table if not exists loss_prevention.fraud_score (
    fraud_score_id     varchar(32) primary key,
    customer_ref_hash  varchar(64),
    transaction_id     varchar(32),
    score_source       varchar(32),                          -- Appriss_Retail|internal_xgb|Auror_offender_signal
    score              numeric(5,3),                         -- 0..1
    recommendation     varchar(16),                          -- approve|verify|deny
    scored_at          timestamp
);

-- Period shrink snapshot. The ledger truth that exceptions/incidents reconcile to.
create table if not exists loss_prevention.shrink_snapshot (
    snapshot_id              varchar(32) primary key,
    store_id                 varchar(16) references loss_prevention.store(store_id),
    department               varchar(64),
    period_start             date,
    period_end               date,
    opening_inventory_minor  bigint,
    receipts_minor           bigint,
    cogs_minor               bigint,
    closing_inventory_minor  bigint,
    known_shrink_minor       bigint,
    unknown_shrink_minor     bigint,
    total_shrink_minor       bigint,
    shrink_pct               numeric(6,4)
);

-- Helpful indexes for the common LP queries.
create index if not exists ix_lp_exc_store    on loss_prevention.pos_exception(store_id);
create index if not exists ix_lp_exc_emp      on loss_prevention.pos_exception(employee_id);
create index if not exists ix_lp_exc_type     on loss_prevention.pos_exception(exception_type);
create index if not exists ix_lp_inc_store    on loss_prevention.incident(store_id);
create index if not exists ix_lp_inc_suspect  on loss_prevention.incident(suspect_id);
create index if not exists ix_lp_inv_incident on loss_prevention.investigation(incident_id);
create index if not exists ix_lp_rec_incident on loss_prevention.recovery(incident_id);
create index if not exists ix_lp_shrink_store on loss_prevention.shrink_snapshot(store_id);
create index if not exists ix_lp_fraud_txn    on loss_prevention.fraud_score(transaction_id);
