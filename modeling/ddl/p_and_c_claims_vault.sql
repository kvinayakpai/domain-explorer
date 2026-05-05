-- =============================================================================
-- P&C Claims — Data Vault 2.0 (excerpt)
-- Hubs / Links / Satellites for the claims domain with bitemporal reserve history.
-- =============================================================================

create schema if not exists p_and_c_claims_vault;

-- Hubs
create table if not exists p_and_c_claims_vault.hub_policy (
    policy_hk            bytea primary key,
    policy_bk            varchar not null,
    load_dts             timestamp not null,
    rec_src              varchar not null
);

create table if not exists p_and_c_claims_vault.hub_policyholder (
    policyholder_hk      bytea primary key,
    policyholder_bk      varchar not null,
    load_dts             timestamp not null,
    rec_src              varchar not null
);

create table if not exists p_and_c_claims_vault.hub_claim (
    claim_hk             bytea primary key,
    claim_bk             varchar not null,
    load_dts             timestamp not null,
    rec_src              varchar not null
);

create table if not exists p_and_c_claims_vault.hub_adjuster (
    adjuster_hk          bytea primary key,
    adjuster_bk          varchar not null,
    load_dts             timestamp not null,
    rec_src              varchar not null
);

create table if not exists p_and_c_claims_vault.hub_payee (
    payee_hk             bytea primary key,
    payee_bk             varchar not null,
    load_dts             timestamp not null,
    rec_src              varchar not null
);

create table if not exists p_and_c_claims_vault.hub_vendor (
    vendor_hk            bytea primary key,
    vendor_bk            varchar not null,
    load_dts             timestamp not null,
    rec_src              varchar not null
);

-- Links
create table if not exists p_and_c_claims_vault.link_claim_policy (
    link_hk              bytea primary key,
    claim_hk             bytea not null references p_and_c_claims_vault.hub_claim(claim_hk),
    policy_hk            bytea not null references p_and_c_claims_vault.hub_policy(policy_hk),
    load_dts             timestamp not null,
    rec_src              varchar not null
);

create table if not exists p_and_c_claims_vault.link_claim_adjuster (
    link_hk              bytea primary key,
    claim_hk             bytea not null references p_and_c_claims_vault.hub_claim(claim_hk),
    adjuster_hk          bytea not null references p_and_c_claims_vault.hub_adjuster(adjuster_hk),
    assigned_ts          timestamp not null,
    load_dts             timestamp not null,
    rec_src              varchar not null
);

create table if not exists p_and_c_claims_vault.link_claim_vendor (
    link_hk              bytea primary key,
    claim_hk             bytea not null references p_and_c_claims_vault.hub_claim(claim_hk),
    vendor_hk            bytea not null references p_and_c_claims_vault.hub_vendor(vendor_hk),
    load_dts             timestamp not null,
    rec_src              varchar not null
);

create table if not exists p_and_c_claims_vault.link_payout (
    link_hk              bytea primary key,
    claim_hk             bytea not null references p_and_c_claims_vault.hub_claim(claim_hk),
    payee_hk             bytea not null references p_and_c_claims_vault.hub_payee(payee_hk),
    payout_bk            varchar not null,
    load_dts             timestamp not null,
    rec_src              varchar not null
);

-- Satellites
create table if not exists p_and_c_claims_vault.sat_claim_state (
    claim_hk             bytea not null references p_and_c_claims_vault.hub_claim(claim_hk),
    load_dts             timestamp not null,
    load_end_dts         timestamp,
    hash_diff            bytea not null,
    status               varchar(16) not null,
    severity             varchar(16) not null,
    loss_type            varchar(32) not null,
    rec_src              varchar not null,
    primary key (claim_hk, load_dts)
);

create table if not exists p_and_c_claims_vault.sat_claim_reserve_bitemporal (
    claim_hk             bytea not null references p_and_c_claims_vault.hub_claim(claim_hk),
    business_effective_ts timestamp not null,
    load_dts             timestamp not null,
    load_end_dts         timestamp,
    hash_diff            bytea not null,
    reserve_type         varchar(16) not null,
    amount               numeric(14, 2) not null,
    set_by               varchar not null,
    rec_src              varchar not null,
    primary key (claim_hk, business_effective_ts, load_dts)
);

create table if not exists p_and_c_claims_vault.sat_policy_descriptive (
    policy_hk            bytea not null references p_and_c_claims_vault.hub_policy(policy_hk),
    load_dts             timestamp not null,
    load_end_dts         timestamp,
    hash_diff            bytea not null,
    product_code         varchar(16) not null,
    state_iso            varchar(2) not null,
    effective_date       date not null,
    expiration_date      date not null,
    premium_amount       numeric(14, 2) not null,
    rec_src              varchar not null,
    primary key (policy_hk, load_dts)
);

create table if not exists p_and_c_claims_vault.sat_policyholder_descriptive (
    policyholder_hk      bytea not null references p_and_c_claims_vault.hub_policyholder(policyholder_hk),
    load_dts             timestamp not null,
    load_end_dts         timestamp,
    hash_diff            bytea not null,
    legal_name           varchar not null,
    party_type           varchar(16) not null,
    state_iso            varchar(2),
    rec_src              varchar not null,
    primary key (policyholder_hk, load_dts)
);

create table if not exists p_and_c_claims_vault.sat_payout_state (
    link_hk              bytea not null,
    load_dts             timestamp not null,
    load_end_dts         timestamp,
    hash_diff            bytea not null,
    payment_method       varchar(16) not null,
    amount               numeric(14, 2) not null,
    issued_ts            timestamp not null,
    cleared_ts           timestamp,
    rec_src              varchar not null,
    primary key (link_hk, load_dts)
);
