-- =============================================================================
-- Smart Metering — 3NF schema
-- Source standards: ANSI C12.19 (end-device tables), C12.22 (transport),
-- DLMS/COSEM IEC 62056 (OBIS codes), CIM IEC 61968-9 (MeterReadings,
-- EndDeviceEvent), MultiSpeak v5.2.
-- =============================================================================

create schema if not exists smart_metering_3nf;

create table if not exists smart_metering_3nf.service_point (
    service_point_id    varchar primary key,
    usage_point_kind    varchar(16),
    service_category    varchar(16) not null,
    nominal_voltage_v   integer,
    phase_code          varchar(8),
    connection_state    varchar(16) not null,
    latitude            numeric(9, 6),
    longitude           numeric(9, 6),
    address_line        varchar(255),
    address_city        varchar(64),
    address_postal_code varchar(16),
    rate_class_id       varchar,
    customer_id         varchar,
    feeder_id           varchar,
    transformer_id      varchar
);

create table if not exists smart_metering_3nf.communication_module (
    communication_module_id varchar primary key,
    meter_id                varchar,
    media_type              varchar(16) not null,
    imei                    varchar(16),
    imsi                    varchar(16),
    mac_address             varchar(20),
    firmware_version        varchar(16),
    signal_strength_dbm     smallint,
    head_end_ip             varchar(64),
    last_seen_ts            timestamp,
    status                  varchar(16) not null
);

create table if not exists smart_metering_3nf.meter (
    meter_id                varchar primary key,
    serial_number           varchar(32) not null,
    service_point_id        varchar references smart_metering_3nf.service_point(service_point_id),
    manufacturer_code       varchar(8),
    model                   varchar(32),
    hardware_version        varchar(16),
    firmware_version        varchar(16),
    meter_form              varchar(8),
    meter_type              varchar(16) not null,
    phases                  smallint,
    ct_ratio                numeric(8, 3),
    vt_ratio                numeric(8, 3),
    install_date            date,
    removal_date            date,
    status                  varchar(16) not null,
    communication_module_id varchar references smart_metering_3nf.communication_module(communication_module_id),
    timezone                varchar(32)
);

create table if not exists smart_metering_3nf.tou_schedule (
    tou_schedule_id    varchar primary key,
    name               varchar(64) not null,
    effective_from     date not null,
    effective_to       date,
    tariff_class       varchar(32),
    number_of_buckets  smallint,
    timezone           varchar(32)
);

create table if not exists smart_metering_3nf.tou_bucket (
    bucket_id            varchar primary key,
    tou_schedule_id      varchar not null references smart_metering_3nf.tou_schedule(tou_schedule_id),
    bucket_code          varchar(8) not null,
    bucket_label         varchar(32),
    start_minute_of_day  smallint not null,
    end_minute_of_day    smallint not null,
    applicable_days      varchar(8),
    applicable_months    varchar(16),
    rate_currency        varchar(3),
    rate_per_kwh         numeric(10, 5)
);

create table if not exists smart_metering_3nf.rate_class (
    rate_class_id       varchar primary key,
    name                varchar(64) not null,
    customer_segment    varchar(16),
    tou_schedule_id     varchar references smart_metering_3nf.tou_schedule(tou_schedule_id),
    demand_charge_kw    numeric(10, 4),
    customer_charge     numeric(10, 4),
    effective_from      date not null,
    effective_to        date,
    regulatory_filing_id varchar
);

create table if not exists smart_metering_3nf.register_reading (
    reading_id          bigint primary key,
    meter_id            varchar not null references smart_metering_3nf.meter(meter_id),
    read_ts             timestamp not null,
    source              varchar(16) not null,
    obis_code           varchar(20) not null,
    register_value      numeric(20, 6),
    register_uom        varchar(8) not null,
    register_multiplier numeric(8, 3) not null default 1,
    status_flags        varchar(16),
    vee_status          varchar(8) not null default 'raw'
);

create table if not exists smart_metering_3nf.interval_reading (
    meter_id           varchar not null references smart_metering_3nf.meter(meter_id),
    channel_no         smallint not null,
    interval_start     timestamp not null,
    interval_end       timestamp,
    interval_minutes   smallint not null,
    obis_code          varchar(20),
    kwh_value          numeric(18, 6),
    pulse_count        bigint,
    status_byte        varchar(4),
    vee_status         varchar(8) not null default 'raw',
    source_ts          timestamp,
    primary key (meter_id, channel_no, interval_start)
);

create table if not exists smart_metering_3nf.demand_reading (
    demand_id              bigint primary key,
    meter_id               varchar not null references smart_metering_3nf.meter(meter_id),
    read_ts                timestamp not null,
    obis_code              varchar(20) not null,
    demand_value_kw        numeric(12, 4),
    demand_window_minutes  smallint,
    occurrence_ts          timestamp,
    tou_bucket             varchar(8)
);

create table if not exists smart_metering_3nf.meter_event (
    event_id      bigint primary key,
    meter_id      varchar not null references smart_metering_3nf.meter(meter_id),
    event_ts      timestamp not null,
    received_ts   timestamp,
    event_code    varchar(8),
    event_type    varchar(32) not null,
    severity      varchar(8) not null,
    source        varchar(8) not null,
    argument_data text
);

create table if not exists smart_metering_3nf.outage_event (
    outage_event_id        varchar primary key,
    meter_id               varchar not null references smart_metering_3nf.meter(meter_id),
    outage_start_ts        timestamp not null,
    restoration_ts         timestamp,
    cause_code             varchar(16),
    feeder_id              varchar,
    confirmed_oms_event_id varchar,
    nominal_voltage_v      integer
);

create table if not exists smart_metering_3nf.disconnect_command (
    command_id      varchar primary key,
    meter_id        varchar not null references smart_metering_3nf.meter(meter_id),
    command_type    varchar(16) not null,
    requested_ts    timestamp not null,
    dispatched_ts   timestamp,
    confirmed_ts    timestamp,
    result_code     varchar(16),
    requested_by    varchar,
    reason_code     varchar(16)
);

create table if not exists smart_metering_3nf.service_order (
    service_order_id varchar primary key,
    service_point_id varchar references smart_metering_3nf.service_point(service_point_id),
    meter_id         varchar,
    order_type       varchar(16) not null,
    priority         varchar(8),
    scheduled_date   date,
    assigned_crew    varchar(32),
    status           varchar(16) not null,
    completion_ts    timestamp,
    completion_notes text
);

create table if not exists smart_metering_3nf.vee_rule (
    vee_rule_id     varchar primary key,
    name            varchar(64) not null,
    rule_type       varchar(16) not null,
    parameter_json  text,
    action          varchar(16) not null,
    enabled         boolean not null default true
);

create table if not exists smart_metering_3nf.vee_violation (
    violation_id     bigint primary key,
    meter_id         varchar not null references smart_metering_3nf.meter(meter_id),
    vee_rule_id      varchar not null references smart_metering_3nf.vee_rule(vee_rule_id),
    reading_id       bigint,
    violation_ts     timestamp not null,
    original_value   numeric(20, 6),
    corrected_value  numeric(20, 6),
    action_taken     varchar(16) not null,
    reviewer_id      varchar
);

create table if not exists smart_metering_3nf.firmware_release (
    firmware_release_id varchar primary key,
    vendor              varchar(64) not null,
    model               varchar(64),
    version             varchar(16) not null,
    release_notes_uri   varchar(255),
    release_ts          timestamp not null,
    status              varchar(16) not null
);

create table if not exists smart_metering_3nf.firmware_deployment (
    deployment_id        varchar primary key,
    meter_id             varchar not null references smart_metering_3nf.meter(meter_id),
    firmware_release_id  varchar not null references smart_metering_3nf.firmware_release(firmware_release_id),
    scheduled_ts         timestamp,
    started_ts           timestamp,
    completed_ts         timestamp,
    result               varchar(16) not null,
    bytes_transferred    integer,
    error_code           varchar(16)
);

create table if not exists smart_metering_3nf.bill (
    bill_id            varchar primary key,
    service_point_id   varchar not null references smart_metering_3nf.service_point(service_point_id),
    bill_period_start  date not null,
    bill_period_end    date not null,
    opening_register   numeric(20, 6),
    closing_register   numeric(20, 6),
    kwh_consumed       numeric(18, 6),
    peak_demand_kw     numeric(12, 4),
    amount_currency    varchar(3) not null default 'USD',
    energy_charge      numeric(12, 2),
    demand_charge      numeric(12, 2),
    customer_charge    numeric(12, 2),
    total_amount       numeric(12, 2) not null,
    issued_ts          timestamp not null,
    status             varchar(16) not null,
    adjustment_count   smallint not null default 0
);
