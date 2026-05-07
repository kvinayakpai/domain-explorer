-- =============================================================================
-- Smart Metering — dimensional mart
-- Star schema. Facts: interval_15m, register_daily, event, billing_monthly.
-- =============================================================================

create schema if not exists smart_metering_dim;

create table if not exists smart_metering_dim.dim_date (
    date_key      integer primary key,
    date_actual   date not null,
    day_of_week   smallint not null,
    iso_week      smallint not null,
    fiscal_period varchar(8)
);

create table if not exists smart_metering_dim.dim_time (
    time_key       integer primary key,
    hour_of_day    smallint not null,
    minute_of_hour smallint not null
);

create table if not exists smart_metering_dim.dim_meter (
    meter_key      bigint primary key,
    meter_id       varchar not null,
    serial_number  varchar(32),
    manufacturer_code varchar(8),
    model          varchar(32),
    meter_form     varchar(8),
    meter_type     varchar(16),
    valid_from     timestamp not null,
    valid_to       timestamp,
    is_current     boolean not null
);

create table if not exists smart_metering_dim.dim_service_point (
    service_point_key   bigint primary key,
    service_point_id    varchar not null,
    service_category    varchar(16),
    nominal_voltage_v   integer,
    address_postal_code varchar(16),
    feeder_id           varchar,
    transformer_id      varchar,
    rate_class_id       varchar,
    valid_from          timestamp not null,
    valid_to            timestamp,
    is_current          boolean not null
);

create table if not exists smart_metering_dim.dim_rate_class (
    rate_class_key   bigint primary key,
    rate_class_id    varchar not null,
    name             varchar(64),
    customer_segment varchar(16),
    valid_from       timestamp not null,
    valid_to         timestamp,
    is_current       boolean not null
);

create table if not exists smart_metering_dim.dim_tou_bucket (
    tou_bucket_key smallint primary key,
    bucket_code    varchar(8) not null,
    bucket_label   varchar(32) not null,
    season         varchar(16)
);

create table if not exists smart_metering_dim.dim_event_type (
    event_type_key smallint primary key,
    event_code     varchar(8),
    event_type     varchar(32) not null,
    severity       varchar(8) not null
);

create table if not exists smart_metering_dim.dim_obis (
    obis_key   integer primary key,
    obis_code  varchar(20) not null,
    label      varchar(64) not null,
    uom        varchar(8) not null
);

-- ---------------------------------------------------------------------------
-- Facts
-- ---------------------------------------------------------------------------

-- Grain: meter x 15-minute interval.
create table if not exists smart_metering_dim.fact_interval_15m (
    meter_key       bigint not null references smart_metering_dim.dim_meter(meter_key),
    service_point_key bigint references smart_metering_dim.dim_service_point(service_point_key),
    date_key        integer not null references smart_metering_dim.dim_date(date_key),
    time_key        integer not null references smart_metering_dim.dim_time(time_key),
    obis_key        integer not null references smart_metering_dim.dim_obis(obis_key),
    tou_bucket_key  smallint references smart_metering_dim.dim_tou_bucket(tou_bucket_key),
    kwh_value       numeric(18, 6),
    is_estimated    boolean not null default false,
    is_late         boolean not null default false,
    primary key (meter_key, date_key, time_key, obis_key)
);

-- Grain: meter x day register snapshot.
create table if not exists smart_metering_dim.fact_register_daily (
    meter_key      bigint not null references smart_metering_dim.dim_meter(meter_key),
    date_key       integer not null references smart_metering_dim.dim_date(date_key),
    obis_key       integer not null references smart_metering_dim.dim_obis(obis_key),
    register_value numeric(20, 6),
    delta_kwh      numeric(18, 6),
    vee_status     varchar(8),
    primary key (meter_key, date_key, obis_key)
);

-- Grain: meter event.
create table if not exists smart_metering_dim.fact_event (
    event_id        bigint primary key,
    meter_key       bigint not null references smart_metering_dim.dim_meter(meter_key),
    date_key        integer not null references smart_metering_dim.dim_date(date_key),
    time_key        integer references smart_metering_dim.dim_time(time_key),
    event_type_key  smallint not null references smart_metering_dim.dim_event_type(event_type_key),
    received_lag_seconds integer
);

-- Grain: service_point x billing month.
create table if not exists smart_metering_dim.fact_bill (
    bill_id            varchar primary key,
    service_point_key  bigint not null references smart_metering_dim.dim_service_point(service_point_key),
    rate_class_key     bigint not null references smart_metering_dim.dim_rate_class(rate_class_key),
    period_start_date_key integer not null references smart_metering_dim.dim_date(date_key),
    period_end_date_key   integer not null references smart_metering_dim.dim_date(date_key),
    kwh_consumed       numeric(18, 6),
    peak_demand_kw     numeric(12, 4),
    energy_charge      numeric(12, 2),
    demand_charge      numeric(12, 2),
    customer_charge    numeric(12, 2),
    total_amount       numeric(12, 2) not null,
    adjustment_count   smallint not null default 0,
    is_estimated       boolean not null default false
);

-- Grain: meter x day operational summary (read-completion fact).
create table if not exists smart_metering_dim.fact_meter_daily (
    meter_key             bigint not null references smart_metering_dim.dim_meter(meter_key),
    date_key              integer not null references smart_metering_dim.dim_date(date_key),
    scheduled_reads       integer not null,
    successful_reads      integer not null,
    estimated_reads       integer not null,
    late_reads            integer not null,
    tamper_events         integer not null,
    outage_minutes        integer not null,
    avg_signal_strength_dbm smallint,
    primary key (meter_key, date_key)
);
