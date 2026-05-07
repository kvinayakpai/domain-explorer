-- =============================================================================
-- Clinical Trials — 3NF schema
-- Source standards: CDISC SDTM v2.0/IG v3.4 (DM, AE, CM, EX, LB, VS, SV, DV),
-- CDISC ADaM v1.3 (ADSL, ADAE, ADTTE), CDISC ODM-XML / Define-XML v2.1.
-- =============================================================================

create schema if not exists clinical_trials_3nf;

create table if not exists clinical_trials_3nf.study (
    study_id              varchar primary key,
    nct_number            varchar(11),
    eudract_number        varchar(14),
    protocol_id           varchar(32),
    phase                 varchar(8),
    therapeutic_area      varchar(64),
    indication_meddra_pt  varchar(64),
    study_design          varchar(64),
    blinding              varchar(16),
    control_type          varchar(16),
    planned_subjects      integer,
    planned_sites         integer,
    sponsor_org           varchar(128),
    cro_org               varchar(128),
    status                varchar(16) not null,
    planned_start_date    date,
    planned_end_date      date,
    actual_start_date     date,
    actual_end_date       date
);

create table if not exists clinical_trials_3nf.protocol_version (
    protocol_version_id  varchar primary key,
    study_id             varchar not null references clinical_trials_3nf.study(study_id),
    version              varchar(16) not null,
    amendment_number     smallint not null,
    effective_date       date not null,
    rationale            text,
    country_specific     varchar(2),
    ethics_approval_date date
);

create table if not exists clinical_trials_3nf.site (
    site_id                  varchar primary key,
    study_id                 varchar not null references clinical_trials_3nf.study(study_id),
    site_number              varchar(16) not null,
    name                     varchar(255) not null,
    country_iso              varchar(2),
    city                     varchar(64),
    principal_investigator_id varchar,
    irb_iec_name             varchar(255),
    contract_executed_date   date,
    ssu_complete_date        date,
    site_activation_date     date,
    status                   varchar(16) not null,
    closed_date              date
);

create table if not exists clinical_trials_3nf.investigator (
    investigator_id      varchar primary key,
    site_id              varchar not null references clinical_trials_3nf.site(site_id),
    family_name          varchar(128) not null,
    given_names          varchar(255),
    role                 varchar(16) not null,
    cv_received_date     date,
    form_1572_signed_date date,
    gcp_training_date    date,
    license_number       varchar(32),
    orcid                varchar(19)
);

create table if not exists clinical_trials_3nf.subject (
    subject_id          varchar primary key,
    study_id            varchar not null references clinical_trials_3nf.study(study_id),
    site_id             varchar not null references clinical_trials_3nf.site(site_id),
    subject_no          varchar(16) not null,
    screening_id        varchar(16),
    arm_code            varchar(8),
    arm                 varchar(64),
    treatment_arm       varchar(64),
    sex                 varchar(1),
    race_code           varchar(8),
    ethnic_code         varchar(8),
    birth_year          smallint,
    age_at_screening    smallint,
    country_iso         varchar(2),
    rfstdtc             timestamp,
    rfendtc             timestamp,
    dthdtc              date,
    dscompletion_status varchar(16)
);

create table if not exists clinical_trials_3nf.informed_consent (
    consent_id            varchar primary key,
    subject_id            varchar not null references clinical_trials_3nf.subject(subject_id),
    protocol_version_id   varchar not null references clinical_trials_3nf.protocol_version(protocol_version_id),
    consent_form_version  varchar(16) not null,
    consented_at          timestamp not null,
    language              varchar(8),
    witnessed_by          varchar(128),
    status                varchar(16) not null,
    withdrawal_ts         timestamp
);

create table if not exists clinical_trials_3nf.visit (
    visit_occurrence_id varchar primary key,
    subject_id          varchar not null references clinical_trials_3nf.subject(subject_id),
    visit_num           smallint not null,
    visit               varchar(64) not null,
    visit_dy            smallint,
    planned_dt          date,
    actual_dt           date,
    window_lower_dy     smallint,
    window_upper_dy     smallint,
    visit_status        varchar(16) not null,
    epoch               varchar(32)
);

create table if not exists clinical_trials_3nf.crf_item (
    crf_item_id         varchar primary key,
    study_id            varchar not null references clinical_trials_3nf.study(study_id),
    form_oid            varchar(64) not null,
    item_oid            varchar(64) not null,
    item_name           varchar(64),
    prompt_text         varchar(255),
    data_type           varchar(16) not null,
    codelist_oid        varchar(64),
    sdtm_domain         varchar(8),
    sdtm_variable       varchar(16),
    cdash_var_name      varchar(16),
    required            boolean not null default false,
    define_xml_origin   varchar(16)
);

create table if not exists clinical_trials_3nf.crf_data_point (
    data_point_id        bigint primary key,
    subject_id           varchar not null references clinical_trials_3nf.subject(subject_id),
    visit_occurrence_id  varchar references clinical_trials_3nf.visit(visit_occurrence_id),
    crf_item_id          varchar not null references clinical_trials_3nf.crf_item(crf_item_id),
    value_text           text,
    value_numeric        numeric(20, 6),
    value_date           date,
    value_codelist_code  varchar(32),
    source_doc_uri       varchar(255),
    entered_by           varchar,
    entered_ts           timestamp not null,
    locked_ts            timestamp,
    status               varchar(16) not null
);

create table if not exists clinical_trials_3nf.data_query (
    query_id        varchar primary key,
    subject_id      varchar not null references clinical_trials_3nf.subject(subject_id),
    data_point_id   bigint references clinical_trials_3nf.crf_data_point(data_point_id),
    opened_ts       timestamp not null,
    opened_by       varchar,
    query_text      text,
    response_text   text,
    closed_ts       timestamp,
    closed_by       varchar,
    status          varchar(16) not null
);

create table if not exists clinical_trials_3nf.adverse_event (
    ae_id      varchar primary key,
    subject_id varchar not null references clinical_trials_3nf.subject(subject_id),
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
    aeongo     varchar(1)
);

create table if not exists clinical_trials_3nf.concomitant_medication (
    cm_id      varchar primary key,
    subject_id varchar not null references clinical_trials_3nf.subject(subject_id),
    cmtrt      varchar(255) not null,
    cmdecod    varchar(128),
    cmclas     varchar(64),
    cmdose     numeric(12, 3),
    cmdosu     varchar(16),
    cmroute    varchar(16),
    cmstdtc    timestamp,
    cmendtc    timestamp,
    cmindc     varchar(255)
);

create table if not exists clinical_trials_3nf.exposure (
    exposure_id          varchar primary key,
    subject_id           varchar not null references clinical_trials_3nf.subject(subject_id),
    extrt                varchar(64),
    exdose               numeric(12, 3),
    exdosu               varchar(16),
    exdosfrm             varchar(16),
    exroute              varchar(16),
    exstdtc              timestamp,
    exendtc              timestamp,
    visit_occurrence_id  varchar references clinical_trials_3nf.visit(visit_occurrence_id),
    lot_number           varchar(32)
);

create table if not exists clinical_trials_3nf.lab_result (
    lb_id               varchar primary key,
    subject_id          varchar not null references clinical_trials_3nf.subject(subject_id),
    visit_occurrence_id varchar references clinical_trials_3nf.visit(visit_occurrence_id),
    lbtestcd            varchar(8) not null,
    lbtest              varchar(40),
    lbcat               varchar(40),
    lbspec              varchar(40),
    lborres             varchar(64),
    lborresu            varchar(16),
    lbstresn            numeric(20, 6),
    lbstresu            varchar(16),
    lbornrlo            varchar(16),
    lbornrhi            varchar(16),
    lbnrind             varchar(8),
    lbdtc               timestamp
);

create table if not exists clinical_trials_3nf.vital_signs (
    vs_id               varchar primary key,
    subject_id          varchar not null references clinical_trials_3nf.subject(subject_id),
    visit_occurrence_id varchar references clinical_trials_3nf.visit(visit_occurrence_id),
    vstestcd            varchar(8) not null,
    vstest              varchar(40),
    vsorres             varchar(32),
    vsstresn            numeric(12, 3),
    vsstresu            varchar(16),
    vsdtc               timestamp,
    vspos               varchar(16)
);

create table if not exists clinical_trials_3nf.protocol_deviation (
    deviation_id     varchar primary key,
    subject_id       varchar not null references clinical_trials_3nf.subject(subject_id),
    dvterm           varchar(255),
    dvdecod          varchar(64),
    dvscat           varchar(64),
    severity         varchar(16) not null,
    dvstdtc          timestamp,
    reported_to_irb  boolean
);

create table if not exists clinical_trials_3nf.adam_dataset (
    adam_dataset_id   varchar primary key,
    study_id          varchar not null references clinical_trials_3nf.study(study_id),
    dataset_name      varchar(16) not null,
    structure         varchar(32),
    parameter_count   smallint,
    usubjid_count     integer,
    define_xml_uri    varchar(255),
    lock_status       varchar(16) not null,
    snapshot_ts       timestamp
);

create table if not exists clinical_trials_3nf.define_xml_codelist (
    codelist_oid                 varchar(64) primary key,
    study_id                     varchar not null references clinical_trials_3nf.study(study_id),
    name                         varchar(64) not null,
    data_type                    varchar(16),
    nci_codelist_code            varchar(16),
    external_dictionary          varchar(32),
    external_dictionary_version  varchar(16)
);

create table if not exists clinical_trials_3nf.database_lock (
    lock_id         varchar primary key,
    study_id        varchar not null references clinical_trials_3nf.study(study_id),
    lock_type       varchar(16) not null,
    locked_at       timestamp not null,
    locked_by       varchar,
    cutoff_date     date,
    define_xml_uri  varchar(255),
    snapshot_label  varchar(64)
);
