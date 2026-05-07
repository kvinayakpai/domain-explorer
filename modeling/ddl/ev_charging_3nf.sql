-- =============================================================================
-- EV Charging Operations — 3NF schema
-- Source standards: OCPP 2.0.1 (IEC 63584) for station-CSMS messaging,
-- OCPI 2.2.1 for CPO-EMSP roaming, ISO 15118 V2G, OpenADR 2.0b for DR.
-- =============================================================================

create schema if not exists ev_charging_3nf;

create table if not exists ev_charging_3nf.location (
    location_id   varchar primary key,
    country_code  varchar(2) not null,
    party_id      varchar(3) not null,
    name          varchar(255) not null,
    address       varchar(255),
    city          varchar(64),
    postal_code   varchar(16),
    country_iso   varchar(3),
    latitude      numeric(9, 6),
    longitude     numeric(9, 6),
    time_zone     varchar(32),
    parking_type  varchar(32),
    facilities    text,
    opening_times text,
    publish       boolean not null default true,
    last_updated  timestamp not null
);

create table if not exists ev_charging_3nf.charging_station (
    station_id           varchar primary key,
    location_id          varchar not null references ev_charging_3nf.location(location_id),
    vendor_name          varchar(64) not null,
    model                varchar(64),
    serial_number        varchar(64),
    firmware_version     varchar(64),
    modem_iccid          varchar(20),
    modem_imsi           varchar(20),
    registration_status  varchar(16) not null,
    boot_reason          varchar(32),
    last_boot_at         timestamp,
    last_heartbeat_at    timestamp,
    status               varchar(16) not null,
    ocpp_version         varchar(8) not null
);

create table if not exists ev_charging_3nf.evse (
    evse_id              varchar primary key,
    station_id           varchar not null references ev_charging_3nf.charging_station(station_id),
    physical_reference   varchar(16),
    status               varchar(16) not null,
    status_schedule      text,
    capabilities         text,
    floor_level          varchar(8),
    directions           text,
    parking_restrictions text,
    last_updated         timestamp not null
);

create table if not exists ev_charging_3nf.connector (
    connector_id          varchar primary key,
    evse_id               varchar not null references ev_charging_3nf.evse(evse_id),
    standard              varchar(16) not null,
    format                varchar(8) not null,
    power_type            varchar(16) not null,
    max_voltage_v         integer,
    max_amperage_a        integer,
    max_electric_power_w  integer,
    tariff_ids            text,
    last_updated          timestamp not null
);

create table if not exists ev_charging_3nf.token (
    token_uid            varchar(36) primary key,
    country_code         varchar(2) not null,
    party_id             varchar(3) not null,
    type                 varchar(16) not null,
    contract_id          varchar(36),
    visual_number        varchar(64),
    issuer               varchar(64),
    group_id             varchar(36),
    valid                boolean not null,
    whitelist            varchar(16),
    language             varchar(2),
    default_profile_type varchar(16),
    last_updated         timestamp not null
);

create table if not exists ev_charging_3nf.tariff (
    tariff_id              varchar(36) primary key,
    country_code           varchar(2) not null,
    party_id               varchar(3) not null,
    currency               varchar(3) not null,
    tariff_type            varchar(16),
    name                   varchar(255),
    min_price_excl_vat     numeric(8, 2),
    min_price_incl_vat     numeric(8, 2),
    max_price_excl_vat     numeric(8, 2),
    max_price_incl_vat     numeric(8, 2),
    start_date_time        timestamp,
    end_date_time          timestamp,
    energy_mix_supplier_name varchar(64),
    last_updated           timestamp not null
);

create table if not exists ev_charging_3nf.tariff_element (
    tariff_element_id        varchar primary key,
    tariff_id                varchar(36) not null references ev_charging_3nf.tariff(tariff_id),
    element_index            smallint not null,
    price_component_type     varchar(16) not null,
    price_per_unit           numeric(10, 5) not null,
    vat_pct                  numeric(5, 2),
    step_size                integer,
    restriction_min_kwh      numeric(10, 3),
    restriction_max_kwh      numeric(10, 3),
    restriction_min_power    numeric(10, 3),
    restriction_max_power    numeric(10, 3),
    restriction_start_time   varchar(8),
    restriction_end_time     varchar(8),
    restriction_day_of_week  varchar(32)
);

create table if not exists ev_charging_3nf.charging_session (
    session_id              varchar(36) primary key,
    country_code            varchar(2) not null,
    party_id                varchar(3) not null,
    location_id             varchar references ev_charging_3nf.location(location_id),
    evse_id                 varchar references ev_charging_3nf.evse(evse_id),
    connector_id            varchar references ev_charging_3nf.connector(connector_id),
    token_uid               varchar(36) references ev_charging_3nf.token(token_uid),
    meter_id                varchar(64),
    start_date_time         timestamp not null,
    end_date_time           timestamp,
    kwh                     numeric(12, 3) not null default 0,
    cdr_token_contract_id   varchar(36),
    auth_method             varchar(16) not null,
    authorization_reference varchar(36),
    status                  varchar(16) not null,
    charging_periods_count  integer not null default 0,
    total_cost_excl_vat     numeric(10, 4),
    total_cost_incl_vat     numeric(10, 4),
    currency                varchar(3),
    last_updated            timestamp not null
);

create table if not exists ev_charging_3nf.charging_period (
    period_id        varchar primary key,
    session_id       varchar(36) not null references ev_charging_3nf.charging_session(session_id),
    start_date_time  timestamp not null,
    dimension_type   varchar(16) not null,
    dimension_volume numeric(12, 3) not null,
    tariff_id        varchar(36) references ev_charging_3nf.tariff(tariff_id)
);

create table if not exists ev_charging_3nf.meter_value (
    meter_value_id     bigint primary key,
    session_id         varchar(36) not null references ev_charging_3nf.charging_session(session_id),
    timestamp          timestamp not null,
    measurand          varchar(32) not null,
    phase              varchar(8),
    location           varchar(8),
    context            varchar(16),
    unit               varchar(8),
    value_numeric      numeric(20, 6),
    signed_meter_value text
);

create table if not exists ev_charging_3nf.cdr (
    cdr_id                  varchar(36) primary key,
    country_code            varchar(2) not null,
    party_id                varchar(3) not null,
    start_date_time         timestamp not null,
    end_date_time           timestamp not null,
    session_id              varchar(36) references ev_charging_3nf.charging_session(session_id),
    cdr_token_uid           varchar(36),
    cdr_token_type          varchar(16),
    cdr_location_id         varchar,
    meter_id                varchar(64),
    total_cost_excl_vat     numeric(10, 4),
    total_cost_incl_vat     numeric(10, 4) not null,
    total_energy_kwh        numeric(12, 3) not null,
    total_time_hours        numeric(8, 3),
    total_parking_time_hours numeric(8, 3),
    currency                varchar(3) not null,
    invoice_reference_id    varchar(36),
    roaming_cdr             boolean not null default false,
    last_updated            timestamp not null
);

create table if not exists ev_charging_3nf.charging_profile (
    charging_profile_id      varchar primary key,
    station_id               varchar references ev_charging_3nf.charging_station(station_id),
    evse_id                  varchar references ev_charging_3nf.evse(evse_id),
    stack_level              smallint not null,
    charging_profile_purpose varchar(32) not null,
    charging_profile_kind    varchar(16) not null,
    recurrency_kind          varchar(8),
    valid_from               timestamp,
    valid_to                 timestamp,
    charging_rate_unit       varchar(8) not null,
    schedule_period_count    integer,
    created_at               timestamp not null
);

create table if not exists ev_charging_3nf.status_notification (
    status_notification_id bigint primary key,
    station_id             varchar not null references ev_charging_3nf.charging_station(station_id),
    evse_id                varchar references ev_charging_3nf.evse(evse_id),
    connector_id           varchar references ev_charging_3nf.connector(connector_id),
    timestamp              timestamp not null,
    connector_status       varchar(16) not null,
    error_code             varchar(32),
    info                   varchar(255),
    vendor_id              varchar(64),
    vendor_error_code      varchar(64)
);

create table if not exists ev_charging_3nf.firmware_release (
    firmware_release_id   varchar primary key,
    vendor_name           varchar(64) not null,
    model                 varchar(64),
    version               varchar(64) not null,
    release_notes_uri     varchar(255),
    signed_firmware_uri   varchar(255),
    signature             varchar(255),
    signing_certificate   text,
    released_at           timestamp not null
);

create table if not exists ev_charging_3nf.firmware_update (
    update_id           varchar primary key,
    station_id          varchar not null references ev_charging_3nf.charging_station(station_id),
    firmware_release_id varchar not null references ev_charging_3nf.firmware_release(firmware_release_id),
    requested_at        timestamp not null,
    retrieve_date_time  timestamp,
    firmware_status     varchar(32) not null,
    completed_at        timestamp
);

create table if not exists ev_charging_3nf.dr_event (
    dr_event_id        varchar primary key,
    program_id         varchar(64),
    vtn_party_id       varchar(64),
    ven_party_id       varchar(64),
    signal_type        varchar(16) not null,
    signal_units       varchar(8),
    dtstart            timestamp not null,
    duration           varchar(16),
    priority           smallint,
    opt_in             boolean,
    response_required  boolean not null default true,
    created_at         timestamp not null
);
