-- =============================================================================
-- Predictive Maintenance — 3NF schema
-- Source standards (verbatim where the spec names a field):
--   ISO 13374 — Condition monitoring; six-block model (DA, DM, SD, HA, PA, AG)
--   ISO 14224 — Reliability and maintenance data; failure mode taxonomy
--   ISA-95 — Equipment hierarchy (Site/Area/Line/Work-Center/Equipment)
--   OPC UA (IEC 62541) — quality_code = OPC UA StatusCode
--   MIMOSA OSA-CBM — entity contract for condition-based maintenance
-- Vendors reflected in tag conventions and source IDs:
--   PTC ThingWorx, Siemens MindSphere/Senseye, GE Digital APM, Aveva PI,
--   IBM Maximo APM, Honeywell Forge, AspenTech Mtell, Augury, Uptake,
--   SparkCognition, SKF @ptitude, Emerson AMS.
-- =============================================================================

create schema if not exists predictive_maintenance;

-- ISA-95 Equipment Hierarchy: a physical asset.
create table if not exists predictive_maintenance.asset (
    asset_id            varchar(64) primary key,
    tag_id              varchar(128) unique,             -- Site.Area.Line.Pump-101
    asset_class         varchar(64),                     -- pump|motor|compressor|...
    manufacturer        varchar(128),                    -- SKF|Siemens|ABB|Emerson|...
    model_number        varchar(128),
    serial_number       varchar(128),
    site_id             varchar(64),                     -- ISA-95 Site
    area_id             varchar(64),                     -- ISA-95 Area
    line_id             varchar(64),                     -- ISA-95 Line / Work Center
    criticality         varchar(8),                      -- A|B|C per RCM (SAE JA1011)
    install_date        date,
    design_life_hours   integer,
    rated_kw            numeric(10,2),
    status              varchar(16)                       -- running|stopped|standby|maintenance|decommissioned
);

-- Sensor / channel attached to an asset.
create table if not exists predictive_maintenance.sensor (
    sensor_id            varchar(64) primary key,
    asset_id             varchar(64) references predictive_maintenance.asset(asset_id),
    sensor_type          varchar(32),                    -- vibration_accel|temp_rtd|pressure|...
    measurement_location varchar(64),                    -- DE bearing|NDE bearing|casing axial|...
    unit                 varchar(16),                    -- g|mm/s|degC|bar|...
    sampling_hz          numeric(10,2),
    range_min            numeric(15,6),
    range_max            numeric(15,6),
    alarm_low            numeric(15,6),                  -- ISO 10816 vibration severity zones
    alarm_high           numeric(15,6),
    install_date         date,
    status               varchar(16)                      -- active|drifted|failed|removed
);

-- High-cardinality time-series fact at minute or sub-minute grain.
create table if not exists predictive_maintenance.sensor_reading (
    reading_id      bigint primary key,
    sensor_id       varchar(64) references predictive_maintenance.sensor(sensor_id),
    asset_id        varchar(64) references predictive_maintenance.asset(asset_id),
    reading_ts      timestamp,
    value           numeric(15,6),
    quality_code    smallint,                            -- OPC-UA StatusCode (192=Good)
    is_anomaly      boolean,
    ingestion_ts    timestamp
);

-- Catalogued failure mode per ISO 14224 Annex B.
create table if not exists predictive_maintenance.failure_mode (
    failure_mode_id              varchar(32) primary key,
    fault_code                   varchar(16),            -- ISO 14224: BRD|GBR|VIB|OVH|...
    description                  varchar(255),
    applicable_asset_class       varchar(64),
    characteristic_frequency_hz  numeric(10,2),          -- BPFO/BPFI/BSF/FTF or gear mesh
    typical_p_f_interval_hours   integer,                -- RCM P-F curve
    severity_tier                varchar(8)              -- S1|S2|S3 — IEC 61508-aligned
);

-- Observed equipment failure — the label class for supervised models.
create table if not exists predictive_maintenance.failure_event (
    failure_event_id        varchar(64) primary key,
    asset_id                varchar(64) references predictive_maintenance.asset(asset_id),
    failure_mode_id         varchar(32) references predictive_maintenance.failure_mode(failure_mode_id),
    failure_ts              timestamp,
    detected_by             varchar(16),                 -- model_alert|operator|inspection|protective_trip|catastrophic
    downtime_minutes        integer,
    production_loss_units   bigint,
    root_cause              text,
    corrective_action       text,
    cost_usd                numeric(15,2)
);

-- Trained PdM model artifact reference.
create table if not exists predictive_maintenance.model_version (
    model_version_id      varchar(64) primary key,
    model_id              varchar(64),
    algorithm             varchar(64),                   -- autoencoder|isolation_forest|xgboost|lstm|transformer
    trained_on_from_ts    timestamp,
    trained_on_to_ts      timestamp,
    holdout_precision     numeric(5,4),
    holdout_recall        numeric(5,4),
    holdout_rul_mape      numeric(5,4),
    deployed_at           timestamp,
    deprecated_at         timestamp,
    champion              boolean
);

-- One PdM model output at a point in time.
create table if not exists predictive_maintenance.prediction (
    prediction_id              varchar(64) primary key,
    asset_id                   varchar(64) references predictive_maintenance.asset(asset_id),
    model_id                   varchar(64),
    model_version              varchar(32),
    prediction_ts              timestamp,
    prediction_type            varchar(16),              -- anomaly_score|rul|fault_class|health_index
    anomaly_score              numeric(8,4),
    rul_hours                  integer,
    rul_confidence_lower       integer,
    rul_confidence_upper       integer,
    predicted_failure_mode_id  varchar(32) references predictive_maintenance.failure_mode(failure_mode_id),
    severity                   varchar(8),               -- info|warning|alarm|critical
    feature_snapshot_hash      varchar(64)
);

-- CMMS-issued maintenance order — preventive / corrective / predictive.
create table if not exists predictive_maintenance.work_order (
    work_order_id                  varchar(64) primary key,
    asset_id                       varchar(64) references predictive_maintenance.asset(asset_id),
    wo_type                        varchar(16),          -- preventive|corrective|predictive|inspection|emergency
    wo_priority                    smallint,             -- 1..5
    triggered_by_prediction_id     varchar(64) references predictive_maintenance.prediction(prediction_id),
    scheduled_start                timestamp,
    actual_start                   timestamp,
    actual_end                     timestamp,
    labor_hours                    numeric(8,2),
    parts_cost_usd                 numeric(15,2),
    labor_cost_usd                 numeric(15,2),
    status                         varchar(16),          -- open|in_progress|completed|cancelled|rejected
    failure_event_id               varchar(64) references predictive_maintenance.failure_event(failure_event_id),
    crew_id                        varchar(64)
);

-- Plan rules driving when work orders are auto-generated.
create table if not exists predictive_maintenance.maintenance_plan (
    plan_id              varchar(64) primary key,
    asset_id             varchar(64) references predictive_maintenance.asset(asset_id),
    plan_type            varchar(16),                    -- calendar|runtime|condition|predictive
    interval_value       integer,
    interval_unit        varchar(16),                    -- days|operating_hours|cycles
    trigger_condition    text,                           -- JSON expression
    job_plan_template    varchar(64),
    active               boolean,
    created_at           timestamp
);

-- Helpful indexes on time and cardinality.
create index if not exists ix_reading_sensor    on predictive_maintenance.sensor_reading(sensor_id, reading_ts);
create index if not exists ix_reading_asset     on predictive_maintenance.sensor_reading(asset_id, reading_ts);
create index if not exists ix_failure_asset     on predictive_maintenance.failure_event(asset_id, failure_ts);
create index if not exists ix_wo_asset          on predictive_maintenance.work_order(asset_id, scheduled_start);
create index if not exists ix_prediction_asset  on predictive_maintenance.prediction(asset_id, prediction_ts);
create index if not exists ix_sensor_asset      on predictive_maintenance.sensor(asset_id);
