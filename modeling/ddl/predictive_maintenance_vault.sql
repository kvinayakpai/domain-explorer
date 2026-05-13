-- =============================================================================
-- Predictive Maintenance — Data Vault 2.0 schema
-- Hubs (business keys) + Links (relationships) + Satellites (descriptive,
-- insert-only, time-stamped). Mirrors ISO 14224 / ISO 13374 source contract.
-- =============================================================================

create schema if not exists predictive_maintenance_vault;

-- ---------- HUBS ----------
create table if not exists predictive_maintenance_vault.h_asset (
    hk_asset        varchar(32) primary key,         -- MD5(asset_id)
    asset_id        varchar(64) unique,
    load_dts        timestamp,
    record_source   varchar(64)
);

create table if not exists predictive_maintenance_vault.h_sensor (
    hk_sensor       varchar(32) primary key,
    sensor_id       varchar(64) unique,
    load_dts        timestamp,
    record_source   varchar(64)
);

create table if not exists predictive_maintenance_vault.h_failure_mode (
    hk_failure_mode varchar(32) primary key,
    failure_mode_id varchar(32) unique,
    load_dts        timestamp,
    record_source   varchar(64)
);

create table if not exists predictive_maintenance_vault.h_failure_event (
    hk_failure_event   varchar(32) primary key,
    failure_event_id   varchar(64) unique,
    load_dts           timestamp,
    record_source      varchar(64)
);

create table if not exists predictive_maintenance_vault.h_work_order (
    hk_work_order   varchar(32) primary key,
    work_order_id   varchar(64) unique,
    load_dts        timestamp,
    record_source   varchar(64)
);

create table if not exists predictive_maintenance_vault.h_prediction (
    hk_prediction   varchar(32) primary key,
    prediction_id   varchar(64) unique,
    load_dts        timestamp,
    record_source   varchar(64)
);

create table if not exists predictive_maintenance_vault.h_model_version (
    hk_model_version    varchar(32) primary key,
    model_version_id    varchar(64) unique,
    load_dts            timestamp,
    record_source       varchar(64)
);

create table if not exists predictive_maintenance_vault.h_maintenance_plan (
    hk_maintenance_plan varchar(32) primary key,
    plan_id             varchar(64) unique,
    load_dts            timestamp,
    record_source       varchar(64)
);

-- ---------- LINKS ----------
create table if not exists predictive_maintenance_vault.l_sensor_asset (
    hk_link         varchar(32) primary key,
    hk_sensor       varchar(32) references predictive_maintenance_vault.h_sensor(hk_sensor),
    hk_asset        varchar(32) references predictive_maintenance_vault.h_asset(hk_asset),
    load_dts        timestamp,
    record_source   varchar(64)
);

create table if not exists predictive_maintenance_vault.l_failure_asset (
    hk_link             varchar(32) primary key,
    hk_failure_event    varchar(32) references predictive_maintenance_vault.h_failure_event(hk_failure_event),
    hk_asset            varchar(32) references predictive_maintenance_vault.h_asset(hk_asset),
    hk_failure_mode     varchar(32) references predictive_maintenance_vault.h_failure_mode(hk_failure_mode),
    load_dts            timestamp,
    record_source       varchar(64)
);

create table if not exists predictive_maintenance_vault.l_wo_asset (
    hk_link             varchar(32) primary key,
    hk_work_order       varchar(32) references predictive_maintenance_vault.h_work_order(hk_work_order),
    hk_asset            varchar(32) references predictive_maintenance_vault.h_asset(hk_asset),
    hk_failure_event    varchar(32) references predictive_maintenance_vault.h_failure_event(hk_failure_event),
    load_dts            timestamp,
    record_source       varchar(64)
);

create table if not exists predictive_maintenance_vault.l_prediction_asset (
    hk_link             varchar(32) primary key,
    hk_prediction       varchar(32) references predictive_maintenance_vault.h_prediction(hk_prediction),
    hk_asset            varchar(32) references predictive_maintenance_vault.h_asset(hk_asset),
    hk_model_version    varchar(32) references predictive_maintenance_vault.h_model_version(hk_model_version),
    hk_failure_mode     varchar(32) references predictive_maintenance_vault.h_failure_mode(hk_failure_mode),
    load_dts            timestamp,
    record_source       varchar(64)
);

create table if not exists predictive_maintenance_vault.l_plan_asset (
    hk_link                 varchar(32) primary key,
    hk_maintenance_plan     varchar(32) references predictive_maintenance_vault.h_maintenance_plan(hk_maintenance_plan),
    hk_asset                varchar(32) references predictive_maintenance_vault.h_asset(hk_asset),
    load_dts                timestamp,
    record_source           varchar(64)
);

-- ---------- SATELLITES ----------
create table if not exists predictive_maintenance_vault.s_asset_descriptive (
    hk_asset            varchar(32) references predictive_maintenance_vault.h_asset(hk_asset),
    load_dts            timestamp,
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
    record_source       varchar(64),
    primary key (hk_asset, load_dts)
);

create table if not exists predictive_maintenance_vault.s_sensor_descriptive (
    hk_sensor               varchar(32) references predictive_maintenance_vault.h_sensor(hk_sensor),
    load_dts                timestamp,
    sensor_type             varchar(32),
    measurement_location    varchar(64),
    unit                    varchar(16),
    sampling_hz             numeric(10,2),
    range_min               numeric(15,6),
    range_max               numeric(15,6),
    alarm_low               numeric(15,6),
    alarm_high              numeric(15,6),
    status                  varchar(16),
    record_source           varchar(64),
    primary key (hk_sensor, load_dts)
);

create table if not exists predictive_maintenance_vault.s_failure_event_descriptive (
    hk_failure_event        varchar(32) references predictive_maintenance_vault.h_failure_event(hk_failure_event),
    load_dts                timestamp,
    failure_ts              timestamp,
    detected_by             varchar(16),
    downtime_minutes        integer,
    production_loss_units   bigint,
    root_cause              text,
    corrective_action       text,
    cost_usd                numeric(15,2),
    record_source           varchar(64),
    primary key (hk_failure_event, load_dts)
);

create table if not exists predictive_maintenance_vault.s_work_order_state (
    hk_work_order       varchar(32) references predictive_maintenance_vault.h_work_order(hk_work_order),
    load_dts            timestamp,
    wo_type             varchar(16),
    wo_priority         smallint,
    scheduled_start     timestamp,
    actual_start        timestamp,
    actual_end          timestamp,
    labor_hours         numeric(8,2),
    parts_cost_usd      numeric(15,2),
    labor_cost_usd      numeric(15,2),
    status              varchar(16),
    crew_id             varchar(64),
    record_source       varchar(64),
    primary key (hk_work_order, load_dts)
);

create table if not exists predictive_maintenance_vault.s_prediction_payload (
    hk_prediction               varchar(32) references predictive_maintenance_vault.h_prediction(hk_prediction),
    load_dts                    timestamp,
    prediction_ts               timestamp,
    prediction_type             varchar(16),
    anomaly_score               numeric(8,4),
    rul_hours                   integer,
    rul_confidence_lower        integer,
    rul_confidence_upper        integer,
    severity                    varchar(8),
    feature_snapshot_hash       varchar(64),
    record_source               varchar(64),
    primary key (hk_prediction, load_dts)
);

create table if not exists predictive_maintenance_vault.s_model_version_metrics (
    hk_model_version    varchar(32) references predictive_maintenance_vault.h_model_version(hk_model_version),
    load_dts            timestamp,
    algorithm           varchar(64),
    holdout_precision   numeric(5,4),
    holdout_recall      numeric(5,4),
    holdout_rul_mape    numeric(5,4),
    deployed_at         timestamp,
    deprecated_at       timestamp,
    champion            boolean,
    record_source       varchar(64),
    primary key (hk_model_version, load_dts)
);

create table if not exists predictive_maintenance_vault.s_failure_mode_descriptive (
    hk_failure_mode                 varchar(32) references predictive_maintenance_vault.h_failure_mode(hk_failure_mode),
    load_dts                        timestamp,
    fault_code                      varchar(16),
    description                     varchar(255),
    applicable_asset_class          varchar(64),
    characteristic_frequency_hz     numeric(10,2),
    typical_p_f_interval_hours      integer,
    severity_tier                   varchar(8),
    record_source                   varchar(64),
    primary key (hk_failure_mode, load_dts)
);
