-- =============================================================================
-- Refinery Operations — dimensional marts (Kimball)
-- Grain notes:
--   fct_installation  one row per pump installed in a position for a period
--   fct_failure       one row per functional failure (ISO 14224 mode)
--   fct_signal_day    one row per historian tag per day
-- dim_equipment carries the bearing lot and whether its engineering change
-- waived the qualification test, so lot-level reliability is one join away.
-- =============================================================================

create schema if not exists refinery_operations_dim;

create table if not exists refinery_operations_dim.dim_date (
    date_key                integer primary key,          -- yyyymmdd
    calendar_date           date unique,
    year                    smallint,
    month                   smallint,
    iso_week                smallint
);

create table if not exists refinery_operations_dim.dim_functional_location (
    functional_location_key varchar(32) primary key,      -- functional_location_id
    floc_code               varchar(40),
    tag                     varchar(24),
    site_id                 varchar(16),
    site_name               varchar(64),
    process_unit            varchar(16),
    service                 varchar(48),
    api_610_type            varchar(8),
    train_letter            char(1),
    is_installed_spare      boolean
);

create table if not exists refinery_operations_dim.dim_equipment (
    equipment_key           varchar(24) primary key,      -- maker's serial
    model                   varchar(24),
    built_on                date,
    bearing_lot_id          varchar(16),
    bearing_lot_change_id   varchar(16),
    bearing_lot_waived      boolean,                      -- qualification test waived on the lot's change
    seal_lot_id             varchar(16)
);

create table if not exists refinery_operations_dim.fct_installation (
    installation_id         varchar(16) primary key,
    functional_location_key varchar(32) references refinery_operations_dim.dim_functional_location (functional_location_key),
    equipment_key           varchar(24) references refinery_operations_dim.dim_equipment (equipment_key),
    installed_from_key      integer references refinery_operations_dim.dim_date (date_key),
    installed_to_key        integer references refinery_operations_dim.dim_date (date_key),
    installed_days          integer,                      -- to the as-of date while still installed
    failure_count           integer
);

create table if not exists refinery_operations_dim.fct_failure (
    failure_event_id        varchar(16) primary key,
    functional_location_key varchar(32) references refinery_operations_dim.dim_functional_location (functional_location_key),
    equipment_key           varchar(24) references refinery_operations_dim.dim_equipment (equipment_key),
    failed_on_key           integer references refinery_operations_dim.dim_date (date_key),
    iso14224_failure_mode   varchar(4),
    repair_days             integer,
    days_since_install      integer
);

create table if not exists refinery_operations_dim.fct_signal_day (
    signal_id               varchar(48),
    functional_location_key varchar(32) references refinery_operations_dim.dim_functional_location (functional_location_key),
    date_key                integer references refinery_operations_dim.dim_date (date_key),
    quantity                varchar(24),
    mean_value              decimal(12, 4),
    max_value               decimal(12, 4),
    alarm_high              decimal(10, 3),
    above_alarm             boolean,
    primary key (signal_id, date_key)
);
