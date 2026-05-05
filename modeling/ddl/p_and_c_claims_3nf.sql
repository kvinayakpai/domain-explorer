-- =============================================================================
-- P&C Claims — 3NF schema (excerpt)
-- Property & casualty claims platform — FNOL through payout and recovery.
-- =============================================================================

create schema if not exists p_and_c_claims_3nf;

create table if not exists p_and_c_claims_3nf.policy (
    policy_id            varchar primary key,
    policyholder_id      varchar not null,
    product_code         varchar(16) not null,
    effective_date       date not null,
    expiration_date      date not null,
    premium_amount       numeric(14, 2) not null,
    state_iso            varchar(2) not null,
    is_active            boolean not null default true
);

create table if not exists p_and_c_claims_3nf.policyholder (
    policyholder_id      varchar primary key,
    legal_name           varchar not null,
    party_type           varchar(16) not null,
    address_line1        varchar,
    city                 varchar,
    state_iso            varchar(2),
    postal_code          varchar(16),
    country_iso2         varchar(2)
);

create table if not exists p_and_c_claims_3nf.coverage (
    coverage_id          varchar primary key,
    policy_id            varchar not null references p_and_c_claims_3nf.policy(policy_id),
    coverage_code        varchar(32) not null,
    limit_amount         numeric(14, 2) not null,
    deductible           numeric(14, 2) not null
);

create table if not exists p_and_c_claims_3nf.claim (
    claim_id             varchar primary key,
    policy_id            varchar not null references p_and_c_claims_3nf.policy(policy_id),
    fnol_ts              timestamp not null,
    loss_date            date not null,
    loss_type            varchar(32) not null,
    loss_state_iso       varchar(2) not null,
    severity             varchar(16) not null,
    status               varchar(16) not null,
    closed_ts            timestamp
);

create table if not exists p_and_c_claims_3nf.claimant (
    claimant_id          varchar primary key,
    claim_id             varchar not null references p_and_c_claims_3nf.claim(claim_id),
    legal_name           varchar not null,
    relationship         varchar(32) not null
);

create table if not exists p_and_c_claims_3nf.adjuster (
    adjuster_id          varchar primary key,
    full_name            varchar not null,
    license_state_iso    varchar(2) not null,
    team                 varchar(32) not null,
    is_siu               boolean not null default false
);

create table if not exists p_and_c_claims_3nf.claim_assignment (
    claim_id             varchar not null references p_and_c_claims_3nf.claim(claim_id),
    adjuster_id          varchar not null references p_and_c_claims_3nf.adjuster(adjuster_id),
    assigned_ts          timestamp not null,
    primary key (claim_id, adjuster_id, assigned_ts)
);

create table if not exists p_and_c_claims_3nf.claim_note (
    note_id              varchar primary key,
    claim_id             varchar not null references p_and_c_claims_3nf.claim(claim_id),
    author_id            varchar not null,
    note_ts              timestamp not null,
    note_text            text not null,
    note_type            varchar(16) not null
);

create table if not exists p_and_c_claims_3nf.reserve (
    reserve_id           varchar primary key,
    claim_id             varchar not null references p_and_c_claims_3nf.claim(claim_id),
    reserve_type         varchar(16) not null,
    amount               numeric(14, 2) not null,
    set_ts               timestamp not null,
    set_by               varchar not null,
    is_current           boolean not null
);

create table if not exists p_and_c_claims_3nf.payout (
    payout_id            varchar primary key,
    claim_id             varchar not null references p_and_c_claims_3nf.claim(claim_id),
    payee_party_id       varchar not null,
    payment_method       varchar(16) not null,
    amount               numeric(14, 2) not null,
    issued_ts            timestamp not null,
    cleared_ts           timestamp
);

create table if not exists p_and_c_claims_3nf.recovery (
    recovery_id          varchar primary key,
    claim_id             varchar not null references p_and_c_claims_3nf.claim(claim_id),
    recovery_type        varchar(16) not null,
    amount               numeric(14, 2) not null,
    received_ts          timestamp not null
);

create table if not exists p_and_c_claims_3nf.subrogation (
    subro_id             varchar primary key,
    claim_id             varchar not null references p_and_c_claims_3nf.claim(claim_id),
    third_party          varchar not null,
    pursued_ts           timestamp not null,
    recovered_amount     numeric(14, 2),
    status               varchar(16) not null
);

create table if not exists p_and_c_claims_3nf.fraud_referral (
    referral_id          varchar primary key,
    claim_id             varchar not null references p_and_c_claims_3nf.claim(claim_id),
    referred_ts          timestamp not null,
    risk_score           numeric(5, 2),
    disposition          varchar(16)
);

create table if not exists p_and_c_claims_3nf.litigation (
    litigation_id        varchar primary key,
    claim_id             varchar not null references p_and_c_claims_3nf.claim(claim_id),
    venue                varchar not null,
    filed_ts             timestamp not null,
    closed_ts            timestamp,
    outcome              varchar(32)
);

create table if not exists p_and_c_claims_3nf.fnol_intake (
    intake_id            varchar primary key,
    claim_id             varchar not null references p_and_c_claims_3nf.claim(claim_id),
    channel              varchar(16) not null,
    received_ts          timestamp not null,
    artifact_count       integer not null default 0
);

create table if not exists p_and_c_claims_3nf.claim_artifact (
    artifact_id          varchar primary key,
    claim_id             varchar not null references p_and_c_claims_3nf.claim(claim_id),
    artifact_type        varchar(16) not null,
    storage_uri          varchar not null,
    captured_ts          timestamp not null
);

create table if not exists p_and_c_claims_3nf.vendor (
    vendor_id            varchar primary key,
    vendor_name          varchar not null,
    vendor_type          varchar(32) not null
);

create table if not exists p_and_c_claims_3nf.vendor_assignment (
    vendor_assignment_id varchar primary key,
    claim_id             varchar not null references p_and_c_claims_3nf.claim(claim_id),
    vendor_id            varchar not null references p_and_c_claims_3nf.vendor(vendor_id),
    assigned_ts          timestamp not null,
    fee_amount           numeric(14, 2)
);
