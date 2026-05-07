-- =============================================================================
-- Settlement & Clearing — Data Vault 2.0
-- Hubs: party, instrument, safekeeping_account, cash_account,
--       settlement_instruction, csd, ccp, margin_call.
-- Sat hash_diff lets us replay every status hop emitted as ISO 20022
-- sese.024 across the trade-to-settled lifecycle without overwriting.
-- =============================================================================

create schema if not exists settlement_clearing_vault;

-- ---------------------------------------------------------------------------
-- Hubs (one per business key)
-- ---------------------------------------------------------------------------
create table if not exists settlement_clearing_vault.hub_party (
    party_hk   bytea primary key,
    party_bk   varchar not null,           -- LEI or internal party id
    load_dts   timestamp not null,
    rec_src    varchar not null
);

create table if not exists settlement_clearing_vault.hub_instrument (
    instrument_hk   bytea primary key,
    instrument_bk   varchar not null,      -- ISIN or internal id
    load_dts        timestamp not null,
    rec_src         varchar not null
);

create table if not exists settlement_clearing_vault.hub_safekeeping_account (
    safekeeping_account_hk   bytea primary key,
    safekeeping_account_bk   varchar not null,
    load_dts                 timestamp not null,
    rec_src                  varchar not null
);

create table if not exists settlement_clearing_vault.hub_cash_account (
    cash_account_hk   bytea primary key,
    cash_account_bk   varchar not null,
    load_dts          timestamp not null,
    rec_src           varchar not null
);

create table if not exists settlement_clearing_vault.hub_ssi (
    ssi_hk     bytea primary key,
    ssi_bk     varchar not null,           -- TransactionIdentification
    load_dts   timestamp not null,
    rec_src    varchar not null
);

create table if not exists settlement_clearing_vault.hub_csd (
    csd_hk     bytea primary key,
    csd_bk     varchar not null,
    load_dts   timestamp not null,
    rec_src    varchar not null
);

create table if not exists settlement_clearing_vault.hub_ccp (
    ccp_hk     bytea primary key,
    ccp_bk     varchar not null,
    load_dts   timestamp not null,
    rec_src    varchar not null
);

create table if not exists settlement_clearing_vault.hub_margin_call (
    margin_call_hk   bytea primary key,
    margin_call_bk   varchar not null,
    load_dts         timestamp not null,
    rec_src          varchar not null
);

-- ---------------------------------------------------------------------------
-- Links (relationships between hubs)
-- ---------------------------------------------------------------------------
create table if not exists settlement_clearing_vault.link_ssi_party (
    link_hk    bytea primary key,
    ssi_hk     bytea not null references settlement_clearing_vault.hub_ssi(ssi_hk),
    party_hk   bytea not null references settlement_clearing_vault.hub_party(party_hk),
    load_dts   timestamp not null,
    rec_src    varchar not null
);

create table if not exists settlement_clearing_vault.link_ssi_account (
    link_hk                 bytea primary key,
    ssi_hk                  bytea not null references settlement_clearing_vault.hub_ssi(ssi_hk),
    safekeeping_account_hk  bytea not null references settlement_clearing_vault.hub_safekeeping_account(safekeeping_account_hk),
    cash_account_hk         bytea references settlement_clearing_vault.hub_cash_account(cash_account_hk),
    instrument_hk           bytea not null references settlement_clearing_vault.hub_instrument(instrument_hk),
    load_dts                timestamp not null,
    rec_src                 varchar not null
);

create table if not exists settlement_clearing_vault.link_safekeeping_csd (
    link_hk                 bytea primary key,
    safekeeping_account_hk  bytea not null references settlement_clearing_vault.hub_safekeeping_account(safekeeping_account_hk),
    csd_hk                  bytea not null references settlement_clearing_vault.hub_csd(csd_hk),
    load_dts                timestamp not null,
    rec_src                 varchar not null
);

create table if not exists settlement_clearing_vault.link_margin_call_ccp (
    link_hk         bytea primary key,
    margin_call_hk  bytea not null references settlement_clearing_vault.hub_margin_call(margin_call_hk),
    ccp_hk          bytea not null references settlement_clearing_vault.hub_ccp(ccp_hk),
    party_hk        bytea not null references settlement_clearing_vault.hub_party(party_hk),
    load_dts        timestamp not null,
    rec_src         varchar not null
);

create table if not exists settlement_clearing_vault.link_collateral_movement (
    link_hk          bytea primary key,
    margin_call_hk   bytea not null references settlement_clearing_vault.hub_margin_call(margin_call_hk),
    instrument_hk    bytea references settlement_clearing_vault.hub_instrument(instrument_hk),
    csd_hk           bytea references settlement_clearing_vault.hub_csd(csd_hk),
    load_dts         timestamp not null,
    rec_src          varchar not null
);

-- ---------------------------------------------------------------------------
-- Satellites (descriptive context, change-tracked via hash_diff)
-- ---------------------------------------------------------------------------
create table if not exists settlement_clearing_vault.sat_party_descriptive (
    party_hk      bytea not null references settlement_clearing_vault.hub_party(party_hk),
    load_dts      timestamp not null,
    load_end_dts  timestamp,
    hash_diff     bytea not null,
    legal_name    varchar(255),
    bic           varchar(11),
    party_role    varchar(16),
    country_iso   varchar(2),
    status        varchar(16),
    rec_src       varchar not null,
    primary key (party_hk, load_dts)
);

create table if not exists settlement_clearing_vault.sat_instrument_descriptive (
    instrument_hk    bytea not null references settlement_clearing_vault.hub_instrument(instrument_hk),
    load_dts         timestamp not null,
    load_end_dts     timestamp,
    hash_diff        bytea not null,
    isin             varchar(12),
    cusip            varchar(9),
    figi             varchar(12),
    cfi_code         varchar(6),
    short_name       varchar(64),
    currency         varchar(3),
    country_of_issue varchar(2),
    maturity_date    date,
    status           varchar(16),
    rec_src          varchar not null,
    primary key (instrument_hk, load_dts)
);

-- Captures every sese.024 status hop without losing prior states.
create table if not exists settlement_clearing_vault.sat_ssi_state (
    ssi_hk                          bytea not null references settlement_clearing_vault.hub_ssi(ssi_hk),
    load_dts                        timestamp not null,
    load_end_dts                    timestamp,
    hash_diff                       bytea not null,
    status                          varchar(16) not null,
    matching_status_code            varchar(8),
    settlement_method               varchar(8),
    delivery_type                   varchar(8),
    payment_type                    varchar(8),
    partial_settlement_indicator    varchar(8),
    hold_indicator                  boolean,
    settlement_quantity             decimal(20,4),
    settlement_amount               decimal(20,4),
    settlement_currency             varchar(3),
    settlement_date                 date,
    rec_src                         varchar not null,
    primary key (ssi_hk, load_dts)
);

create table if not exists settlement_clearing_vault.sat_ssi_failure (
    ssi_hk                  bytea not null references settlement_clearing_vault.hub_ssi(ssi_hk),
    load_dts                timestamp not null,
    load_end_dts            timestamp,
    hash_diff               bytea not null,
    fail_reason_code        varchar(8),
    failed_quantity         decimal(20,4),
    failed_amount           decimal(20,4),
    age_days                smallint,
    csd_penalty_applied     decimal(15,4),
    csdr_penalty_currency   varchar(3),
    rec_src                 varchar not null,
    primary key (ssi_hk, load_dts)
);

create table if not exists settlement_clearing_vault.sat_safekeeping_balance (
    safekeeping_account_hk   bytea not null references settlement_clearing_vault.hub_safekeeping_account(safekeeping_account_hk),
    load_dts                 timestamp not null,
    load_end_dts             timestamp,
    hash_diff                bytea not null,
    instrument_hk            bytea not null references settlement_clearing_vault.hub_instrument(instrument_hk),
    opening_balance          decimal(20,4),
    closing_balance          decimal(20,4),
    pending_in               decimal(20,4),
    pending_out              decimal(20,4),
    rec_src                  varchar not null,
    primary key (safekeeping_account_hk, instrument_hk, load_dts)
);

create table if not exists settlement_clearing_vault.sat_margin_call_state (
    margin_call_hk             bytea not null references settlement_clearing_vault.hub_margin_call(margin_call_hk),
    load_dts                   timestamp not null,
    load_end_dts               timestamp,
    hash_diff                  bytea not null,
    call_type                  varchar(16),
    call_amount                decimal(20,4),
    call_currency              varchar(3),
    call_ts                    timestamp,
    due_ts                     timestamp,
    status                     varchar(16),
    collateral_amount_pledged  decimal(20,4),
    variation_pnl              decimal(20,4),
    rec_src                    varchar not null,
    primary key (margin_call_hk, load_dts)
);

create table if not exists settlement_clearing_vault.sat_cns_obligation (
    party_hk             bytea not null references settlement_clearing_vault.hub_party(party_hk),
    instrument_hk        bytea not null references settlement_clearing_vault.hub_instrument(instrument_hk),
    business_date        date not null,
    load_dts             timestamp not null,
    load_end_dts         timestamp,
    hash_diff            bytea not null,
    long_position_qty    decimal(20,4),
    short_position_qty   decimal(20,4),
    net_position_qty     decimal(20,4),
    net_money            decimal(20,4),
    net_money_currency   varchar(3),
    aged_failures_qty    decimal(20,4),
    rec_src              varchar not null,
    primary key (party_hk, instrument_hk, business_date, load_dts)
);
