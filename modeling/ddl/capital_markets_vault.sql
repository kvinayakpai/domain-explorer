-- =============================================================================
-- Capital Markets — Data Vault 2.0
-- Hubs: order, trade, instrument, counterparty, account, settlement_instruction.
-- Bitemporal sat for FpML trade state and lifecycle events.
-- =============================================================================

create schema if not exists capital_markets_vault;

-- ---------------------------------------------------------------------------
-- Hubs
-- ---------------------------------------------------------------------------
create table if not exists capital_markets_vault.hub_order (
    order_hk     bytea primary key,
    order_bk     varchar not null,
    load_dts     timestamp not null,
    rec_src      varchar not null
);

create table if not exists capital_markets_vault.hub_trade (
    trade_hk     bytea primary key,
    trade_bk     varchar not null,
    usi          varchar(64),
    load_dts     timestamp not null,
    rec_src      varchar not null
);

create table if not exists capital_markets_vault.hub_instrument (
    instrument_hk bytea primary key,
    instrument_bk varchar not null,
    isin          varchar(12),
    load_dts      timestamp not null,
    rec_src       varchar not null
);

create table if not exists capital_markets_vault.hub_counterparty (
    counterparty_hk bytea primary key,
    counterparty_bk varchar not null,
    lei             varchar(20),
    load_dts        timestamp not null,
    rec_src         varchar not null
);

create table if not exists capital_markets_vault.hub_account (
    account_hk   bytea primary key,
    account_bk   varchar not null,
    load_dts     timestamp not null,
    rec_src      varchar not null
);

create table if not exists capital_markets_vault.hub_settlement_instruction (
    ssi_hk       bytea primary key,
    ssi_bk       varchar not null,
    load_dts     timestamp not null,
    rec_src      varchar not null
);

-- ---------------------------------------------------------------------------
-- Links
-- ---------------------------------------------------------------------------
create table if not exists capital_markets_vault.link_order_instrument (
    link_hk      bytea primary key,
    order_hk     bytea not null references capital_markets_vault.hub_order(order_hk),
    instrument_hk bytea not null references capital_markets_vault.hub_instrument(instrument_hk),
    account_hk   bytea not null references capital_markets_vault.hub_account(account_hk),
    load_dts     timestamp not null,
    rec_src      varchar not null
);

create table if not exists capital_markets_vault.link_trade_components (
    link_hk         bytea primary key,
    trade_hk        bytea not null references capital_markets_vault.hub_trade(trade_hk),
    instrument_hk   bytea not null references capital_markets_vault.hub_instrument(instrument_hk),
    account_hk      bytea not null references capital_markets_vault.hub_account(account_hk),
    counterparty_hk bytea not null references capital_markets_vault.hub_counterparty(counterparty_hk),
    load_dts        timestamp not null,
    rec_src         varchar not null
);

create table if not exists capital_markets_vault.link_trade_settlement (
    link_hk      bytea primary key,
    trade_hk     bytea not null references capital_markets_vault.hub_trade(trade_hk),
    ssi_hk       bytea not null references capital_markets_vault.hub_settlement_instruction(ssi_hk),
    load_dts     timestamp not null,
    rec_src      varchar not null
);

create table if not exists capital_markets_vault.link_order_execution (
    link_hk      bytea primary key,
    order_hk     bytea not null references capital_markets_vault.hub_order(order_hk),
    exec_bk      varchar not null,
    trade_hk     bytea references capital_markets_vault.hub_trade(trade_hk),
    load_dts     timestamp not null,
    rec_src      varchar not null
);

-- ---------------------------------------------------------------------------
-- Satellites (bitemporal)
-- ---------------------------------------------------------------------------
create table if not exists capital_markets_vault.sat_order_state (
    order_hk      bytea not null references capital_markets_vault.hub_order(order_hk),
    load_dts      timestamp not null,
    load_end_dts  timestamp,
    hash_diff     bytea not null,
    side          varchar(8) not null,
    order_qty     numeric(20, 4) not null,
    price         numeric(20, 8),
    ord_type      varchar(8) not null,
    time_in_force varchar(8) not null,
    order_status  varchar(8) not null,
    leaves_qty    numeric(20, 4),
    cum_qty       numeric(20, 4),
    avg_px        numeric(20, 8),
    rec_src       varchar not null,
    primary key (order_hk, load_dts)
);

create table if not exists capital_markets_vault.sat_trade_state (
    trade_hk             bytea not null references capital_markets_vault.hub_trade(trade_hk),
    load_dts             timestamp not null,
    load_end_dts         timestamp,
    hash_diff            bytea not null,
    side                 varchar(8) not null,
    trade_qty            numeric(20, 4) not null,
    trade_price          numeric(20, 8) not null,
    notional             numeric(20, 4),
    notional_currency    varchar(3),
    settlement_date      date,
    clearing_status      varchar(16) not null,
    product_type_fpml    varchar(64),
    ccp_id               varchar,
    master_agreement_id  varchar,
    rec_src              varchar not null,
    primary key (trade_hk, load_dts)
);

create table if not exists capital_markets_vault.sat_instrument_descriptive (
    instrument_hk    bytea not null references capital_markets_vault.hub_instrument(instrument_hk),
    load_dts         timestamp not null,
    load_end_dts     timestamp,
    hash_diff        bytea not null,
    symbol           varchar(16),
    security_type    varchar(16) not null,
    cfi_code         varchar(6),
    currency         varchar(3) not null,
    maturity_date    date,
    contract_multiplier numeric(18, 6),
    tick_size        numeric(18, 8),
    status           varchar(16) not null,
    rec_src          varchar not null,
    primary key (instrument_hk, load_dts)
);

create table if not exists capital_markets_vault.sat_counterparty_credit (
    counterparty_hk bytea not null references capital_markets_vault.hub_counterparty(counterparty_hk),
    load_dts        timestamp not null,
    load_end_dts    timestamp,
    hash_diff       bytea not null,
    credit_rating   varchar(8),
    parent_lei      varchar(20),
    status          varchar(16) not null,
    rec_src         varchar not null,
    primary key (counterparty_hk, load_dts)
);

create table if not exists capital_markets_vault.sat_settlement_state (
    ssi_hk              bytea not null references capital_markets_vault.hub_settlement_instruction(ssi_hk),
    load_dts            timestamp not null,
    load_end_dts        timestamp,
    hash_diff           bytea not null,
    settlement_amount   numeric(20, 4) not null,
    settlement_currency varchar(3) not null,
    settlement_quantity numeric(20, 4) not null,
    settlement_date     date not null,
    delivery_type       varchar(8) not null,
    payment_type        varchar(8),
    status              varchar(16) not null,
    matched_ts          timestamp,
    settled_ts          timestamp,
    rec_src             varchar not null,
    primary key (ssi_hk, load_dts)
);

create table if not exists capital_markets_vault.sat_lifecycle_event (
    trade_hk         bytea not null references capital_markets_vault.hub_trade(trade_hk),
    event_bk         varchar not null,
    load_dts         timestamp not null,
    hash_diff        bytea not null,
    event_type       varchar(32) not null,
    effective_date   date not null,
    payment_date     date,
    payment_amount   numeric(20, 4),
    payment_currency varchar(3),
    reset_rate       numeric(12, 9),
    index_name       varchar(32),
    rec_src          varchar not null,
    primary key (trade_hk, event_bk, load_dts)
);

create table if not exists capital_markets_vault.sat_margin_call (
    counterparty_hk          bytea not null references capital_markets_vault.hub_counterparty(counterparty_hk),
    margin_call_bk           varchar not null,
    load_dts                 timestamp not null,
    hash_diff                bytea not null,
    call_type                varchar(16) not null,
    call_amount              numeric(20, 4) not null,
    call_currency            varchar(3) not null,
    due_ts                   timestamp not null,
    status                   varchar(16) not null,
    collateral_pledged_value numeric(20, 4),
    rec_src                  varchar not null,
    primary key (counterparty_hk, margin_call_bk, load_dts)
);
