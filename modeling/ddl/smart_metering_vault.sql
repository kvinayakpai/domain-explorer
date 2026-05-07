-- =============================================================================
-- Smart Metering — Data Vault 2.0
-- Hubs: meter, service_point, comm_module, firmware_release. Bitemporal sat
-- on register reading allows reconstructing any meter's billing baseline.
-- =============================================================================

create schema if not exists smart_metering_vault;

create table if not exists smart_metering_vault.hub_meter (
    meter_hk     bytea primary key,
    meter_bk     varchar not null,
    serial_number varchar(32),
    load_dts     timestamp not null,
    rec_src      varchar not null
);

create table if not exists smart_metering_vault.hub_service_point (
    service_point_hk bytea primary key,
    service_point_bk varchar not null,
    load_dts         timestamp not null,
    rec_src          varchar not null
);

create table if not exists smart_metering_vault.hub_communication_module (
    communication_module_hk bytea primary key,
    communication_module_bk varchar not null,
    load_dts                timestamp not null,
    rec_src                 varchar not null
);

create table if not exists smart_metering_vault.hub_firmware_release (
    firmware_release_hk bytea primary key,
    firmware_release_bk varchar not null,
    load_dts            timestamp not null,
    rec_src             varchar not null
);

create table if not exists smart_metering_vault.hub_outage (
    outage_hk     bytea primary key,
    outage_bk     varchar not null,
    load_dts      timestamp not null,
    rec_src       varchar not null
);

-- ---------------------------------------------------------------------------
-- Links
-- ---------------------------------------------------------------------------
create table if not exists smart_metering_vault.link_meter_service_point (
    link_hk           bytea primary key,
    meter_hk          bytea not null references smart_metering_vault.hub_meter(meter_hk),
    service_point_hk  bytea not null references smart_metering_vault.hub_service_point(service_point_hk),
    load_dts          timestamp not null,
    rec_src           varchar not null
);

create table if not exists smart_metering_vault.link_meter_comm (
    link_hk                 bytea primary key,
    meter_hk                bytea not null references smart_metering_vault.hub_meter(meter_hk),
    communication_module_hk bytea not null references smart_metering_vault.hub_communication_module(communication_module_hk),
    load_dts                timestamp not null,
    rec_src                 varchar not null
);

create table if not exists smart_metering_vault.link_outage_meter (
    link_hk      bytea primary key,
    outage_hk    bytea not null references smart_metering_vault.hub_outage(outage_hk),
    meter_hk     bytea not null references smart_metering_vault.hub_meter(meter_hk),
    load_dts     timestamp not null,
    rec_src      varchar not null
);

create table if not exists smart_metering_vault.link_firmware_deployment (
    link_hk             bytea primary key,
    meter_hk            bytea not null references smart_metering_vault.hub_meter(meter_hk),
    firmware_release_hk bytea not null references smart_metering_vault.hub_firmware_release(firmware_release_hk),
    deployment_bk       varchar not null,
    load_dts            timestamp not null,
    rec_src             varchar not null
);

-- ---------------------------------------------------------------------------
-- Satellites (bitemporal)
-- ---------------------------------------------------------------------------
create table if not exists smart_metering_vault.sat_meter_descriptive (
    meter_hk         bytea not null references smart_metering_vault.hub_meter(meter_hk),
    load_dts         timestamp not null,
    load_end_dts     timestamp,
    hash_diff        bytea not null,
    manufacturer_code varchar(8),
    model            varchar(32),
    hardware_version varchar(16),
    firmware_version varchar(16),
    meter_form       varchar(8),
    meter_type       varchar(16) not null,
    phases           smallint,
    ct_ratio         numeric(8, 3),
    vt_ratio         numeric(8, 3),
    install_date     date,
    removal_date     date,
    status           varchar(16) not null,
    timezone         varchar(32),
    rec_src          varchar not null,
    primary key (meter_hk, load_dts)
);

create table if not exists smart_metering_vault.sat_service_point_descriptive (
    service_point_hk    bytea not null references smart_metering_vault.hub_service_point(service_point_hk),
    load_dts            timestamp not null,
    load_end_dts        timestamp,
    hash_diff           bytea not null,
    usage_point_kind    varchar(16),
    service_category    varchar(16) not null,
    nominal_voltage_v   integer,
    phase_code          varchar(8),
    connection_state    varchar(16) not null,
    address_postal_code varchar(16),
    rate_class_id       varchar,
    feeder_id           varchar,
    transformer_id      varchar,
    rec_src             varchar not null,
    primary key (service_point_hk, load_dts)
);

create table if not exists smart_metering_vault.sat_register_reading (
    meter_hk            bytea not null references smart_metering_vault.hub_meter(meter_hk),
    obis_code           varchar(20) not null,
    read_ts             timestamp not null,
    load_dts            timestamp not null,
    hash_diff           bytea not null,
    register_value      numeric(20, 6),
    register_uom        varchar(8) not null,
    register_multiplier numeric(8, 3),
    status_flags        varchar(16),
    vee_status          varchar(8) not null,
    rec_src             varchar not null,
    primary key (meter_hk, obis_code, read_ts, load_dts)
);

create table if not exists smart_metering_vault.sat_meter_event (
    meter_hk      bytea not null references smart_metering_vault.hub_meter(meter_hk),
    event_ts      timestamp not null,
    load_dts      timestamp not null,
    hash_diff     bytea not null,
    event_code    varchar(8),
    event_type    varchar(32) not null,
    severity      varchar(8) not null,
    source        varchar(8) not null,
    argument_data text,
    rec_src       varchar not null,
    primary key (meter_hk, event_ts, load_dts)
);

create table if not exists smart_metering_vault.sat_outage_state (
    outage_hk          bytea not null references smart_metering_vault.hub_outage(outage_hk),
    load_dts           timestamp not null,
    load_end_dts       timestamp,
    hash_diff          bytea not null,
    outage_start_ts    timestamp not null,
    restoration_ts     timestamp,
    cause_code         varchar(16),
    feeder_id          varchar,
    confirmed_oms_event_id varchar,
    rec_src            varchar not null,
    primary key (outage_hk, load_dts)
);

create table if not exists smart_metering_vault.sat_firmware_deployment (
    link_hk           bytea not null,
    load_dts          timestamp not null,
    load_end_dts      timestamp,
    hash_diff         bytea not null,
    scheduled_ts      timestamp,
    started_ts        timestamp,
    completed_ts      timestamp,
    result            varchar(16) not null,
    bytes_transferred integer,
    error_code        varchar(16),
    rec_src           varchar not null,
    primary key (link_hk, load_dts)
);

create table if not exists smart_metering_vault.sat_communication_module_state (
    communication_module_hk bytea not null references smart_metering_vault.hub_communication_module(communication_module_hk),
    load_dts                timestamp not null,
    load_end_dts            timestamp,
    hash_diff               bytea not null,
    media_type              varchar(16) not null,
    firmware_version        varchar(16),
    signal_strength_dbm     smallint,
    head_end_ip             varchar(64),
    last_seen_ts            timestamp,
    status                  varchar(16) not null,
    rec_src                 varchar not null,
    primary key (communication_module_hk, load_dts)
);
