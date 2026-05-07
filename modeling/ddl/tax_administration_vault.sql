-- =============================================================================
-- Tax Administration — Data Vault 2.0
-- Hubs: taxpayer, return, audit_case, info_return, crs_record, fatca_record.
-- Bitemporal sat for return state allows reconstructing original vs amended.
-- =============================================================================

create schema if not exists tax_administration_vault;

create table if not exists tax_administration_vault.hub_taxpayer (
    taxpayer_hk bytea primary key,
    tin         varchar(11) not null,
    tin_type    varchar(8) not null,
    load_dts    timestamp not null,
    rec_src     varchar not null
);

create table if not exists tax_administration_vault.hub_return (
    return_hk     bytea primary key,
    submission_id varchar(20) not null,
    load_dts      timestamp not null,
    rec_src       varchar not null
);

create table if not exists tax_administration_vault.hub_audit_case (
    audit_case_hk bytea primary key,
    audit_case_bk varchar not null,
    load_dts      timestamp not null,
    rec_src       varchar not null
);

create table if not exists tax_administration_vault.hub_information_return (
    info_return_hk bytea primary key,
    info_return_bk varchar not null,
    load_dts       timestamp not null,
    rec_src        varchar not null
);

create table if not exists tax_administration_vault.hub_crs_record (
    crs_record_hk bytea primary key,
    docref_id     varchar(64) not null,
    load_dts      timestamp not null,
    rec_src       varchar not null
);

create table if not exists tax_administration_vault.hub_fatca_record (
    fatca_record_hk bytea primary key,
    docref_id       varchar(64) not null,
    load_dts        timestamp not null,
    rec_src         varchar not null
);

-- ---------------------------------------------------------------------------
-- Links
-- ---------------------------------------------------------------------------
create table if not exists tax_administration_vault.link_taxpayer_return (
    link_hk     bytea primary key,
    taxpayer_hk bytea not null references tax_administration_vault.hub_taxpayer(taxpayer_hk),
    return_hk   bytea not null references tax_administration_vault.hub_return(return_hk),
    load_dts    timestamp not null,
    rec_src     varchar not null
);

create table if not exists tax_administration_vault.link_taxpayer_info_return (
    link_hk          bytea primary key,
    taxpayer_hk      bytea not null references tax_administration_vault.hub_taxpayer(taxpayer_hk),
    info_return_hk   bytea not null references tax_administration_vault.hub_information_return(info_return_hk),
    load_dts         timestamp not null,
    rec_src          varchar not null
);

create table if not exists tax_administration_vault.link_taxpayer_audit (
    link_hk         bytea primary key,
    taxpayer_hk     bytea not null references tax_administration_vault.hub_taxpayer(taxpayer_hk),
    audit_case_hk   bytea not null references tax_administration_vault.hub_audit_case(audit_case_hk),
    return_hk       bytea references tax_administration_vault.hub_return(return_hk),
    load_dts        timestamp not null,
    rec_src         varchar not null
);

create table if not exists tax_administration_vault.link_taxpayer_crs (
    link_hk        bytea primary key,
    taxpayer_hk    bytea not null references tax_administration_vault.hub_taxpayer(taxpayer_hk),
    crs_record_hk  bytea not null references tax_administration_vault.hub_crs_record(crs_record_hk),
    load_dts       timestamp not null,
    rec_src        varchar not null
);

create table if not exists tax_administration_vault.link_taxpayer_fatca (
    link_hk         bytea primary key,
    taxpayer_hk     bytea not null references tax_administration_vault.hub_taxpayer(taxpayer_hk),
    fatca_record_hk bytea not null references tax_administration_vault.hub_fatca_record(fatca_record_hk),
    load_dts        timestamp not null,
    rec_src         varchar not null
);

-- ---------------------------------------------------------------------------
-- Satellites (bitemporal)
-- ---------------------------------------------------------------------------
create table if not exists tax_administration_vault.sat_taxpayer_descriptive (
    taxpayer_hk        bytea not null references tax_administration_vault.hub_taxpayer(taxpayer_hk),
    load_dts           timestamp not null,
    load_end_dts       timestamp,
    hash_diff          bytea not null,
    legal_name         varchar(255) not null,
    entity_type        varchar(16) not null,
    filing_status      varchar(16),
    address_postal_code varchar(10),
    state_code         varchar(2),
    country_iso        varchar(2),
    status             varchar(16) not null,
    rec_src            varchar not null,
    primary key (taxpayer_hk, load_dts)
);

create table if not exists tax_administration_vault.sat_return_state (
    return_hk             bytea not null references tax_administration_vault.hub_return(return_hk),
    load_dts              timestamp not null,
    load_end_dts          timestamp,
    hash_diff             bytea not null,
    form_code             varchar(8) not null,
    tax_year              smallint not null,
    amended_return_indicator boolean not null default false,
    submitted_at          timestamp not null,
    ack_status            varchar(8),
    ack_received_at       timestamp,
    rec_src               varchar not null,
    primary key (return_hk, load_dts)
);

create table if not exists tax_administration_vault.sat_return_data (
    return_hk      bytea not null references tax_administration_vault.hub_return(return_hk),
    load_dts       timestamp not null,
    load_end_dts   timestamp,
    hash_diff      bytea not null,
    total_income   numeric(15, 2),
    agi            numeric(15, 2),
    taxable_income numeric(15, 2),
    total_tax      numeric(15, 2),
    total_payments numeric(15, 2),
    refund_amount  numeric(15, 2),
    amount_owed    numeric(15, 2),
    dependent_count smallint,
    rec_src        varchar not null,
    primary key (return_hk, load_dts)
);

create table if not exists tax_administration_vault.sat_audit_state (
    audit_case_hk         bytea not null references tax_administration_vault.hub_audit_case(audit_case_hk),
    load_dts              timestamp not null,
    load_end_dts          timestamp,
    hash_diff             bytea not null,
    audit_type            varchar(16) not null,
    risk_score            numeric(6, 4),
    selection_program     varchar(32),
    opened_at             date,
    closed_at             date,
    status                varchar(16) not null,
    outcome               varchar(16),
    adjusted_tax_amount   numeric(15, 2),
    rec_src               varchar not null,
    primary key (audit_case_hk, load_dts)
);

create table if not exists tax_administration_vault.sat_information_return (
    info_return_hk        bytea not null references tax_administration_vault.hub_information_return(info_return_hk),
    load_dts              timestamp not null,
    load_end_dts          timestamp,
    hash_diff             bytea not null,
    form_code             varchar(16) not null,
    tax_year              smallint not null,
    total_amount          numeric(15, 2),
    federal_tax_withheld  numeric(15, 2),
    corrected_indicator   boolean not null default false,
    received_at           timestamp not null,
    match_status          varchar(16) not null,
    rec_src               varchar not null,
    primary key (info_return_hk, load_dts)
);

create table if not exists tax_administration_vault.sat_crs_record (
    crs_record_hk         bytea not null references tax_administration_vault.hub_crs_record(crs_record_hk),
    load_dts              timestamp not null,
    load_end_dts          timestamp,
    hash_diff             bytea not null,
    reporting_fi_giin     varchar(19),
    account_number        varchar(64) not null,
    residence_country_iso varchar(2),
    account_balance       numeric(20, 2),
    balance_currency      varchar(3),
    report_period_end     date,
    rec_src               varchar not null,
    primary key (crs_record_hk, load_dts)
);
