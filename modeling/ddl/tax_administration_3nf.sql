-- =============================================================================
-- Tax Administration — 3NF schema
-- Source standards: IRS Modernized e-File (MeF) XML schemas (ReturnHeader,
-- ReturnData, IRS-Forms namespace), SSA EFW2/EFW2C, OECD CRS XML, IRS FATCA
-- XML v2.0, state MeF.
-- =============================================================================

create schema if not exists tax_administration_3nf;

create table if not exists tax_administration_3nf.taxpayer (
    taxpayer_id          varchar primary key,
    tin                  varchar(11) not null,
    tin_type             varchar(8) not null,
    legal_name           varchar(255) not null,
    dba                  varchar(255),
    entity_type          varchar(16) not null,
    filing_status        varchar(16),
    tax_year_end_month   smallint,
    address_line1        varchar(255),
    address_line2        varchar(255),
    city                 varchar(64),
    state_code           varchar(2),
    postal_code          varchar(10),
    country_iso          varchar(2),
    foreign_country      varchar(64),
    status               varchar(16) not null,
    registered_at        date
);

create table if not exists tax_administration_3nf.filing_period (
    filing_period_id   varchar primary key,
    tax_year           smallint not null,
    period_type        varchar(8) not null,
    period_start       date not null,
    period_end         date not null,
    due_date           date not null,
    extended_due_date  date
);

create table if not exists tax_administration_3nf.return_header (
    submission_id              varchar(20) primary key,
    taxpayer_id                varchar not null references tax_administration_3nf.taxpayer(taxpayer_id),
    filing_period_id           varchar not null references tax_administration_3nf.filing_period(filing_period_id),
    form_code                  varchar(8) not null,
    form_version               varchar(8),
    tax_year                   smallint not null,
    tax_period_begin           date,
    tax_period_end             date,
    return_type_code           varchar(16),
    filer_type                 varchar(8),
    address_change_indicator   boolean not null default false,
    amended_return_indicator   boolean not null default false,
    originator_efin            varchar(6),
    originator_role            varchar(16),
    ero_signature_pin          varchar(11),
    practitioner_pin           varchar(11),
    software_id                varchar(8),
    software_version           varchar(20),
    filing_security_code       varchar(11),
    ip_address                 varchar(45),
    submitted_at               timestamp not null,
    ack_status                 varchar(8),
    ack_received_at            timestamp,
    state_submission_indicator boolean not null default false
);

create table if not exists tax_administration_3nf.return_data (
    return_data_id            varchar primary key,
    submission_id             varchar(20) not null references tax_administration_3nf.return_header(submission_id),
    total_income              numeric(15, 2),
    agi                       numeric(15, 2),
    taxable_income            numeric(15, 2),
    total_tax                 numeric(15, 2),
    total_payments            numeric(15, 2),
    refund_amount             numeric(15, 2),
    amount_owed               numeric(15, 2),
    dependent_count           smallint,
    refund_disposition        varchar(16),
    bank_routing_number_hash  varchar(64),
    bank_account_number_hash  varchar(64)
);

create table if not exists tax_administration_3nf.line_item (
    line_item_id      bigint primary key,
    submission_id     varchar(20) not null references tax_administration_3nf.return_header(submission_id),
    schedule_code     varchar(8),
    line_number       varchar(16) not null,
    line_description  varchar(255),
    amount            numeric(15, 2),
    data_type         varchar(16),
    page              smallint,
    line_token        varchar(64)
);

create table if not exists tax_administration_3nf.information_return (
    info_return_id          varchar primary key,
    payer_tin               varchar(11) not null,
    payer_name              varchar(255) not null,
    recipient_taxpayer_id   varchar references tax_administration_3nf.taxpayer(taxpayer_id),
    form_code               varchar(16) not null,
    tax_year                smallint not null,
    total_amount            numeric(15, 2),
    federal_tax_withheld    numeric(15, 2),
    state_tax_withheld      numeric(15, 2),
    state_code              varchar(2),
    corrected_indicator     boolean not null default false,
    source_filing_type      varchar(16),
    received_at             timestamp not null,
    matched_submission_id   varchar(20),
    match_status            varchar(16) not null default 'unmatched'
);

create table if not exists tax_administration_3nf.assessment (
    assessment_id     varchar primary key,
    taxpayer_id       varchar not null references tax_administration_3nf.taxpayer(taxpayer_id),
    filing_period_id  varchar references tax_administration_3nf.filing_period(filing_period_id),
    submission_id     varchar(20),
    assessment_type   varchar(16) not null,
    assessed_amount   numeric(15, 2) not null,
    penalty_amount    numeric(15, 2) not null default 0,
    interest_amount   numeric(15, 2) not null default 0,
    assessment_date   date not null,
    notice_code       varchar(8),
    status            varchar(16) not null
);

create table if not exists tax_administration_3nf.payment (
    payment_id           varchar primary key,
    taxpayer_id          varchar not null references tax_administration_3nf.taxpayer(taxpayer_id),
    filing_period_id     varchar references tax_administration_3nf.filing_period(filing_period_id),
    payment_type         varchar(16) not null,
    payment_method       varchar(16),
    amount               numeric(15, 2) not null,
    posted_at            timestamp not null,
    status               varchar(16) not null,
    confirmation_number  varchar(32)
);

create table if not exists tax_administration_3nf.refund_disbursement (
    refund_id            varchar primary key,
    submission_id        varchar(20) not null references tax_administration_3nf.return_header(submission_id),
    taxpayer_id          varchar not null references tax_administration_3nf.taxpayer(taxpayer_id),
    refund_amount        numeric(15, 2) not null,
    hold_reason_code     varchar(8),
    held_until           date,
    disbursed_at         timestamp,
    disbursement_method  varchar(16),
    ach_trace_number     varchar(15),
    status               varchar(16) not null
);

create table if not exists tax_administration_3nf.audit_case (
    audit_case_id          varchar primary key,
    taxpayer_id            varchar not null references tax_administration_3nf.taxpayer(taxpayer_id),
    submission_id          varchar(20),
    filing_period_id       varchar references tax_administration_3nf.filing_period(filing_period_id),
    audit_type             varchar(16) not null,
    risk_score             numeric(6, 4),
    selection_program      varchar(32),
    opened_at              date,
    closed_at              date,
    examiner_id            varchar,
    status                 varchar(16) not null,
    outcome                varchar(16),
    adjusted_tax_amount    numeric(15, 2)
);

create table if not exists tax_administration_3nf.examination_finding (
    finding_id          varchar primary key,
    audit_case_id       varchar not null references tax_administration_3nf.audit_case(audit_case_id),
    line_token          varchar(64),
    original_amount     numeric(15, 2),
    adjusted_amount     numeric(15, 2),
    variance            numeric(15, 2),
    code_section        varchar(16),
    penalty_code        varchar(16),
    agreed_indicator    boolean
);

create table if not exists tax_administration_3nf.collection_lien (
    lien_id          varchar primary key,
    taxpayer_id      varchar not null references tax_administration_3nf.taxpayer(taxpayer_id),
    assessment_id    varchar references tax_administration_3nf.assessment(assessment_id),
    lien_amount      numeric(15, 2) not null,
    filed_at         date not null,
    county_recorder  varchar(64),
    state_code       varchar(2),
    serial_number    varchar(32),
    released_at      date,
    status           varchar(16) not null
);

create table if not exists tax_administration_3nf.installment_agreement (
    agreement_id     varchar primary key,
    taxpayer_id      varchar not null references tax_administration_3nf.taxpayer(taxpayer_id),
    total_balance    numeric(15, 2) not null,
    monthly_payment  numeric(15, 2) not null,
    payment_method   varchar(16),
    status           varchar(16) not null,
    effective_date   date,
    closed_date      date
);

create table if not exists tax_administration_3nf.crs_account_record (
    crs_record_id              varchar primary key,
    account_holder_taxpayer_id varchar references tax_administration_3nf.taxpayer(taxpayer_id),
    reporting_fi_giin          varchar(19),
    reporting_fi_name          varchar(255),
    account_number             varchar(64) not null,
    account_holder_type        varchar(8),
    residence_country_iso      varchar(2),
    account_balance            numeric(20, 2),
    balance_currency           varchar(3),
    payment_dividends          numeric(20, 2),
    payment_interest           numeric(20, 2),
    payment_gross_proceeds     numeric(20, 2),
    payment_other              numeric(20, 2),
    report_period_end          date,
    docref_id                  varchar(64) not null,
    corr_docref_id             varchar(64),
    status                     varchar(16) not null
);

create table if not exists tax_administration_3nf.fatca_record (
    fatca_record_id            varchar primary key,
    account_holder_taxpayer_id varchar references tax_administration_3nf.taxpayer(taxpayer_id),
    reporting_fi_giin          varchar(19),
    account_number             varchar(64) not null,
    account_balance_usd        numeric(20, 2),
    payments_dividends_usd     numeric(20, 2),
    payments_interest_usd      numeric(20, 2),
    report_period_end          date,
    docref_id                  varchar(64) not null,
    corr_docref_id             varchar(64),
    status                     varchar(16) not null
);

create table if not exists tax_administration_3nf.notice (
    notice_id          varchar primary key,
    taxpayer_id        varchar not null references tax_administration_3nf.taxpayer(taxpayer_id),
    notice_code        varchar(8) not null,
    notice_type        varchar(32),
    tax_period_id      varchar,
    amount_due         numeric(15, 2),
    response_due_date  date,
    sent_at            timestamp not null,
    delivery_channel   varchar(16),
    status             varchar(16) not null
);
