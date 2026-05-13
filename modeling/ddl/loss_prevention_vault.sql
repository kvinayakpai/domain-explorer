-- =============================================================================
-- Loss Prevention — Data Vault 2.0 schema
-- Hubs (business keys) + Links (relationships) + Satellites (insert-only,
-- time-stamped). Designed so cross-retailer ORC links can drop in without
-- restructuring core hubs.
-- =============================================================================

create schema if not exists loss_prevention_vault;

-- ---------- HUBS ----------
create table if not exists loss_prevention_vault.h_store (
    hk_store        varchar(32) primary key,    -- MD5(store_id)
    store_id        varchar(16) unique,
    load_dts        timestamp,
    record_source   varchar(64)
);

create table if not exists loss_prevention_vault.h_employee (
    hk_employee     varchar(32) primary key,
    employee_id     varchar(16) unique,
    load_dts        timestamp,
    record_source   varchar(64)
);

create table if not exists loss_prevention_vault.h_item (
    hk_item         varchar(32) primary key,
    item_id         varchar(32) unique,
    load_dts        timestamp,
    record_source   varchar(64)
);

create table if not exists loss_prevention_vault.h_transaction (
    hk_transaction  varchar(32) primary key,
    transaction_id  varchar(32) unique,
    load_dts        timestamp,
    record_source   varchar(64)
);

create table if not exists loss_prevention_vault.h_exception (
    hk_exception    varchar(32) primary key,
    exception_id    varchar(32) unique,
    load_dts        timestamp,
    record_source   varchar(64)
);

create table if not exists loss_prevention_vault.h_incident (
    hk_incident     varchar(32) primary key,
    incident_id     varchar(32) unique,
    load_dts        timestamp,
    record_source   varchar(64)
);

create table if not exists loss_prevention_vault.h_suspect (
    hk_suspect      varchar(32) primary key,
    suspect_id      varchar(32) unique,
    load_dts        timestamp,
    record_source   varchar(64)
);

create table if not exists loss_prevention_vault.h_investigation (
    hk_investigation  varchar(32) primary key,
    investigation_id  varchar(32) unique,
    load_dts          timestamp,
    record_source     varchar(64)
);

-- ---------- LINKS ----------
create table if not exists loss_prevention_vault.l_exception_transaction (
    hk_link         varchar(32) primary key,
    hk_exception    varchar(32) references loss_prevention_vault.h_exception(hk_exception),
    hk_transaction  varchar(32) references loss_prevention_vault.h_transaction(hk_transaction),
    hk_store        varchar(32) references loss_prevention_vault.h_store(hk_store),
    hk_employee     varchar(32) references loss_prevention_vault.h_employee(hk_employee),
    load_dts        timestamp,
    record_source   varchar(64)
);

create table if not exists loss_prevention_vault.l_incident_store (
    hk_link         varchar(32) primary key,
    hk_incident     varchar(32) references loss_prevention_vault.h_incident(hk_incident),
    hk_store        varchar(32) references loss_prevention_vault.h_store(hk_store),
    load_dts        timestamp,
    record_source   varchar(64)
);

create table if not exists loss_prevention_vault.l_incident_suspect (
    hk_link         varchar(32) primary key,
    hk_incident     varchar(32) references loss_prevention_vault.h_incident(hk_incident),
    hk_suspect      varchar(32) references loss_prevention_vault.h_suspect(hk_suspect),
    load_dts        timestamp,
    record_source   varchar(64)
);

create table if not exists loss_prevention_vault.l_investigation_incident (
    hk_link             varchar(32) primary key,
    hk_investigation    varchar(32) references loss_prevention_vault.h_investigation(hk_investigation),
    hk_incident         varchar(32) references loss_prevention_vault.h_incident(hk_incident),
    load_dts            timestamp,
    record_source       varchar(64)
);

create table if not exists loss_prevention_vault.l_recovery_incident (
    hk_link             varchar(32) primary key,
    hk_incident         varchar(32) references loss_prevention_vault.h_incident(hk_incident),
    hk_investigation    varchar(32) references loss_prevention_vault.h_investigation(hk_investigation),
    load_dts            timestamp,
    record_source       varchar(64)
);

create table if not exists loss_prevention_vault.l_orc_ring (
    hk_link             varchar(32) primary key,
    hk_suspect          varchar(32) references loss_prevention_vault.h_suspect(hk_suspect),
    orc_ring_id         varchar(32),
    alto_packet_id      varchar(64),
    auror_offender_id   varchar(64),
    load_dts            timestamp,
    record_source       varchar(64)
);

-- ---------- SATELLITES ----------
create table if not exists loss_prevention_vault.s_store_descriptive (
    hk_store         varchar(32) references loss_prevention_vault.h_store(hk_store),
    load_dts         timestamp,
    store_name       varchar(255),
    banner           varchar(64),
    region           varchar(64),
    country_iso2     varchar(2),
    format           varchar(32),
    lp_staffing_tier varchar(8),
    eas_enabled      boolean,
    rfid_enabled     boolean,
    status           varchar(16),
    record_source    varchar(64),
    primary key (hk_store, load_dts)
);

create table if not exists loss_prevention_vault.s_employee_descriptive (
    hk_employee       varchar(32) references loss_prevention_vault.h_employee(hk_employee),
    load_dts          timestamp,
    employee_ref_hash varchar(64),
    role              varchar(32),
    home_store_id     varchar(16),
    status            varchar(16),
    record_source     varchar(64),
    primary key (hk_employee, load_dts)
);

create table if not exists loss_prevention_vault.s_exception_payload (
    hk_exception          varchar(32) references loss_prevention_vault.h_exception(hk_exception),
    load_dts              timestamp,
    exception_type        varchar(32),
    exception_score       numeric(5,3),
    source_system         varchar(32),
    amount_at_risk_minor  bigint,
    status                varchar(16),
    video_segment_ref     text,
    record_source         varchar(64),
    primary key (hk_exception, load_dts)
);

create table if not exists loss_prevention_vault.s_incident_state (
    hk_incident       varchar(32) references loss_prevention_vault.h_incident(hk_incident),
    load_dts          timestamp,
    incident_type     varchar(32),
    status            varchar(16),
    gross_loss_minor  bigint,
    recovered_minor   bigint,
    net_loss_minor    bigint,
    nibrs_code        varchar(8),
    record_source     varchar(64),
    primary key (hk_incident, load_dts)
);

create table if not exists loss_prevention_vault.s_suspect_descriptive (
    hk_suspect              varchar(32) references loss_prevention_vault.h_suspect(hk_suspect),
    load_dts                timestamp,
    suspect_ref_hash        varchar(64),
    alias_count             smallint,
    orc_flag                boolean,
    orc_ring_id             varchar(32),
    known_vehicle_ref_hash  varchar(64),
    auror_offender_id       varchar(64),
    alto_packet_id          varchar(64),
    record_source           varchar(64),
    primary key (hk_suspect, load_dts)
);

create table if not exists loss_prevention_vault.s_investigation_state (
    hk_investigation       varchar(32) references loss_prevention_vault.h_investigation(hk_investigation),
    load_dts               timestamp,
    investigation_type     varchar(32),
    status                 varchar(16),
    evidence_count         integer,
    video_evidence_minutes integer,
    prosecution_referred   boolean,
    alto_shared            boolean,
    case_packet_uri        text,
    record_source          varchar(64),
    primary key (hk_investigation, load_dts)
);

create table if not exists loss_prevention_vault.s_recovery_payload (
    hk_incident              varchar(32) references loss_prevention_vault.h_incident(hk_incident),
    load_dts                 timestamp,
    recovered_amount_minor   bigint,
    recovery_type            varchar(32),
    recovered_at             timestamp,
    record_source            varchar(64),
    primary key (hk_incident, load_dts)
);

create table if not exists loss_prevention_vault.s_shrink_snapshot (
    hk_store                  varchar(32) references loss_prevention_vault.h_store(hk_store),
    load_dts                  timestamp,
    department                varchar(64),
    period_start              date,
    period_end                date,
    opening_inventory_minor   bigint,
    receipts_minor            bigint,
    cogs_minor                bigint,
    closing_inventory_minor   bigint,
    known_shrink_minor        bigint,
    unknown_shrink_minor      bigint,
    total_shrink_minor        bigint,
    shrink_pct                numeric(6,4),
    record_source             varchar(64),
    primary key (hk_store, load_dts, department, period_start)
);
