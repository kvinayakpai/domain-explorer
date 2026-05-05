-- =============================================================================
-- Pharmacovigilance — 3NF schema (excerpt)
-- ICSR intake through MedDRA coding, regulatory submission, and signal mgmt.
-- =============================================================================

create schema if not exists pharmacovigilance_3nf;

create table if not exists pharmacovigilance_3nf.product (
    product_id           varchar primary key,
    brand_name           varchar not null,
    inn                  varchar not null,
    atc_code             varchar(8),
    therapeutic_area     varchar(64),
    is_marketed          boolean not null default true
);

create table if not exists pharmacovigilance_3nf.product_authorization (
    auth_id              varchar primary key,
    product_id           varchar not null references pharmacovigilance_3nf.product(product_id),
    region_iso           varchar(8) not null,
    authorization_holder varchar not null,
    auth_status          varchar(16) not null,
    issued_date          date not null
);

create table if not exists pharmacovigilance_3nf.patient (
    patient_id           varchar primary key,
    age                  smallint,
    sex                  varchar(1),
    country_iso2         varchar(2),
    weight_kg            numeric(6, 2)
);

create table if not exists pharmacovigilance_3nf.reporter (
    reporter_id          varchar primary key,
    reporter_type        varchar(16) not null,
    qualification        varchar(16),
    country_iso2         varchar(2)
);

create table if not exists pharmacovigilance_3nf.case_intake (
    intake_id            varchar primary key,
    intake_channel       varchar(16) not null,
    received_at          timestamp not null,
    source_system        varchar(32) not null,
    initial_artifact_uri varchar
);

create table if not exists pharmacovigilance_3nf.icsr (
    icsr_id              varchar primary key,
    intake_id            varchar references pharmacovigilance_3nf.case_intake(intake_id),
    patient_id           varchar references pharmacovigilance_3nf.patient(patient_id),
    reporter_id          varchar references pharmacovigilance_3nf.reporter(reporter_id),
    case_version         smallint not null,
    case_state           varchar(16) not null,
    seriousness          varchar(16) not null,
    expectedness         varchar(16),
    causality            varchar(16),
    intake_country       varchar(2),
    closed_at            timestamp
);

create table if not exists pharmacovigilance_3nf.adverse_event (
    ae_id                varchar primary key,
    icsr_id              varchar not null references pharmacovigilance_3nf.icsr(icsr_id),
    onset_date           date,
    end_date             date,
    outcome              varchar(16),
    free_text            text
);

create table if not exists pharmacovigilance_3nf.meddra_term (
    pt_code              varchar(16) primary key,
    pt_name              varchar not null,
    soc_code             varchar(16) not null,
    soc_name             varchar not null,
    hlt_code             varchar(16),
    hlgt_code            varchar(16)
);

create table if not exists pharmacovigilance_3nf.ae_meddra_coding (
    ae_id                varchar not null references pharmacovigilance_3nf.adverse_event(ae_id),
    pt_code              varchar(16) not null references pharmacovigilance_3nf.meddra_term(pt_code),
    coded_at             timestamp not null,
    coder_id             varchar not null,
    primary key (ae_id, pt_code)
);

create table if not exists pharmacovigilance_3nf.suspect_product (
    icsr_id              varchar not null references pharmacovigilance_3nf.icsr(icsr_id),
    product_id           varchar not null references pharmacovigilance_3nf.product(product_id),
    role                 varchar(16) not null,
    dose_text            varchar,
    indication           varchar,
    primary key (icsr_id, product_id, role)
);

create table if not exists pharmacovigilance_3nf.medical_review (
    review_id            varchar primary key,
    icsr_id              varchar not null references pharmacovigilance_3nf.icsr(icsr_id),
    reviewer_id          varchar not null,
    reviewed_at          timestamp not null,
    causality_assigned   varchar(16) not null,
    review_notes         text
);

create table if not exists pharmacovigilance_3nf.regulatory_submission (
    submission_id        varchar primary key,
    icsr_id              varchar not null references pharmacovigilance_3nf.icsr(icsr_id),
    target_authority     varchar(16) not null,
    submission_type      varchar(16) not null,
    due_date             date not null,
    submitted_at         timestamp,
    transmission_status  varchar(16) not null,
    ack_received_at      timestamp
);

create table if not exists pharmacovigilance_3nf.signal_record (
    signal_id            varchar primary key,
    product_id           varchar not null references pharmacovigilance_3nf.product(product_id),
    pt_code              varchar(16) not null references pharmacovigilance_3nf.meddra_term(pt_code),
    detected_at          timestamp not null,
    detection_method     varchar(32) not null,
    disproportionality   numeric(8, 4),
    status               varchar(16) not null
);

create table if not exists pharmacovigilance_3nf.signal_evaluation (
    evaluation_id        varchar primary key,
    signal_id            varchar not null references pharmacovigilance_3nf.signal_record(signal_id),
    evaluated_at         timestamp not null,
    outcome              varchar(16) not null,
    label_change_recommended boolean not null default false
);

create table if not exists pharmacovigilance_3nf.literature_reference (
    reference_id         varchar primary key,
    icsr_id              varchar references pharmacovigilance_3nf.icsr(icsr_id),
    citation             varchar not null,
    pubmed_id            varchar(16),
    captured_at          timestamp not null
);

create table if not exists pharmacovigilance_3nf.audit_log (
    audit_id             varchar primary key,
    entity_type          varchar(32) not null,
    entity_id            varchar not null,
    action               varchar(16) not null,
    actor_id             varchar not null,
    action_ts            timestamp not null,
    before_value         text,
    after_value          text
);

create table if not exists pharmacovigilance_3nf.risk_minimization (
    rm_id                varchar primary key,
    product_id           varchar not null references pharmacovigilance_3nf.product(product_id),
    measure_type         varchar(32) not null,
    description          text not null,
    effective_from       date not null,
    effective_to         date
);
