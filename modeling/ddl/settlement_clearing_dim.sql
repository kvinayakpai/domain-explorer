-- =============================================================================
-- Settlement & Clearing — dimensional mart
-- Star schema. Facts: settlement_instruction, fail, margin_call, cns_obligation,
--   collateral_movement, recon_break_daily.
-- Conformed dims (SCD2): party, instrument, csd, ccp, account, date.
-- =============================================================================

create schema if not exists settlement_clearing_dim;

-- ---------------------------------------------------------------------------
-- Conformed dimensions (SCD2)
-- ---------------------------------------------------------------------------
create table if not exists settlement_clearing_dim.dim_date (
    date_key      integer primary key,
    date_actual   date not null,
    day_of_week   smallint not null,
    iso_week      smallint not null,
    fiscal_period varchar(8)
);

create table if not exists settlement_clearing_dim.dim_party (
    party_key      bigint primary key,
    party_id       varchar not null,
    lei            varchar(20),
    bic            varchar(11),
    legal_name     varchar(255),
    party_role     varchar(16),
    country_iso    varchar(2),
    valid_from     timestamp not null,
    valid_to       timestamp,
    is_current     boolean not null
);

create table if not exists settlement_clearing_dim.dim_instrument (
    instrument_key   bigint primary key,
    instrument_id    varchar not null,
    isin             varchar(12),
    cusip            varchar(9),
    figi             varchar(12),
    cfi_code         varchar(6),
    currency         varchar(3),
    country_of_issue varchar(2),
    valid_from       timestamp not null,
    valid_to         timestamp,
    is_current       boolean not null
);

create table if not exists settlement_clearing_dim.dim_csd (
    csd_key       bigint primary key,
    csd_id        varchar not null,
    bic           varchar(11),
    name          varchar(64),
    country_iso   varchar(2),
    t2s_eligible  boolean,
    valid_from    timestamp not null,
    valid_to      timestamp,
    is_current    boolean not null
);

create table if not exists settlement_clearing_dim.dim_ccp (
    ccp_key                 bigint primary key,
    ccp_id                  varchar not null,
    bic                     varchar(11),
    lei                     varchar(20),
    name                    varchar(64),
    country_iso             varchar(2),
    default_fund_currency   varchar(3),
    valid_from              timestamp not null,
    valid_to                timestamp,
    is_current              boolean not null
);

create table if not exists settlement_clearing_dim.dim_account (
    account_key                 bigint primary key,
    account_id                  varchar not null,
    account_kind                varchar(16),    -- Safekeeping|Cash
    account_type                varchar(16),    -- Own|Client|Omnibus|Segregated|RTGS|...
    owner_party_id              varchar,
    csd_id                      varchar,
    valid_from                  timestamp not null,
    valid_to                    timestamp,
    is_current                  boolean not null
);

-- ---------------------------------------------------------------------------
-- Facts
-- ---------------------------------------------------------------------------

-- Grain: one row per settlement instruction (sese.023 lifecycle terminal state).
create table if not exists settlement_clearing_dim.fact_settlement (
    ssi_id                          varchar primary key,
    party_key                       bigint references settlement_clearing_dim.dim_party(party_key),
    counterparty_key                bigint references settlement_clearing_dim.dim_party(party_key),
    instrument_key                  bigint references settlement_clearing_dim.dim_instrument(instrument_key),
    csd_key                         bigint references settlement_clearing_dim.dim_csd(csd_key),
    safekeeping_account_key         bigint references settlement_clearing_dim.dim_account(account_key),
    cash_account_key                bigint references settlement_clearing_dim.dim_account(account_key),
    trade_date_key                  integer references settlement_clearing_dim.dim_date(date_key),
    intended_settlement_date_key    integer references settlement_clearing_dim.dim_date(date_key),
    actual_settlement_date_key      integer references settlement_clearing_dim.dim_date(date_key),
    settlement_method               varchar(8),     -- DVP|RVP|FOP
    delivery_type                   varchar(8),     -- DELI|RECE
    settlement_quantity             decimal(20,4),
    settlement_amount               decimal(20,4),
    settlement_currency             varchar(3),
    matched_t1                      boolean,
    settled_same_day                boolean,
    final_status                    varchar(16),
    days_to_settle                  smallint,
    is_partial                      boolean
);

-- Grain: one row per failure event — feeds CSDR penalty and buy-in counts.
create table if not exists settlement_clearing_dim.fact_settlement_fail (
    fail_id                 varchar primary key,
    ssi_id                  varchar references settlement_clearing_dim.fact_settlement(ssi_id),
    party_key               bigint references settlement_clearing_dim.dim_party(party_key),
    instrument_key          bigint references settlement_clearing_dim.dim_instrument(instrument_key),
    csd_key                 bigint references settlement_clearing_dim.dim_csd(csd_key),
    fail_date_key           integer references settlement_clearing_dim.dim_date(date_key),
    fail_reason_code        varchar(8),
    failed_quantity         decimal(20,4),
    failed_amount           decimal(20,4),
    age_days                smallint,
    csd_penalty_applied     decimal(15,4),
    csdr_penalty_currency   varchar(3),
    triggered_buyin         boolean
);

-- Grain: one row per CCP margin call.
create table if not exists settlement_clearing_dim.fact_margin_call (
    margin_call_id              varchar primary key,
    ccp_key                     bigint references settlement_clearing_dim.dim_ccp(ccp_key),
    clearing_member_key         bigint references settlement_clearing_dim.dim_party(party_key),
    call_date_key               integer references settlement_clearing_dim.dim_date(date_key),
    call_type                   varchar(16),
    call_amount                 decimal(20,4),
    call_currency               varchar(3),
    collateral_amount_pledged   decimal(20,4),
    variation_pnl               decimal(20,4),
    minutes_to_meet             integer,
    final_status                varchar(16),
    disputed_flag               boolean
);

-- Grain: one row per participant x CUSIP x business_date (CNS daily netting batch).
create table if not exists settlement_clearing_dim.fact_cns_obligation_daily (
    business_date_key       integer not null references settlement_clearing_dim.dim_date(date_key),
    party_key               bigint not null references settlement_clearing_dim.dim_party(party_key),
    instrument_key          bigint not null references settlement_clearing_dim.dim_instrument(instrument_key),
    long_position_qty       decimal(20,4),
    short_position_qty      decimal(20,4),
    net_position_qty        decimal(20,4),
    gross_obligation_qty    decimal(20,4),
    net_money               decimal(20,4),
    net_money_currency      varchar(3),
    aged_failures_qty       decimal(20,4),
    primary key (business_date_key, party_key, instrument_key)
);

-- Grain: one row per collateral movement (pledge / return).
create table if not exists settlement_clearing_dim.fact_collateral_movement (
    collateral_movement_id  varchar primary key,
    margin_call_id          varchar references settlement_clearing_dim.fact_margin_call(margin_call_id),
    movement_date_key       integer references settlement_clearing_dim.dim_date(date_key),
    instrument_key          bigint references settlement_clearing_dim.dim_instrument(instrument_key),
    csd_key                 bigint references settlement_clearing_dim.dim_csd(csd_key),
    collateral_type         varchar(16),    -- Cash|Securities
    direction               varchar(8),     -- Pledge|Return
    quantity                decimal(20,4),
    market_value            decimal(20,4),
    haircut_pct             decimal(6,4),
    post_haircut_value      decimal(20,4),
    currency                varchar(3)
);

-- Grain: one row per (account x business_date) — open break aging snapshot.
create table if not exists settlement_clearing_dim.fact_recon_break_daily (
    business_date_key   integer not null references settlement_clearing_dim.dim_date(date_key),
    account_key         bigint not null references settlement_clearing_dim.dim_account(account_key),
    open_break_count    integer not null,
    aged_break_count    integer not null,                  -- > 5 days
    new_break_count     integer not null,
    resolved_count      integer not null,
    avg_age_days        decimal(10,2),
    sum_break_amount    decimal(20,4),
    primary key (business_date_key, account_key)
);
