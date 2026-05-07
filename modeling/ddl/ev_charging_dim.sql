-- =============================================================================
-- EV Charging — dimensional mart
-- Star schema. Facts: session, cdr, status_15m (uptime), dr_response.
-- =============================================================================

create schema if not exists ev_charging_dim;

create table if not exists ev_charging_dim.dim_date (
    date_key      integer primary key,
    date_actual   date not null,
    day_of_week   smallint not null,
    iso_week      smallint not null,
    fiscal_period varchar(8)
);

create table if not exists ev_charging_dim.dim_time (
    time_key       integer primary key,
    hour_of_day    smallint not null,
    minute_of_hour smallint not null
);

create table if not exists ev_charging_dim.dim_location (
    location_key bigint primary key,
    location_id  varchar not null,
    name         varchar(255),
    city         varchar(64),
    country_iso  varchar(3),
    parking_type varchar(32),
    valid_from   timestamp not null,
    valid_to     timestamp,
    is_current   boolean not null
);

create table if not exists ev_charging_dim.dim_station (
    station_key      bigint primary key,
    station_id       varchar not null,
    vendor_name      varchar(64),
    model            varchar(64),
    ocpp_version     varchar(8),
    valid_from       timestamp not null,
    valid_to         timestamp,
    is_current       boolean not null
);

create table if not exists ev_charging_dim.dim_evse (
    evse_key      bigint primary key,
    evse_id       varchar not null,
    station_id    varchar,
    valid_from    timestamp not null,
    valid_to      timestamp,
    is_current    boolean not null
);

create table if not exists ev_charging_dim.dim_connector (
    connector_key  bigint primary key,
    connector_id   varchar not null,
    standard       varchar(16),
    power_type     varchar(16),
    max_power_w    integer,
    valid_from     timestamp not null,
    valid_to       timestamp,
    is_current     boolean not null
);

create table if not exists ev_charging_dim.dim_token (
    token_key   bigint primary key,
    token_uid   varchar(36) not null,
    type        varchar(16),
    issuer      varchar(64),
    valid_from  timestamp not null,
    valid_to    timestamp,
    is_current  boolean not null
);

create table if not exists ev_charging_dim.dim_tariff (
    tariff_key  bigint primary key,
    tariff_id   varchar(36) not null,
    tariff_type varchar(16),
    currency    varchar(3),
    valid_from  timestamp not null,
    valid_to    timestamp,
    is_current  boolean not null
);

-- ---------------------------------------------------------------------------
-- Facts
-- ---------------------------------------------------------------------------

-- Grain: one row per charging session.
create table if not exists ev_charging_dim.fact_session (
    session_id          varchar(36) primary key,
    location_key        bigint references ev_charging_dim.dim_location(location_key),
    station_key         bigint references ev_charging_dim.dim_station(station_key),
    evse_key            bigint references ev_charging_dim.dim_evse(evse_key),
    connector_key       bigint references ev_charging_dim.dim_connector(connector_key),
    token_key           bigint references ev_charging_dim.dim_token(token_key),
    tariff_key          bigint references ev_charging_dim.dim_tariff(tariff_key),
    start_date_key      integer not null references ev_charging_dim.dim_date(date_key),
    start_time_key      integer references ev_charging_dim.dim_time(time_key),
    end_date_key        integer references ev_charging_dim.dim_date(date_key),
    duration_minutes    integer,
    kwh                 numeric(12, 3) not null default 0,
    revenue_excl_vat    numeric(10, 4),
    revenue_incl_vat    numeric(10, 4),
    is_completed        boolean not null,
    is_roaming          boolean not null default false,
    auth_method         varchar(16)
);

-- Grain: one row per CDR (settled charge detail record).
create table if not exists ev_charging_dim.fact_cdr (
    cdr_id              varchar(36) primary key,
    session_id          varchar(36),
    location_key        bigint references ev_charging_dim.dim_location(location_key),
    token_key           bigint references ev_charging_dim.dim_token(token_key),
    start_date_key      integer not null references ev_charging_dim.dim_date(date_key),
    end_date_key        integer not null references ev_charging_dim.dim_date(date_key),
    total_energy_kwh    numeric(12, 3) not null,
    total_cost_incl_vat numeric(10, 4) not null,
    currency            varchar(3) not null,
    is_roaming          boolean not null default false
);

-- Grain: EVSE x 15-minute slot status.
create table if not exists ev_charging_dim.fact_evse_status_15m (
    evse_key       bigint not null references ev_charging_dim.dim_evse(evse_key),
    date_key       integer not null references ev_charging_dim.dim_date(date_key),
    time_key       integer not null references ev_charging_dim.dim_time(time_key),
    available_min  smallint not null,
    occupied_min   smallint not null,
    faulted_min    smallint not null,
    unavailable_min smallint not null,
    primary key (evse_key, date_key, time_key)
);

-- Grain: DR event x station.
create table if not exists ev_charging_dim.fact_dr_response (
    dr_event_id      varchar not null,
    station_key      bigint not null references ev_charging_dim.dim_station(station_key),
    event_start_key  integer not null references ev_charging_dim.dim_date(date_key),
    duration_minutes integer not null,
    requested_kw     numeric(10, 3),
    delivered_kw     numeric(10, 3),
    compliance_pct   numeric(6, 3),
    is_opted_in      boolean not null,
    primary key (dr_event_id, station_key)
);
