-- =============================================================================
-- Upstream Production — Artificial Lift (ESP) — Data Vault 2.0 schema
-- Hubs: well, ESP string, component, signal. The run link ties a string to a
-- well for a period; DIFA findings and failures are satellites on that link, so a
-- teardown always points at the string that failed in the well it failed in.
-- =============================================================================

create schema if not exists upstream_artificial_lift_vault;

create table if not exists upstream_artificial_lift_vault.h_well (
    hk_well                 varchar(32) primary key,      -- MD5(well_id)
    well_id                 varchar(8) unique,
    load_dts                timestamp,
    record_source           varchar(32)                   -- OSDU
);

create table if not exists upstream_artificial_lift_vault.h_esp_string (
    hk_esp_string           varchar(32) primary key,
    esp_string_id           varchar(16) unique,
    load_dts                timestamp,
    record_source           varchar(32)                   -- SAP_PM / ESP vendor
);

create table if not exists upstream_artificial_lift_vault.h_component (
    hk_component            varchar(32) primary key,
    component_id            varchar(16) unique,
    load_dts                timestamp,
    record_source           varchar(32)                   -- MAKER_MES
);

create table if not exists upstream_artificial_lift_vault.h_signal (
    hk_signal               varchar(32) primary key,
    signal_id               varchar(48) unique,
    load_dts                timestamp,
    record_source           varchar(32)                   -- SCADA
);

create table if not exists upstream_artificial_lift_vault.l_esp_run (
    hk_esp_run              varchar(32) primary key,      -- MD5(run_id)
    hk_well                 varchar(32) references upstream_artificial_lift_vault.h_well (hk_well),
    hk_esp_string           varchar(32) references upstream_artificial_lift_vault.h_esp_string (hk_esp_string),
    run_id                  varchar(16),
    load_dts                timestamp,
    record_source           varchar(32)
);

create table if not exists upstream_artificial_lift_vault.l_string_component (
    hk_string_component     varchar(32) primary key,
    hk_esp_string           varchar(32) references upstream_artificial_lift_vault.h_esp_string (hk_esp_string),
    hk_component            varchar(32) references upstream_artificial_lift_vault.h_component (hk_component),
    load_dts                timestamp,
    record_source           varchar(32)
);

create table if not exists upstream_artificial_lift_vault.s_well (
    hk_well                 varchar(32) references upstream_artificial_lift_vault.h_well (hk_well),
    load_dts                timestamp,
    hash_diff               varchar(32),
    field_id                varchar(16),
    pad                     varchar(8),
    lift_method             varchar(12),
    esp_setting_depth_m     decimal(8, 1),
    primary key (hk_well, load_dts)
);

create table if not exists upstream_artificial_lift_vault.s_esp_run_state (
    hk_esp_run              varchar(32) references upstream_artificial_lift_vault.l_esp_run (hk_esp_run),
    load_dts                timestamp,
    run_start               date,
    run_end                 date,
    run_state               varchar(8),
    censored                boolean,
    pull_reason             varchar(48),
    primary key (hk_esp_run, load_dts)
);

create table if not exists upstream_artificial_lift_vault.s_component_lots (
    hk_component            varchar(32) references upstream_artificial_lift_vault.h_component (hk_component),
    load_dts                timestamp,
    component_kind          varchar(12),
    material_lots           varchar(64),
    primary key (hk_component, load_dts)
);

create table if not exists upstream_artificial_lift_vault.s_difa_finding (
    hk_esp_string           varchar(32) references upstream_artificial_lift_vault.h_esp_string (hk_esp_string),
    difa_report_id          varchar(16),
    load_dts                timestamp,
    reported_on             date,
    standard                varchar(16),
    finding                 text,
    primary key (hk_esp_string, difa_report_id, load_dts)
);

create table if not exists upstream_artificial_lift_vault.s_signal_daily (
    hk_signal               varchar(32) references upstream_artificial_lift_vault.h_signal (hk_signal),
    day                     date,
    load_dts                timestamp,
    mean_value              decimal(12, 4),
    max_value               decimal(12, 4),
    primary key (hk_signal, day, load_dts)
);

create table if not exists upstream_artificial_lift_vault.s_well_production (
    hk_well                 varchar(32) references upstream_artificial_lift_vault.h_well (hk_well),
    day                     date,
    load_dts                timestamp,
    oil_bbl_d               decimal(10, 2),
    primary key (hk_well, day, load_dts)
);
