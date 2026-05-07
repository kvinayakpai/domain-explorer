-- =============================================================================
-- Capital Markets — 3NF schema
-- Source standards: FIX 4.4/5.0 SP2 (orders/executions), FpML 5.x (trades,
-- lifecycle events), ISO 20022 securities (sese/semt) for settlement, CFTC
-- Part 43/45 + EMIR/MiFIR for regulatory reporting.
-- =============================================================================

create schema if not exists capital_markets_3nf;

-- ---------------------------------------------------------------------------
-- Reference / master data
-- ---------------------------------------------------------------------------
create table if not exists capital_markets_3nf.counterparty (
    counterparty_id    varchar primary key,
    lei                varchar(20),
    legal_name         varchar(255) not null,
    bic                varchar(11),
    party_type         varchar(16) not null,
    jurisdiction_iso   varchar(2),
    credit_rating      varchar(8),
    parent_lei         varchar(20),
    status             varchar(16) not null,
    onboarded_at       timestamp not null
);

create table if not exists capital_markets_3nf.instrument (
    instrument_id            varchar primary key,
    isin                     varchar(12),
    cusip                    varchar(9),
    figi                     varchar(12),
    ric                      varchar(16),
    symbol                   varchar(16),
    security_type            varchar(16) not null,
    cfi_code                 varchar(6),
    currency                 varchar(3) not null,
    country_of_issue         varchar(2),
    maturity_date            date,
    contract_multiplier      numeric(18, 6),
    tick_size                numeric(18, 8),
    lot_size                 integer,
    underlying_instrument_id varchar,
    product_type_fpml        varchar(64),
    status                   varchar(16) not null
);

create table if not exists capital_markets_3nf.execution_venue (
    venue_id      varchar primary key,
    mic           varchar(4),
    name          varchar(64) not null,
    country_iso   varchar(2),
    venue_type    varchar(16),
    operating_mic varchar(4),
    status        varchar(16) not null
);

create table if not exists capital_markets_3nf.account (
    account_id           varchar primary key,
    counterparty_id      varchar not null references capital_markets_3nf.counterparty(counterparty_id),
    account_type         varchar(16) not null,
    base_currency        varchar(3) not null,
    clearing_account     varchar(32),
    opened_at            date not null,
    closed_at            date,
    investment_objective varchar(64)
);

-- ---------------------------------------------------------------------------
-- Order / execution (FIX)
-- ---------------------------------------------------------------------------
create table if not exists capital_markets_3nf.order (
    order_id          varchar primary key,
    parent_order_id   varchar references capital_markets_3nf.order(order_id),
    orig_cl_ord_id    varchar,
    account_id        varchar not null references capital_markets_3nf.account(account_id),
    instrument_id     varchar not null references capital_markets_3nf.instrument(instrument_id),
    venue_id          varchar references capital_markets_3nf.execution_venue(venue_id),
    side              varchar(8) not null,
    order_qty         numeric(20, 4) not null,
    price             numeric(20, 8),
    stop_price        numeric(20, 8),
    ord_type          varchar(8) not null,
    time_in_force     varchar(8) not null,
    handl_inst        varchar(4),
    exec_inst         varchar(8),
    order_status      varchar(8) not null,
    arrival_price     numeric(20, 8),
    transact_time     timestamp not null,
    sender_comp_id    varchar(32),
    target_comp_id    varchar(32),
    text_memo         varchar(255)
);

create table if not exists capital_markets_3nf.execution_report (
    exec_id              varchar primary key,
    order_id             varchar not null references capital_markets_3nf.order(order_id),
    exec_type            varchar(8) not null,
    ord_status           varchar(8) not null,
    leaves_qty           numeric(20, 4),
    cum_qty              numeric(20, 4),
    avg_px               numeric(20, 8),
    last_qty             numeric(20, 4),
    last_px              numeric(20, 8),
    trade_date           date,
    transact_time        timestamp not null,
    venue_id             varchar references capital_markets_3nf.execution_venue(venue_id),
    liquidity_indicator  varchar(8),
    trade_capacity       varchar(8)
);

-- ---------------------------------------------------------------------------
-- Trade booking (FpML)
-- ---------------------------------------------------------------------------
create table if not exists capital_markets_3nf.trade (
    trade_id                  varchar primary key,
    trade_id_scheme           varchar(64),
    usi                       varchar(64),
    account_id                varchar not null references capital_markets_3nf.account(account_id),
    instrument_id             varchar not null references capital_markets_3nf.instrument(instrument_id),
    counterparty_id           varchar not null references capital_markets_3nf.counterparty(counterparty_id),
    side                      varchar(8) not null,
    trade_qty                 numeric(20, 4) not null,
    trade_price               numeric(20, 8) not null,
    notional                  numeric(20, 4),
    notional_currency         varchar(3),
    trade_date                date not null,
    execution_ts              timestamp not null,
    settlement_date           date,
    settlement_currency       varchar(3),
    clearing_status           varchar(16) not null,
    ccp_id                    varchar,
    product_type_fpml         varchar(64),
    master_agreement_id       varchar,
    regulatory_jurisdiction   varchar(8)
);

create table if not exists capital_markets_3nf.allocation (
    allocation_id              varchar primary key,
    trade_id                   varchar not null references capital_markets_3nf.trade(trade_id),
    account_id                 varchar not null references capital_markets_3nf.account(account_id),
    alloc_qty                  numeric(20, 4) not null,
    alloc_avg_price            numeric(20, 8),
    alloc_status               varchar(8) not null,
    settlement_instructions_id varchar,
    created_at                 timestamp not null
);

create table if not exists capital_markets_3nf.confirmation (
    confirmation_id      varchar primary key,
    trade_id             varchar not null references capital_markets_3nf.trade(trade_id),
    counterparty_id      varchar not null references capital_markets_3nf.counterparty(counterparty_id),
    confirmation_status  varchar(8) not null,
    confirmation_method  varchar(16),
    confirmed_at         timestamp not null
);

-- ---------------------------------------------------------------------------
-- Settlement (ISO 20022)
-- ---------------------------------------------------------------------------
create table if not exists capital_markets_3nf.settlement_instruction (
    ssi_id              varchar primary key,
    trade_id            varchar not null references capital_markets_3nf.trade(trade_id),
    account_owner       varchar,
    safekeeping_account varchar(35) not null,
    csd_bic             varchar(11),
    instrument_id       varchar not null references capital_markets_3nf.instrument(instrument_id),
    settlement_amount   numeric(20, 4) not null,
    settlement_currency varchar(3) not null,
    settlement_quantity numeric(20, 4) not null,
    trade_date          date not null,
    settlement_date     date not null,
    delivery_type       varchar(8) not null,
    payment_type        varchar(8),
    priority            varchar(8),
    status              varchar(16) not null,
    matched_ts          timestamp,
    settled_ts          timestamp
);

-- ---------------------------------------------------------------------------
-- Position / lifecycle / margin / regulatory / market data
-- ---------------------------------------------------------------------------
create table if not exists capital_markets_3nf.position (
    position_id      varchar primary key,
    account_id       varchar not null references capital_markets_3nf.account(account_id),
    instrument_id    varchar not null references capital_markets_3nf.instrument(instrument_id),
    position_date    date not null,
    long_qty         numeric(20, 4) not null default 0,
    short_qty        numeric(20, 4) not null default 0,
    net_qty          numeric(20, 4) not null default 0,
    avg_cost         numeric(20, 8),
    market_price     numeric(20, 8),
    market_value     numeric(20, 4),
    unrealized_pnl   numeric(20, 4),
    realized_pnl     numeric(20, 4),
    currency         varchar(3) not null
);

create table if not exists capital_markets_3nf.lifecycle_event (
    event_id           varchar primary key,
    trade_id           varchar not null references capital_markets_3nf.trade(trade_id),
    event_type         varchar(32) not null,
    effective_date     date not null,
    payment_date       date,
    payment_amount     numeric(20, 4),
    payment_currency   varchar(3),
    reset_rate         numeric(12, 9),
    index_name         varchar(32),
    processed_ts       timestamp not null,
    source_message_id  varchar
);

create table if not exists capital_markets_3nf.margin_call (
    margin_call_id          varchar primary key,
    counterparty_id         varchar not null references capital_markets_3nf.counterparty(counterparty_id),
    ccp_id                  varchar,
    call_type               varchar(16) not null,
    call_amount             numeric(20, 4) not null,
    call_currency           varchar(3) not null,
    call_ts                 timestamp not null,
    due_ts                  timestamp not null,
    status                  varchar(16) not null,
    collateral_pledged_value numeric(20, 4)
);

create table if not exists capital_markets_3nf.trade_break (
    break_id            varchar primary key,
    trade_id            varchar not null references capital_markets_3nf.trade(trade_id),
    break_type          varchar(16) not null,
    detected_at         timestamp not null,
    assignee_id         varchar,
    status              varchar(16) not null,
    resolved_at         timestamp,
    resolution_notes    text
);

create table if not exists capital_markets_3nf.regulatory_report (
    report_id          varchar primary key,
    trade_id           varchar not null references capital_markets_3nf.trade(trade_id),
    regime             varchar(8) not null,
    report_type        varchar(16) not null,
    utis_uti           varchar(64),
    trade_repository   varchar(32),
    submission_ts      timestamp not null,
    ack_status         varchar(8),
    ack_ts             timestamp,
    error_code         varchar(16)
);

create table if not exists capital_markets_3nf.market_data_tick (
    tick_id           bigint primary key,
    instrument_id     varchar not null references capital_markets_3nf.instrument(instrument_id),
    venue_id          varchar references capital_markets_3nf.execution_venue(venue_id),
    tick_ts           timestamp not null,
    bid_px            numeric(20, 8),
    bid_sz            numeric(20, 4),
    ask_px            numeric(20, 8),
    ask_sz            numeric(20, 4),
    last_px           numeric(20, 8),
    last_sz           numeric(20, 4),
    condition_codes   varchar(16)
);
