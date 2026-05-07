-- =============================================================================
-- Settlement & Clearing — 3NF schema
-- Source standards:
--   ISO 20022 Securities Settlement (sese.*, semt.*, setr.*, colr.*)
--     https://www.iso20022.org/iso-20022-message-definitions
--   ISO 17442 Legal Entity Identifier (LEI), ISO 9362 BIC,
--     ISO 10962 CFI, ISO 6166 ISIN.
--   DTCC NSCC Continuous Net Settlement (CNS) record specs
--     https://www.dtcc.com/clearing-services
--   T2S, CSDR Settlement Discipline Regime, BCBS 248 Intraday Liquidity.
-- Table and column names mirror the ISO 20022 message components verbatim
-- where the standard names them; otherwise use the closest canonical term.
-- =============================================================================

create schema if not exists settlement_clearing_3nf;

-- ISO 20022 PartyIdentification — issuer, owner, counterparty, agent.
create table if not exists settlement_clearing_3nf.party (
    party_id        varchar primary key,
    lei             varchar(20),                -- ISO 17442
    bic             varchar(11),                -- ISO 9362 BIC11
    legal_name      varchar(255),
    party_role      varchar(16),                -- AccountOwner|AccountServicer|CSD|CCP|CashAgent|SettlementAgent
    country_iso     varchar(2),                 -- ISO 3166-1 alpha-2
    status          varchar(16)
);

-- Central Securities Depository (DTCC, Euroclear, Clearstream, JASDEC, T2S).
create table if not exists settlement_clearing_3nf.csd (
    csd_id           varchar primary key,
    bic              varchar(11),
    name             varchar(64),
    country_iso      varchar(2),
    timezone         varchar(32),
    cutoff_local_time varchar(8),
    t2s_eligible     boolean,                   -- TARGET2-Securities
    status           varchar(16)
);

-- Central Counterparty (NSCC, LCH, ICE Clear, Eurex Clearing, CME ClearPort).
create table if not exists settlement_clearing_3nf.ccp (
    ccp_id                  varchar primary key,
    bic                     varchar(11),
    lei                     varchar(20),
    name                    varchar(64),
    country_iso             varchar(2),
    clearing_segments       text,
    default_fund_currency   varchar(3),
    status                  varchar(16)
);

-- ISO 20022 SecurityIdentification — instrument master with ISO 6166 / 10962.
create table if not exists settlement_clearing_3nf.instrument (
    instrument_id      varchar primary key,
    isin               varchar(12),             -- ISO 6166
    cusip              varchar(9),
    figi               varchar(12),
    cfi_code           varchar(6),              -- ISO 10962
    short_name         varchar(64),
    issuer_party_id    varchar references settlement_clearing_3nf.party(party_id),
    currency           varchar(3),              -- ISO 4217
    country_of_issue   varchar(2),
    maturity_date      date,
    status             varchar(16)
);

-- ISO 20022 SafekeepingAccount (acmt.* / sese.023 SafekeepingAccount block).
create table if not exists settlement_clearing_3nf.safekeeping_account (
    safekeeping_account_id      varchar(35) primary key,
    account_owner_party_id      varchar references settlement_clearing_3nf.party(party_id),
    account_servicer_party_id   varchar references settlement_clearing_3nf.party(party_id),
    csd_id                      varchar references settlement_clearing_3nf.csd(csd_id),
    account_type                varchar(16),    -- Own|Client|Omnibus|Segregated
    opened_at                   date,
    status                      varchar(16)
);

-- ISO 20022 CashAccount — settlement cash leg (RTGS / correspondent / client).
create table if not exists settlement_clearing_3nf.cash_account (
    cash_account_id             varchar(35) primary key,
    account_owner_party_id      varchar references settlement_clearing_3nf.party(party_id),
    bic                         varchar(11),
    account_servicer_party_id   varchar,
    currency                    varchar(3),
    account_type                varchar(16),    -- RTGS|Correspondent|Client
    opened_at                   date,
    status                      varchar(16)
);

-- Trade pending settlement (slim view; full booking in capital_markets domain).
create table if not exists settlement_clearing_3nf.trade (
    trade_id                varchar primary key,
    instrument_id           varchar references settlement_clearing_3nf.instrument(instrument_id),
    account_owner_party_id  varchar references settlement_clearing_3nf.party(party_id),
    counterparty_party_id   varchar references settlement_clearing_3nf.party(party_id),
    side                    varchar(8),         -- BUYI|SELL
    quantity                decimal(20,4),
    trade_price             decimal(20,8),
    trade_date              date,
    settlement_date         date,
    clearing_status         varchar(16),
    ccp_id                  varchar references settlement_clearing_3nf.ccp(ccp_id),
    csd_id                  varchar references settlement_clearing_3nf.csd(csd_id)
);

-- ISO 20022 sese.023 SecuritiesSettlementTransactionInstruction.
create table if not exists settlement_clearing_3nf.settlement_instruction (
    ssi_id                          varchar primary key,        -- TransactionIdentification
    trade_id                        varchar references settlement_clearing_3nf.trade(trade_id),
    account_owner_party_id          varchar references settlement_clearing_3nf.party(party_id),
    safekeeping_account_id          varchar(35) references settlement_clearing_3nf.safekeeping_account(safekeeping_account_id),
    cash_account_id                 varchar(35) references settlement_clearing_3nf.cash_account(cash_account_id),
    instrument_id                   varchar references settlement_clearing_3nf.instrument(instrument_id),
    settlement_quantity             decimal(20,4),
    settlement_amount               decimal(20,4),
    settlement_currency             varchar(3),
    trade_date                      date,
    settlement_date                 date,
    delivery_type                   varchar(8),                 -- DELI|RECE
    payment_type                    varchar(8),                 -- APMT|FREE
    settlement_method               varchar(8),                 -- DVP|RVP|FOP|DWPP
    priority                        varchar(8),
    partial_settlement_indicator    varchar(8),                 -- NPAR|PART
    hold_indicator                  boolean,
    linkage_id                      varchar(64),
    status                          varchar(16),                -- Pending|Matched|Unmatched|Settled|Failed|Cancelled
    created_at                      timestamp
);

-- ISO 20022 sese.024 SecuritiesSettlementTransactionStatusAdvice — matching log.
create table if not exists settlement_clearing_3nf.matching_status (
    matching_status_id      varchar primary key,
    ssi_id                  varchar references settlement_clearing_3nf.settlement_instruction(ssi_id),
    status_code             varchar(8),         -- MACH|NMAT|UMAC
    reason_code             varchar(8),         -- DEPT|PRIC|QUTY|VAR|SETR|...
    reason_description      varchar(255),
    status_ts               timestamp,
    counterparty_match_ts   timestamp
);

-- ISO 20022 sese.025 SecuritiesSettlementTransactionConfirmation.
create table if not exists settlement_clearing_3nf.settlement_confirmation (
    confirmation_id            varchar primary key,
    ssi_id                     varchar references settlement_clearing_3nf.settlement_instruction(ssi_id),
    settled_quantity           decimal(20,4),
    settled_amount             decimal(20,4),
    settled_currency           varchar(3),
    settlement_ts              timestamp,
    corporate_action_event_id  varchar,
    status_code                varchar(8)       -- SETT|PSET (partially settled)
);

-- Failed settlement event (CSDR Settlement Discipline Regime applies in EU).
create table if not exists settlement_clearing_3nf.failed_settlement (
    fail_id                 varchar primary key,
    ssi_id                  varchar references settlement_clearing_3nf.settlement_instruction(ssi_id),
    failed_quantity         decimal(20,4),
    failed_amount           decimal(20,4),
    fail_reason_code        varchar(8),         -- LACK|CASH|NCRR|CSDH|LATE|OTHR
    fail_ts                 timestamp,
    age_days                smallint,
    csd_penalty_applied     decimal(15,4),      -- CSDR daily penalty
    csdr_penalty_currency   varchar(3),
    status                  varchar(16)
);

-- CSDR Buy-In execution under EU Settlement Discipline regime.
create table if not exists settlement_clearing_3nf.buyin (
    buyin_id                 varchar primary key,
    fail_id                  varchar references settlement_clearing_3nf.failed_settlement(fail_id),
    instrument_id            varchar references settlement_clearing_3nf.instrument(instrument_id),
    bought_in_quantity       decimal(20,4),
    buyin_price              decimal(20,8),
    buyin_currency           varchar(3),
    extension_period_days    smallint,
    triggered_by             varchar(16),
    executed_at              timestamp,
    status                   varchar(16)
);

-- DTCC NSCC Continuous Net Settlement — daily netted obligation per
-- participant per CUSIP. Fields drawn from CNS record specs.
create table if not exists settlement_clearing_3nf.cns_obligation (
    cns_obligation_id      varchar primary key,
    participant_party_id   varchar references settlement_clearing_3nf.party(party_id),
    cusip                  varchar(9),
    business_date          date,
    long_position_qty      decimal(20,4),
    short_position_qty     decimal(20,4),
    net_position_qty       decimal(20,4),
    net_money              decimal(20,4),
    net_money_currency     varchar(3),
    aged_failures_qty      decimal(20,4),
    status                 varchar(16)
);

-- ISO 20022 colr.022 MarginCallRequest — Initial / Variation / Default Fund.
create table if not exists settlement_clearing_3nf.ccp_margin_call (
    margin_call_id              varchar primary key,
    ccp_id                      varchar references settlement_clearing_3nf.ccp(ccp_id),
    clearing_member_party_id    varchar references settlement_clearing_3nf.party(party_id),
    call_type                   varchar(16),    -- Initial|Variation|DefaultFund|Concentration
    call_amount                 decimal(20,4),
    call_currency               varchar(3),
    call_ts                     timestamp,
    due_ts                      timestamp,
    status                      varchar(16),    -- Issued|Acknowledged|Met|Disputed
    collateral_amount_pledged   decimal(20,4),
    variation_pnl               decimal(20,4)
);

-- ISO 20022 colr.005 / colr.006 — pledge or return of collateral against margin.
create table if not exists settlement_clearing_3nf.collateral_movement (
    collateral_movement_id   varchar primary key,
    margin_call_id           varchar references settlement_clearing_3nf.ccp_margin_call(margin_call_id),
    collateral_type          varchar(16),       -- Cash|Securities
    instrument_id            varchar references settlement_clearing_3nf.instrument(instrument_id),
    quantity                 decimal(20,4),
    market_value             decimal(20,4),
    haircut_pct              decimal(6,4),
    post_haircut_value       decimal(20,4),
    currency                 varchar(3),
    direction                varchar(8),        -- Pledge|Return
    movement_ts              timestamp,
    csd_id                   varchar references settlement_clearing_3nf.csd(csd_id)
);

-- ISO 20022 camt.054 BankToCustomerDebitCreditNotification — settlement cash leg.
create table if not exists settlement_clearing_3nf.cash_movement (
    cash_movement_id          varchar primary key,
    cash_account_id           varchar(35) references settlement_clearing_3nf.cash_account(cash_account_id),
    ssi_id                    varchar references settlement_clearing_3nf.settlement_instruction(ssi_id),
    credit_debit_indicator    varchar(4),       -- DBIT|CRDT
    amount                    decimal(20,4),
    currency                  varchar(3),
    value_date                date,
    booking_date              date,
    end_to_end_id             varchar(35),
    status                    varchar(16)
);

-- ISO 20022 semt.017 ReportingTransactionStatement (statement of holdings).
create table if not exists settlement_clearing_3nf.holding_statement (
    statement_id            varchar primary key,
    safekeeping_account_id  varchar(35) references settlement_clearing_3nf.safekeeping_account(safekeeping_account_id),
    instrument_id           varchar references settlement_clearing_3nf.instrument(instrument_id),
    as_of_date              date,
    opening_balance         decimal(20,4),
    closing_balance         decimal(20,4),
    pending_in              decimal(20,4),
    pending_out             decimal(20,4),
    settlement_status       varchar(16)
);

-- Reconciliation break between internal book and CSD/CCP statement.
create table if not exists settlement_clearing_3nf.reconciliation_break (
    break_id          varchar primary key,
    account_id        varchar,
    instrument_id     varchar references settlement_clearing_3nf.instrument(instrument_id),
    break_type        varchar(16),              -- Quantity|Price|Currency|SettleDate|Counterparty
    break_amount      decimal(20,4),
    detected_at       timestamp,
    source_system     varchar(32),
    assignee_id       varchar,
    status            varchar(16),              -- Open|InProgress|Resolved|Aged
    resolved_at       timestamp,
    resolution_notes  text
);
