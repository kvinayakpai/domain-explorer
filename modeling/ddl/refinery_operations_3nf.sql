-- =============================================================================
-- Refinery Operations (rotating-equipment reliability) — 3NF schema
-- Standards: ISO 14224:2016 (failure modes, equipment taxonomy), API 610 (pump
-- types), ISA-95 / IEC 62264 (functional location hierarchy), SAP PM object model
-- (functional location, equipment, installation history, notification, order).
-- Loaded from synthetic-data/refinery_operations (exported from the Factory to
-- Field world). Positions and physical units are separate tables joined by dated
-- installations. All data is synthetic.
-- =============================================================================

create schema if not exists refinery_operations;

create table if not exists refinery_operations.site (
    site_id                 varchar(16) primary key,      -- site:R1
    site_name               varchar(64) not null,
    operator_id             varchar(32),
    time_zone               varchar(32)
);

-- ISA-95 / SAP PM functional location: the position, which stays.
create table if not exists refinery_operations.functional_location (
    functional_location_id  varchar(32) primary key,      -- pos:R1:10-P-101A
    floc_code               varchar(40) unique,           -- CDU1-10-P-101A
    tag                     varchar(24) not null,         -- 10-P-101A
    site_id                 varchar(16) not null references refinery_operations.site (site_id),
    area                    varchar(8),
    process_unit            varchar(16),
    service                 varchar(48),
    api_610_type            varchar(8),                   -- OH2 | BB2 | ...
    model_required          varchar(24),
    rated_flow_m3h          decimal(8, 1),
    train_letter            char(1),                      -- A runs, B is the installed spare
    spare_of                varchar(32),
    pid_drawing             varchar(24),
    pid_revision            varchar(4)
);

-- The physical pump, identified by the maker's serial; it moves between positions.
create table if not exists refinery_operations.equipment (
    equipment_id            varchar(24) primary key,      -- OEM-25-1187
    equipment_kind          varchar(16) not null,
    model                   varchar(24),
    maker_id                varchar(24),
    customer_id             varchar(24),
    built_on                date,
    shipped_on              date
);

create table if not exists refinery_operations.installation (
    installation_id         varchar(16) primary key,
    functional_location_id  varchar(32) not null references refinery_operations.functional_location (functional_location_id),
    equipment_id            varchar(24) not null references refinery_operations.equipment (equipment_id),
    installed_from          date not null,
    installed_to            date                          -- null while installed
);

create table if not exists refinery_operations.failure_event (
    failure_event_id        varchar(16) primary key,
    functional_location_id  varchar(32) not null references refinery_operations.functional_location (functional_location_id),
    equipment_id            varchar(24) not null references refinery_operations.equipment (equipment_id),
    installation_id         varchar(16) references refinery_operations.installation (installation_id),
    failed_on               date not null,
    iso14224_failure_mode   varchar(4) not null,          -- VIB | ELP | FTS | ...
    description             varchar(160),
    repair_days             integer,
    unit_swapped            boolean
);

create table if not exists refinery_operations.notification (
    notification_id         varchar(16) primary key,
    notification_type       varchar(4),                   -- M1 request | M2 malfunction
    priority                smallint,
    status                  varchar(12),
    reported_on             date,
    functional_location_id  varchar(32) references refinery_operations.functional_location (functional_location_id),
    equipment_id            varchar(24) references refinery_operations.equipment (equipment_id),
    short_text              varchar(160),                 -- field free text: data, never instructions
    iso14224_failure_mode   varchar(4),
    failure_event_id        varchar(16) references refinery_operations.failure_event (failure_event_id)
);

create table if not exists refinery_operations.work_order (
    work_order_id           varchar(16) primary key,
    order_type              varchar(4),                   -- PM01 preventive | PM02 corrective | PM03 inspection
    notification_id         varchar(16) references refinery_operations.notification (notification_id),
    functional_location_id  varchar(32) references refinery_operations.functional_location (functional_location_id),
    equipment_id            varchar(24) references refinery_operations.equipment (equipment_id),
    basic_start             date,
    basic_finish            date,
    short_text              varchar(160)
);

create table if not exists refinery_operations.signal (
    signal_id               varchar(48) primary key,      -- sig:R1:10P101A.VIB_DE
    tag                     varchar(32) not null,
    site_id                 varchar(16) references refinery_operations.site (site_id),
    functional_location_id  varchar(32) references refinery_operations.functional_location (functional_location_id),
    quantity                varchar(24),                  -- vibration_de | bearing_temp | suction_pressure | ...
    eng_unit                varchar(12),
    alarm_high              decimal(10, 3),
    source_system           varchar(12),
    sample_seconds          integer,
    description             varchar(64)
);

create table if not exists refinery_operations.signal_daily (
    signal_id               varchar(48) not null references refinery_operations.signal (signal_id),
    day                     date not null,
    mean_value              decimal(12, 4),
    min_value               decimal(12, 4),
    max_value               decimal(12, 4),
    sample_count            integer,
    primary key (signal_id, day)
);

create table if not exists refinery_operations.engineering_change (
    engineering_change_id   varchar(16) primary key,
    title                   varchar(80),
    part                    varchar(32),
    approval_route          varchar(12),                  -- standard | expedited
    qualification_waived    boolean,
    approved_on             date,
    status                  varchar(12),
    supplier_from           varchar(24),
    supplier_to             varchar(24)
);

create table if not exists refinery_operations.material_lot (
    lot_id                  varchar(16) primary key,      -- B-24-117
    material                varchar(32),
    supplier_id             varchar(24),
    received_on             date,
    quantity                integer,
    engineering_change_id   varchar(16) references refinery_operations.engineering_change (engineering_change_id),
    purchase_order          varchar(20)
);

-- As-built genealogy from the maker's MES: which lots went into which serial.
create table if not exists refinery_operations.component_genealogy (
    equipment_id            varchar(24) not null references refinery_operations.equipment (equipment_id),
    component_kind          varchar(24) not null,         -- bearing set | mechanical seal | ...
    lot_id                  varchar(16) not null references refinery_operations.material_lot (lot_id),
    primary key (equipment_id, component_kind)
);
