-- =============================================================================
-- Pharmacovigilance — Data Vault 2.0 (excerpt)
-- Hubs / Links / Satellites for ICSR, product, authority, signal — with
-- audit-grade load_dts on every node (21 CFR Part 11 alignment).
-- =============================================================================

create schema if not exists pharmacovigilance_vault;

-- Hubs
create table if not exists pharmacovigilance_vault.hub_icsr (
    icsr_hk              bytea primary key,
    icsr_bk              varchar not null,
    load_dts             timestamp not null,
    rec_src              varchar not null
);

create table if not exists pharmacovigilance_vault.hub_product (
    product_hk           bytea primary key,
    product_bk           varchar not null,
    load_dts             timestamp not null,
    rec_src              varchar not null
);

create table if not exists pharmacovigilance_vault.hub_patient (
    patient_hk           bytea primary key,
    patient_bk           varchar not null,
    load_dts             timestamp not null,
    rec_src              varchar not null
);

create table if not exists pharmacovigilance_vault.hub_reporter (
    reporter_hk          bytea primary key,
    reporter_bk          varchar not null,
    load_dts             timestamp not null,
    rec_src              varchar not null
);

create table if not exists pharmacovigilance_vault.hub_authority (
    authority_hk         bytea primary key,
    authority_bk         varchar not null,
    load_dts             timestamp not null,
    rec_src              varchar not null
);

create table if not exists pharmacovigilance_vault.hub_meddra_term (
    meddra_hk            bytea primary key,
    pt_code              varchar(16) not null,
    load_dts             timestamp not null,
    rec_src              varchar not null
);

create table if not exists pharmacovigilance_vault.hub_signal (
    signal_hk            bytea primary key,
    signal_bk            varchar not null,
    load_dts             timestamp not null,
    rec_src              varchar not null
);

-- Links
create table if not exists pharmacovigilance_vault.link_icsr_product (
    link_hk              bytea primary key,
    icsr_hk              bytea not null references pharmacovigilance_vault.hub_icsr(icsr_hk),
    product_hk           bytea not null references pharmacovigilance_vault.hub_product(product_hk),
    role                 varchar(16) not null,
    load_dts             timestamp not null,
    rec_src              varchar not null
);

create table if not exists pharmacovigilance_vault.link_icsr_patient (
    link_hk              bytea primary key,
    icsr_hk              bytea not null references pharmacovigilance_vault.hub_icsr(icsr_hk),
    patient_hk           bytea not null references pharmacovigilance_vault.hub_patient(patient_hk),
    load_dts             timestamp not null,
    rec_src              varchar not null
);

create table if not exists pharmacovigilance_vault.link_icsr_reporter (
    link_hk              bytea primary key,
    icsr_hk              bytea not null references pharmacovigilance_vault.hub_icsr(icsr_hk),
    reporter_hk          bytea not null references pharmacovigilance_vault.hub_reporter(reporter_hk),
    load_dts             timestamp not null,
    rec_src              varchar not null
);

create table if not exists pharmacovigilance_vault.link_ae_meddra (
    link_hk              bytea primary key,
    icsr_hk              bytea not null references pharmacovigilance_vault.hub_icsr(icsr_hk),
    meddra_hk            bytea not null references pharmacovigilance_vault.hub_meddra_term(meddra_hk),
    ae_bk                varchar not null,
    load_dts             timestamp not null,
    rec_src              varchar not null
);

create table if not exists pharmacovigilance_vault.link_submission (
    link_hk              bytea primary key,
    icsr_hk              bytea not null references pharmacovigilance_vault.hub_icsr(icsr_hk),
    authority_hk         bytea not null references pharmacovigilance_vault.hub_authority(authority_hk),
    submission_bk        varchar not null,
    load_dts             timestamp not null,
    rec_src              varchar not null
);

create table if not exists pharmacovigilance_vault.link_signal_product (
    link_hk              bytea primary key,
    signal_hk            bytea not null references pharmacovigilance_vault.hub_signal(signal_hk),
    product_hk           bytea not null references pharmacovigilance_vault.hub_product(product_hk),
    meddra_hk            bytea not null references pharmacovigilance_vault.hub_meddra_term(meddra_hk),
    load_dts             timestamp not null,
    rec_src              varchar not null
);

-- Satellites
create table if not exists pharmacovigilance_vault.sat_icsr_state (
    icsr_hk              bytea not null references pharmacovigilance_vault.hub_icsr(icsr_hk),
    load_dts             timestamp not null,
    load_end_dts         timestamp,
    hash_diff            bytea not null,
    case_version         smallint not null,
    case_state           varchar(16) not null,
    seriousness          varchar(16) not null,
    expectedness         varchar(16),
    causality            varchar(16),
    intake_country       varchar(2),
    rec_src              varchar not null,
    primary key (icsr_hk, load_dts)
);

create table if not exists pharmacovigilance_vault.sat_product_descriptive (
    product_hk           bytea not null references pharmacovigilance_vault.hub_product(product_hk),
    load_dts             timestamp not null,
    load_end_dts         timestamp,
    hash_diff            bytea not null,
    brand_name           varchar not null,
    inn                  varchar not null,
    atc_code             varchar(8),
    therapeutic_area     varchar(64),
    is_marketed          boolean not null,
    rec_src              varchar not null,
    primary key (product_hk, load_dts)
);

create table if not exists pharmacovigilance_vault.sat_meddra_descriptive (
    meddra_hk            bytea not null references pharmacovigilance_vault.hub_meddra_term(meddra_hk),
    load_dts             timestamp not null,
    load_end_dts         timestamp,
    hash_diff            bytea not null,
    pt_name              varchar not null,
    soc_code             varchar(16) not null,
    soc_name             varchar not null,
    hlt_code             varchar(16),
    hlgt_code            varchar(16),
    rec_src              varchar not null,
    primary key (meddra_hk, load_dts)
);

create table if not exists pharmacovigilance_vault.sat_submission_state (
    link_hk              bytea not null,
    load_dts             timestamp not null,
    load_end_dts         timestamp,
    hash_diff            bytea not null,
    submission_type      varchar(16) not null,
    due_date             date not null,
    submitted_at         timestamp,
    transmission_status  varchar(16) not null,
    ack_received_at      timestamp,
    rec_src              varchar not null,
    primary key (link_hk, load_dts)
);

create table if not exists pharmacovigilance_vault.sat_signal_state (
    signal_hk            bytea not null references pharmacovigilance_vault.hub_signal(signal_hk),
    load_dts             timestamp not null,
    load_end_dts         timestamp,
    hash_diff            bytea not null,
    detected_at          timestamp not null,
    detection_method     varchar(32) not null,
    disproportionality   numeric(8, 4),
    status               varchar(16) not null,
    label_change_recommended boolean not null default false,
    rec_src              varchar not null,
    primary key (signal_hk, load_dts)
);

create table if not exists pharmacovigilance_vault.sat_patient_descriptive (
    patient_hk           bytea not null references pharmacovigilance_vault.hub_patient(patient_hk),
    load_dts             timestamp not null,
    load_end_dts         timestamp,
    hash_diff            bytea not null,
    age                  smallint,
    sex                  varchar(1),
    country_iso2         varchar(2),
    weight_kg            numeric(6, 2),
    rec_src              varchar not null,
    primary key (patient_hk, load_dts)
);
