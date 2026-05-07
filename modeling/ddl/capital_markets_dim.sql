-- =============================================================================
-- Capital Markets — dimensional mart
-- Star schema. Facts: order, execution, trade, settlement, position daily.
-- Dimensions: instrument, counterparty, account, venue, date, time.
-- =============================================================================

create schema if not exists capital_markets_dim;

create table if not exists capital_markets_dim.dim_date (
    date_key      integer primary key,
    date_actual   date not null,
    day_of_week   smallint not null,
    iso_week      smallint not null,
    fiscal_period varchar(8)
);

create table if not exists capital_markets_dim.dim_time (
    time_key       integer primary key,
    hour_of_day    smallint not null,
    minute_of_hour smallint not null,
    second_of_minute smallint not null
);

create table if not exists capital_markets_dim.dim_instrument (
    instrument_key  bigint primary key,
    instrument_id   varchar not null,
    isin            varchar(12),
    symbol          varchar(16),
    security_type   varchar(16),
    cfi_code        varchar(6),
    currency        varchar(3),
    asset_class     varchar(16),
    valid_from      timestamp not null,
    valid_to        timestamp,
    is_current      boolean not null
);

create table if not exists capital_markets_dim.dim_counterparty (
    counterparty_key bigint primary key,
    counterparty_id  varchar not null,
    lei              varchar(20),
    legal_name       varchar(255),
    party_type       varchar(16),
    jurisdiction_iso varchar(2),
    credit_rating    varchar(8),
    valid_from       timestamp not null,
    valid_to         timestamp,
    is_current       boolean not null
);

create table if not exists capital_markets_dim.dim_account (
    account_key   bigint primary key,
    account_id    varchar not null,
    counterparty_id varchar,
    account_type  varchar(16),
    base_currency varchar(3),
    valid_from    timestamp not null,
    valid_to      timestamp,
    is_current    boolean not null
);

create table if not exists capital_markets_dim.dim_venue (
    venue_key   smallint primary key,
    venue_id    varchar not null,
    mic         varchar(4),
    name        varchar(64),
    venue_type  varchar(16),
    country_iso varchar(2)
);

create table if not exists capital_markets_dim.dim_side (
    side_key   smallint primary key,
    side_code  varchar(8) not null,
    side_label varchar(16) not null
);

-- ---------------------------------------------------------------------------
-- Facts
-- ---------------------------------------------------------------------------

-- Grain: one row per FIX execution (fill).
create table if not exists capital_markets_dim.fact_execution (
    exec_id              varchar primary key,
    order_id             varchar not null,
    instrument_key       bigint not null references capital_markets_dim.dim_instrument(instrument_key),
    account_key          bigint not null references capital_markets_dim.dim_account(account_key),
    venue_key            smallint references capital_markets_dim.dim_venue(venue_key),
    side_key             smallint not null references capital_markets_dim.dim_side(side_key),
    trade_date_key       integer not null references capital_markets_dim.dim_date(date_key),
    transact_time_key    integer references capital_markets_dim.dim_time(time_key),
    last_qty             numeric(20, 4) not null,
    last_px              numeric(20, 8) not null,
    notional             numeric(20, 4),
    arrival_price        numeric(20, 8),
    slippage_bps         numeric(10, 4),
    liquidity_indicator  varchar(8)
);

-- Grain: one row per booked trade.
create table if not exists capital_markets_dim.fact_trade (
    trade_id              varchar primary key,
    instrument_key        bigint not null references capital_markets_dim.dim_instrument(instrument_key),
    account_key           bigint not null references capital_markets_dim.dim_account(account_key),
    counterparty_key      bigint not null references capital_markets_dim.dim_counterparty(counterparty_key),
    side_key              smallint not null references capital_markets_dim.dim_side(side_key),
    trade_date_key        integer not null references capital_markets_dim.dim_date(date_key),
    settlement_date_key   integer references capital_markets_dim.dim_date(date_key),
    trade_qty             numeric(20, 4) not null,
    trade_price           numeric(20, 8) not null,
    notional              numeric(20, 4),
    notional_currency     varchar(3),
    is_cleared            boolean not null,
    regulatory_jurisdiction varchar(8)
);

-- Grain: one row per settlement instruction status checkpoint.
create table if not exists capital_markets_dim.fact_settlement (
    ssi_id              varchar primary key,
    trade_id            varchar not null,
    instrument_key      bigint not null references capital_markets_dim.dim_instrument(instrument_key),
    account_key         bigint not null references capital_markets_dim.dim_account(account_key),
    settlement_date_key integer not null references capital_markets_dim.dim_date(date_key),
    settled_date_key    integer references capital_markets_dim.dim_date(date_key),
    settlement_amount   numeric(20, 4) not null,
    settlement_currency varchar(3) not null,
    delivery_type       varchar(8),
    is_settled_on_time  boolean,
    fail_days           integer
);

-- Grain: account x instrument x position_date (daily).
create table if not exists capital_markets_dim.fact_position_daily (
    position_date_key integer not null references capital_markets_dim.dim_date(date_key),
    account_key       bigint not null references capital_markets_dim.dim_account(account_key),
    instrument_key    bigint not null references capital_markets_dim.dim_instrument(instrument_key),
    long_qty          numeric(20, 4) not null,
    short_qty         numeric(20, 4) not null,
    net_qty           numeric(20, 4) not null,
    market_value      numeric(20, 4),
    unrealized_pnl    numeric(20, 4),
    realized_pnl      numeric(20, 4),
    var_1d_99         numeric(20, 4),
    primary key (position_date_key, account_key, instrument_key)
);

-- Grain: one row per trade break event.
create table if not exists capital_markets_dim.fact_trade_break (
    break_id            varchar primary key,
    trade_id            varchar not null,
    counterparty_key    bigint references capital_markets_dim.dim_counterparty(counterparty_key),
    detected_date_key   integer not null references capital_markets_dim.dim_date(date_key),
    resolved_date_key   integer references capital_markets_dim.dim_date(date_key),
    break_type          varchar(16) not null,
    age_days            integer,
    is_resolved         boolean not null
);
