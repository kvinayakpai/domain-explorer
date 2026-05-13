-- =============================================================================
-- Predictive Maintenance — Kimball dimensional schema
-- Star: fct_sensor_readings_pm, fct_failure_events, fct_work_orders_pm,
--       fct_asset_availability
-- Conformed dims: dim_asset_pm, dim_sensor, dim_failure_mode, dim_date_pm,
--                 dim_model_version
-- =============================================================================

create schema if not exists predictive_maintenance_dim;

-- ---------- DIMS ----------
create table if not exists predictive_maintenance_dim.dim_date_pm (
    date_key      integer primary key,         -- yyyymmdd
    cal_date      date,
    day_of_week   smallint,
    day_name      varchar(12),
    month         smallint,
    month_name    varchar(12),
    quarter       smallint,
    year          smallint,
    is_weekend    boolean
);

create table if not exists predictive_maintenance_dim.dim_asset_pm (
    asset_sk            bigint primary key,
    asset_id            varchar(64) unique,
    tag_id              varchar(128),
    asset_class         varchar(64),
    manufacturer        varchar(128),
    model_number        varchar(128),
    site_id             varchar(64),
    area_id             varchar(64),
    line_id             varchar(64),
    criticality         varchar(8),
    design_life_hours   integer,
    rated_kw            numeric(10,2),
    status              varchar(16),
    valid_from          timestamp,
    valid_to            timestamp,
    is_current          boolean
);

create table if not exists predictive_maintenance_dim.dim_sensor (
    sensor_sk               bigint primary key,
    sensor_id               varchar(64) unique,
    asset_id                varchar(64),
    sensor_type             varchar(32),
    measurement_location    varchar(64),
    unit                    varchar(16),
    sampling_hz             numeric(10,2),
    alarm_low               numeric(15,6),
    alarm_high              numeric(15,6),
    status                  varchar(16)
);

create table if not exists predictive_maintenance_dim.dim_failure_mode (
    failure_mode_sk             bigint primary key,
    failure_mode_id             varchar(32) unique,
    fault_code                  varchar(16),
    description                 varchar(255),
    applicable_asset_class      varchar(64),
    characteristic_frequency_hz numeric(10,2),
    typical_p_f_interval_hours  integer,
    severity_tier               varchar(8)
);

create table if not exists predictive_maintenance_dim.dim_model_version (
    model_version_sk    bigint primary key,
    model_version_id    varchar(64) unique,
    algorithm           varchar(64),
    holdout_precision   numeric(5,4),
    holdout_recall      numeric(5,4),
    holdout_rul_mape    numeric(5,4),
    champion            boolean
);

-- ---------- FACTS ----------
-- Sensor-reading fact — pre-aggregated to hourly grain to keep this table tractable
-- (raw 1-min readings remain in the 3NF schema for model training).
create table if not exists predictive_maintenance_dim.fct_sensor_readings_pm (
    reading_id          bigint primary key,
    date_key            integer references predictive_maintenance_dim.dim_date_pm(date_key),
    asset_sk            bigint  references predictive_maintenance_dim.dim_asset_pm(asset_sk),
    sensor_sk           bigint  references predictive_maintenance_dim.dim_sensor(sensor_sk),
    reading_hour        timestamp,
    sample_count        integer,
    value_avg           numeric(15,6),
    value_max           numeric(15,6),
    value_min           numeric(15,6),
    value_stddev        numeric(15,6),
    pct_good_quality    numeric(5,4),
    anomaly_count       integer
);

create table if not exists predictive_maintenance_dim.fct_failure_events (
    failure_event_id        varchar(64) primary key,
    date_key                integer references predictive_maintenance_dim.dim_date_pm(date_key),
    asset_sk                bigint  references predictive_maintenance_dim.dim_asset_pm(asset_sk),
    failure_mode_sk         bigint  references predictive_maintenance_dim.dim_failure_mode(failure_mode_sk),
    failure_ts              timestamp,
    detected_by             varchar(16),
    was_predicted           boolean,
    lead_time_hours         numeric(10,2),                 -- prediction lead time
    downtime_minutes        integer,
    production_loss_units   bigint,
    cost_usd                numeric(15,2)
);

create table if not exists predictive_maintenance_dim.fct_work_orders_pm (
    work_order_id           varchar(64) primary key,
    date_key                integer references predictive_maintenance_dim.dim_date_pm(date_key),
    asset_sk                bigint  references predictive_maintenance_dim.dim_asset_pm(asset_sk),
    failure_mode_sk         bigint  references predictive_maintenance_dim.dim_failure_mode(failure_mode_sk),
    wo_type                 varchar(16),
    wo_priority             smallint,
    is_predictive           boolean,
    is_emergency            boolean,
    scheduled_start         timestamp,
    actual_start            timestamp,
    actual_end              timestamp,
    repair_minutes          integer,                       -- actual_end - actual_start
    labor_hours             numeric(8,2),
    parts_cost_usd          numeric(15,2),
    labor_cost_usd          numeric(15,2),
    total_cost_usd          numeric(15,2),
    status                  varchar(16)
);

-- Daily asset-availability fact for MTBF/MTTR/OEE roll-ups.
create table if not exists predictive_maintenance_dim.fct_asset_availability (
    asset_availability_id   varchar(64) primary key,
    date_key                integer references predictive_maintenance_dim.dim_date_pm(date_key),
    asset_sk                bigint  references predictive_maintenance_dim.dim_asset_pm(asset_sk),
    scheduled_minutes       integer,
    runtime_minutes         integer,
    planned_downtime_min    integer,
    unplanned_downtime_min  integer,
    failure_count           smallint,
    repair_minutes_total    integer,
    availability_pct        numeric(7,4),
    mtbf_hours              numeric(12,4),
    mttr_minutes            numeric(12,4)
);

-- Predictions fact — one row per model output for KPI surfaces (precision/recall/RUL).
create table if not exists predictive_maintenance_dim.fct_predictions (
    prediction_id           varchar(64) primary key,
    date_key                integer references predictive_maintenance_dim.dim_date_pm(date_key),
    asset_sk                bigint  references predictive_maintenance_dim.dim_asset_pm(asset_sk),
    failure_mode_sk         bigint  references predictive_maintenance_dim.dim_failure_mode(failure_mode_sk),
    model_version_sk        bigint  references predictive_maintenance_dim.dim_model_version(model_version_sk),
    prediction_ts           timestamp,
    prediction_type         varchar(16),
    anomaly_score           numeric(8,4),
    rul_hours               integer,
    severity                varchar(8),
    is_true_positive        boolean,
    is_false_positive       boolean,
    is_false_negative       boolean,
    is_true_negative        boolean
);

-- Helpful indexes
create index if not exists ix_fct_reading_asset    on predictive_maintenance_dim.fct_sensor_readings_pm(asset_sk, reading_hour);
create index if not exists ix_fct_reading_date     on predictive_maintenance_dim.fct_sensor_readings_pm(date_key);
create index if not exists ix_fct_failure_asset    on predictive_maintenance_dim.fct_failure_events(asset_sk, failure_ts);
create index if not exists ix_fct_wo_asset         on predictive_maintenance_dim.fct_work_orders_pm(asset_sk, scheduled_start);
create index if not exists ix_fct_availability     on predictive_maintenance_dim.fct_asset_availability(asset_sk, date_key);
create index if not exists ix_fct_predictions      on predictive_maintenance_dim.fct_predictions(asset_sk, prediction_ts);
