-- =============================================================================
-- Upstream Production — Artificial Lift (ESP) — dimensional marts (Kimball)
-- Grain notes:
--   fct_esp_run         one row per string run in a well (censored flag kept)
--   fct_well_day        one row per well per day (allocated oil, producing flag)
--   kpi_esp_run_life    one row per cohort: Kaplan-Meier median run life
-- =============================================================================

create schema if not exists upstream_artificial_lift_dim;

create table if not exists upstream_artificial_lift_dim.dim_date (
    date_key                integer primary key,
    calendar_date           date unique,
    year                    smallint,
    month                   smallint
);

create table if not exists upstream_artificial_lift_dim.dim_well (
    well_key                varchar(8) primary key,       -- well_id
    field_id                varchar(16),
    pad                     varchar(8),
    lift_method             varchar(12),
    esp_setting_depth_m     decimal(8, 1)
);

create table if not exists upstream_artificial_lift_dim.dim_esp_string (
    esp_string_key          varchar(16) primary key,      -- esp_string_id
    model                   varchar(24),
    built_on                date,
    seal_component_id       varchar(16),
    seal_elastomer_lot      varchar(16)                   -- the E- lot in the seal section
);

create table if not exists upstream_artificial_lift_dim.fct_esp_run (
    run_id                  varchar(16) primary key,
    well_key                varchar(8) references upstream_artificial_lift_dim.dim_well (well_key),
    esp_string_key          varchar(16) references upstream_artificial_lift_dim.dim_esp_string (esp_string_key),
    run_start_key           integer references upstream_artificial_lift_dim.dim_date (date_key),
    run_end_key             integer references upstream_artificial_lift_dim.dim_date (date_key),
    run_days                integer,
    failed                  boolean,
    censored                boolean,
    cohort                  varchar(24)                   -- seal built since Aug 2025 | earlier builds
);

create table if not exists upstream_artificial_lift_dim.fct_well_day (
    well_key                varchar(8) references upstream_artificial_lift_dim.dim_well (well_key),
    date_key                integer references upstream_artificial_lift_dim.dim_date (date_key),
    oil_bbl_d               decimal(10, 2),
    producing               boolean,
    primary key (well_key, date_key)
);

create table if not exists upstream_artificial_lift_dim.kpi_esp_run_life (
    cohort                  varchar(24) primary key,
    strings                 integer,
    failed                  integer,
    running                 integer,
    km_median_run_days      integer                       -- null when the curve never falls to 0.5
);
