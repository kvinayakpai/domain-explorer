-- =============================================================================
-- Clinical Trials — Data Vault 2.0
-- Hubs: study, site, subject, crf_item, adam_dataset. Bitemporal sat for CRF
-- data points so locked / unlocked / re-edited states are reconstructable.
-- =============================================================================

create schema if not exists clinical_trials_vault;

create table if not exists clinical_trials_vault.hub_study (
    study_hk    bytea primary key,
    study_bk    varchar not null,
    nct_number  varchar(11),
    load_dts    timestamp not null,
    rec_src     varchar not null
);

create table if not exists clinical_trials_vault.hub_site (
    site_hk     bytea primary key,
    site_bk     varchar not null,
    load_dts    timestamp not null,
    rec_src     varchar not null
);

create table if not exists clinical_trials_vault.hub_subject (
    subject_hk  bytea primary key,
    usubjid     varchar not null,
    load_dts    timestamp not null,
    rec_src     varchar not null
);

create table if not exists clinical_trials_vault.hub_crf_item (
    crf_item_hk bytea primary key,
    crf_item_bk varchar not null,
    load_dts    timestamp not null,
    rec_src     varchar not null
);

create table if not exists clinical_trials_vault.hub_adam_dataset (
    adam_dataset_hk bytea primary key,
    adam_dataset_bk varchar not null,
    load_dts        timestamp not null,
    rec_src         varchar not null
);

-- ---------------------------------------------------------------------------
-- Links
-- ---------------------------------------------------------------------------
create table if not exists clinical_trials_vault.link_subject_site (
    link_hk    bytea primary key,
    subject_hk bytea not null references clinical_trials_vault.hub_subject(subject_hk),
    site_hk    bytea not null references clinical_trials_vault.hub_site(site_hk),
    study_hk   bytea not null references clinical_trials_vault.hub_study(study_hk),
    load_dts   timestamp not null,
    rec_src    varchar not null
);

create table if not exists clinical_trials_vault.link_subject_crf_data (
    link_hk      bytea primary key,
    subject_hk   bytea not null references clinical_trials_vault.hub_subject(subject_hk),
    crf_item_hk  bytea not null references clinical_trials_vault.hub_crf_item(crf_item_hk),
    visit_bk     varchar not null,
    data_point_bk varchar not null,
    load_dts     timestamp not null,
    rec_src      varchar not null
);

create table if not exists clinical_trials_vault.link_subject_ae (
    link_hk    bytea primary key,
    subject_hk bytea not null references clinical_trials_vault.hub_subject(subject_hk),
    ae_bk      varchar not null,
    load_dts   timestamp not null,
    rec_src    varchar not null
);

create table if not exists clinical_trials_vault.link_subject_visit (
    link_hk    bytea primary key,
    subject_hk bytea not null references clinical_trials_vault.hub_subject(subject_hk),
    visit_bk   varchar not null,
    load_dts   timestamp not null,
    rec_src    varchar not null
);

create table if not exists clinical_trials_vault.link_adam_study (
    link_hk         bytea primary key,
    adam_dataset_hk bytea not null references clinical_trials_vault.hub_adam_dataset(adam_dataset_hk),
    study_hk        bytea not null references clinical_trials_vault.hub_study(study_hk),
    load_dts        timestamp not null,
    rec_src         varchar not null
);

-- ---------------------------------------------------------------------------
-- Satellites (bitemporal)
-- ---------------------------------------------------------------------------
create table if not exists clinical_trials_vault.sat_study_descriptive (
    study_hk         bytea not null references clinical_trials_vault.hub_study(study_hk),
    load_dts         timestamp not null,
    load_end_dts     timestamp,
    hash_diff        bytea not null,
    phase            varchar(8),
    therapeutic_area varchar(64),
    study_design     varchar(64),
    blinding         varchar(16),
    planned_subjects integer,
    planned_sites    integer,
    sponsor_org      varchar(128),
    cro_org          varchar(128),
    status           varchar(16) not null,
    rec_src          varchar not null,
    primary key (study_hk, load_dts)
);

create table if not exists clinical_trials_vault.sat_site_state (
    site_hk                bytea not null references clinical_trials_vault.hub_site(site_hk),
    load_dts               timestamp not null,
    load_end_dts           timestamp,
    hash_diff              bytea not null,
    name                   varchar(255),
    country_iso            varchar(2),
    contract_executed_date date,
    site_activation_date   date,
    status                 varchar(16) not null,
    closed_date            date,
    rec_src                varchar not null,
    primary key (site_hk, load_dts)
);

create table if not exists clinical_trials_vault.sat_subject_state (
    subject_hk          bytea not null references clinical_trials_vault.hub_subject(subject_hk),
    load_dts            timestamp not null,
    load_end_dts        timestamp,
    hash_diff           bytea not null,
    arm_code            varchar(8),
    arm                 varchar(64),
    treatment_arm       varchar(64),
    rfstdtc             timestamp,
    rfendtc             timestamp,
    dscompletion_status varchar(16),
    rec_src             varchar not null,
    primary key (subject_hk, load_dts)
);

create table if not exists clinical_trials_vault.sat_crf_data (
    link_hk             bytea not null,
    load_dts            timestamp not null,
    load_end_dts        timestamp,
    hash_diff           bytea not null,
    value_text          text,
    value_numeric       numeric(20, 6),
    value_date          date,
    value_codelist_code varchar(32),
    entered_by          varchar,
    entered_ts          timestamp,
    locked_ts           timestamp,
    status              varchar(16) not null,
    rec_src             varchar not null,
    primary key (link_hk, load_dts)
);

create table if not exists clinical_trials_vault.sat_adverse_event (
    link_hk    bytea not null,
    load_dts   timestamp not null,
    load_end_dts timestamp,
    hash_diff  bytea not null,
    aeterm     varchar(255) not null,
    aedecod    varchar(128),
    aebodsys   varchar(128),
    aesev      varchar(8),
    aeser      varchar(1),
    aerel      varchar(16),
    aeact      varchar(64),
    aeout      varchar(64),
    aestdtc    timestamp,
    aeendtc    timestamp,
    aeongo     varchar(1),
    rec_src    varchar not null,
    primary key (link_hk, load_dts)
);

create table if not exists clinical_trials_vault.sat_adam_state (
    adam_dataset_hk bytea not null references clinical_trials_vault.hub_adam_dataset(adam_dataset_hk),
    load_dts        timestamp not null,
    load_end_dts    timestamp,
    hash_diff       bytea not null,
    dataset_name    varchar(16) not null,
    structure       varchar(32),
    parameter_count smallint,
    usubjid_count   integer,
    lock_status     varchar(16) not null,
    snapshot_ts     timestamp,
    rec_src         varchar not null,
    primary key (adam_dataset_hk, load_dts)
);

create table if not exists clinical_trials_vault.sat_visit_state (
    link_hk      bytea not null,
    load_dts     timestamp not null,
    load_end_dts timestamp,
    hash_diff    bytea not null,
    visit_num    smallint not null,
    visit_label  varchar(64),
    planned_dt   date,
    actual_dt    date,
    visit_status varchar(16) not null,
    rec_src      varchar not null,
    primary key (link_hk, load_dts)
);
