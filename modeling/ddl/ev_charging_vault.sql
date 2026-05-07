-- =============================================================================
-- EV Charging — Data Vault 2.0
-- Hubs: location, station, evse, connector, token, tariff, session, cdr.
-- Bitemporal sat for session state and EVSE status (fault timeline).
-- =============================================================================

create schema if not exists ev_charging_vault;

create table if not exists ev_charging_vault.hub_location (
    location_hk bytea primary key,
    location_bk varchar not null,
    load_dts    timestamp not null,
    rec_src     varchar not null
);

create table if not exists ev_charging_vault.hub_station (
    station_hk bytea primary key,
    station_bk varchar not null,
    load_dts   timestamp not null,
    rec_src    varchar not null
);

create table if not exists ev_charging_vault.hub_evse (
    evse_hk    bytea primary key,
    evse_bk    varchar not null,
    load_dts   timestamp not null,
    rec_src    varchar not null
);

create table if not exists ev_charging_vault.hub_connector (
    connector_hk bytea primary key,
    connector_bk varchar not null,
    load_dts     timestamp not null,
    rec_src      varchar not null
);

create table if not exists ev_charging_vault.hub_token (
    token_hk   bytea primary key,
    token_bk   varchar not null,
    load_dts   timestamp not null,
    rec_src    varchar not null
);

create table if not exists ev_charging_vault.hub_tariff (
    tariff_hk  bytea primary key,
    tariff_bk  varchar not null,
    load_dts   timestamp not null,
    rec_src    varchar not null
);

create table if not exists ev_charging_vault.hub_session (
    session_hk bytea primary key,
    session_bk varchar not null,
    load_dts   timestamp not null,
    rec_src    varchar not null
);

create table if not exists ev_charging_vault.hub_cdr (
    cdr_hk     bytea primary key,
    cdr_bk     varchar not null,
    load_dts   timestamp not null,
    rec_src    varchar not null
);

-- ---------------------------------------------------------------------------
-- Links
-- ---------------------------------------------------------------------------
create table if not exists ev_charging_vault.link_session_assets (
    link_hk      bytea primary key,
    session_hk   bytea not null references ev_charging_vault.hub_session(session_hk),
    location_hk  bytea not null references ev_charging_vault.hub_location(location_hk),
    evse_hk      bytea not null references ev_charging_vault.hub_evse(evse_hk),
    connector_hk bytea not null references ev_charging_vault.hub_connector(connector_hk),
    token_hk     bytea references ev_charging_vault.hub_token(token_hk),
    load_dts     timestamp not null,
    rec_src      varchar not null
);

create table if not exists ev_charging_vault.link_station_evse (
    link_hk    bytea primary key,
    station_hk bytea not null references ev_charging_vault.hub_station(station_hk),
    evse_hk    bytea not null references ev_charging_vault.hub_evse(evse_hk),
    load_dts   timestamp not null,
    rec_src    varchar not null
);

create table if not exists ev_charging_vault.link_connector_tariff (
    link_hk      bytea primary key,
    connector_hk bytea not null references ev_charging_vault.hub_connector(connector_hk),
    tariff_hk    bytea not null references ev_charging_vault.hub_tariff(tariff_hk),
    load_dts     timestamp not null,
    rec_src      varchar not null
);

create table if not exists ev_charging_vault.link_session_cdr (
    link_hk    bytea primary key,
    session_hk bytea not null references ev_charging_vault.hub_session(session_hk),
    cdr_hk     bytea not null references ev_charging_vault.hub_cdr(cdr_hk),
    load_dts   timestamp not null,
    rec_src    varchar not null
);

-- ---------------------------------------------------------------------------
-- Satellites (bitemporal)
-- ---------------------------------------------------------------------------
create table if not exists ev_charging_vault.sat_station_state (
    station_hk          bytea not null references ev_charging_vault.hub_station(station_hk),
    load_dts            timestamp not null,
    load_end_dts        timestamp,
    hash_diff           bytea not null,
    vendor_name         varchar(64) not null,
    model               varchar(64),
    firmware_version    varchar(64),
    registration_status varchar(16) not null,
    last_boot_at        timestamp,
    last_heartbeat_at   timestamp,
    status              varchar(16) not null,
    ocpp_version        varchar(8) not null,
    rec_src             varchar not null,
    primary key (station_hk, load_dts)
);

create table if not exists ev_charging_vault.sat_evse_status (
    evse_hk      bytea not null references ev_charging_vault.hub_evse(evse_hk),
    load_dts     timestamp not null,
    load_end_dts timestamp,
    hash_diff    bytea not null,
    status       varchar(16) not null,
    last_updated timestamp,
    rec_src      varchar not null,
    primary key (evse_hk, load_dts)
);

create table if not exists ev_charging_vault.sat_session_state (
    session_hk          bytea not null references ev_charging_vault.hub_session(session_hk),
    load_dts            timestamp not null,
    load_end_dts        timestamp,
    hash_diff           bytea not null,
    start_date_time     timestamp not null,
    end_date_time       timestamp,
    kwh                 numeric(12, 3) not null default 0,
    auth_method         varchar(16) not null,
    status              varchar(16) not null,
    total_cost_excl_vat numeric(10, 4),
    total_cost_incl_vat numeric(10, 4),
    currency            varchar(3),
    rec_src             varchar not null,
    primary key (session_hk, load_dts)
);

create table if not exists ev_charging_vault.sat_meter_value (
    session_hk    bytea not null references ev_charging_vault.hub_session(session_hk),
    timestamp     timestamp not null,
    measurand     varchar(32) not null,
    load_dts      timestamp not null,
    hash_diff     bytea not null,
    value_numeric numeric(20, 6),
    unit          varchar(8),
    context       varchar(16),
    phase         varchar(8),
    rec_src       varchar not null,
    primary key (session_hk, timestamp, measurand, load_dts)
);

create table if not exists ev_charging_vault.sat_cdr (
    cdr_hk                  bytea not null references ev_charging_vault.hub_cdr(cdr_hk),
    load_dts                timestamp not null,
    load_end_dts            timestamp,
    hash_diff               bytea not null,
    start_date_time         timestamp not null,
    end_date_time           timestamp not null,
    total_cost_incl_vat     numeric(10, 4) not null,
    total_energy_kwh        numeric(12, 3) not null,
    currency                varchar(3) not null,
    invoice_reference_id    varchar(36),
    roaming_cdr             boolean not null,
    rec_src                 varchar not null,
    primary key (cdr_hk, load_dts)
);

create table if not exists ev_charging_vault.sat_tariff (
    tariff_hk        bytea not null references ev_charging_vault.hub_tariff(tariff_hk),
    load_dts         timestamp not null,
    load_end_dts     timestamp,
    hash_diff        bytea not null,
    currency         varchar(3) not null,
    tariff_type      varchar(16),
    name             varchar(255),
    min_price_excl_vat numeric(8, 2),
    max_price_excl_vat numeric(8, 2),
    start_date_time  timestamp,
    end_date_time    timestamp,
    rec_src          varchar not null,
    primary key (tariff_hk, load_dts)
);

create table if not exists ev_charging_vault.sat_status_notification (
    station_hk    bytea not null references ev_charging_vault.hub_station(station_hk),
    timestamp     timestamp not null,
    load_dts      timestamp not null,
    hash_diff     bytea not null,
    connector_status varchar(16) not null,
    error_code    varchar(32),
    info          varchar(255),
    rec_src       varchar not null,
    primary key (station_hk, timestamp, load_dts)
);
