-- =============================================================================
-- Upstream Production — Artificial Lift (ESP) — 3NF schema
-- Standards: API RP 11S1 (ESP teardown / DIFA), API RP 11S (ESP operation),
-- ISO 14224:2016 (failure modes), OSDU well master data.
-- Loaded from synthetic-data/upstream_artificial_lift (exported from the Factory
-- to Field world). Run life belongs to the ESP string; the well keeps its history
-- while strings are installed and pulled. All data is synthetic.
-- =============================================================================

create schema if not exists upstream_artificial_lift;

create table if not exists upstream_artificial_lift.well (
    well_id                 varchar(8) primary key,       -- A-07
    functional_location_id  varchar(32) unique,
    floc_code               varchar(24),
    field_id                varchar(16) not null,
    pad                     varchar(8),
    lift_method             varchar(12) not null,         -- esp | gas_lift
    esp_position_id         varchar(32),
    esp_setting_depth_m     decimal(8, 1)
);

create table if not exists upstream_artificial_lift.esp_string (
    esp_string_id           varchar(16) primary key,      -- ES-25-0233
    model                   varchar(24),
    maker_id                varchar(24),
    built_on                date,
    shipped_on              date
);

create table if not exists upstream_artificial_lift.esp_component (
    component_id            varchar(16) primary key,      -- SS-25-0811
    esp_string_id           varchar(16) not null references upstream_artificial_lift.esp_string (esp_string_id),
    component_kind          varchar(12) not null,         -- pump | intake | seal | motor | cable
    built_on                date,
    material_lots           varchar(64)                   -- e.g. E-25-031;S-25-044
);

-- One string's time in one well. Running strings are censored observations.
create table if not exists upstream_artificial_lift.esp_run (
    run_id                  varchar(16) primary key,
    well_id                 varchar(8) not null references upstream_artificial_lift.well (well_id),
    esp_string_id           varchar(16) not null references upstream_artificial_lift.esp_string (esp_string_id),
    run_start               date not null,
    run_end                 date,
    run_days                integer not null,
    run_state               varchar(8) not null,          -- running | failed
    censored                boolean not null,
    pull_reason             varchar(48),
    seal_built_since_aug_2025 boolean
);

create table if not exists upstream_artificial_lift.failure_event (
    failure_event_id        varchar(16) primary key,
    functional_location_id  varchar(32),
    esp_string_id           varchar(16) references upstream_artificial_lift.esp_string (esp_string_id),
    failed_on               date not null,
    iso14224_failure_mode   varchar(4),
    description             varchar(160),
    repair_days             integer
);

create table if not exists upstream_artificial_lift.difa_report (
    difa_report_id          varchar(16) primary key,
    well_id                 varchar(8) references upstream_artificial_lift.well (well_id),
    esp_string_id           varchar(16) references upstream_artificial_lift.esp_string (esp_string_id),
    reported_on             date,
    standard                varchar(16),                  -- API RP 11S1
    finding                 text
);

create table if not exists upstream_artificial_lift.signal (
    signal_id               varchar(48) primary key,
    tag                     varchar(32) not null,
    functional_location_id  varchar(32),
    quantity                varchar(24),                  -- motor_temperature | intake_pressure | ...
    eng_unit                varchar(12),
    alarm_high              decimal(10, 3),
    source_system           varchar(12),
    sample_seconds          integer,
    description             varchar(64)
);

create table if not exists upstream_artificial_lift.signal_daily (
    signal_id               varchar(48) not null references upstream_artificial_lift.signal (signal_id),
    day                     date not null,
    mean_value              decimal(12, 4),
    min_value               decimal(12, 4),
    max_value               decimal(12, 4),
    sample_count            integer,
    primary key (signal_id, day)
);

create table if not exists upstream_artificial_lift.production_daily (
    well_id                 varchar(8) not null references upstream_artificial_lift.well (well_id),
    day                     date not null,
    oil_bbl_d               decimal(10, 2),               -- allocated, not metered
    primary key (well_id, day)
);

create table if not exists upstream_artificial_lift.workover_rig (
    rig_id                  varchar(8) primary key,
    field_id                varchar(16),
    free_from               date,
    note                    varchar(80)
);
