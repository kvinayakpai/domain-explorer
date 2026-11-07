-- =============================================================================
-- Refinery Operations — Data Vault 2.0 schema
-- Hubs hold business keys (position, pump serial, lot, engineering change, tag);
-- links hold the relationships that change over time (installation, genealogy);
-- satellites are insert-only descriptive history. The installation link is what
-- keeps "which pump was in P-101A on 8 March" answerable after the pump moves.
-- =============================================================================

create schema if not exists refinery_operations_vault;

-- ---------- HUBS ----------
create table if not exists refinery_operations_vault.h_functional_location (
    hk_functional_location  varchar(32) primary key,      -- MD5(functional_location_id)
    functional_location_id  varchar(32) unique,
    load_dts                timestamp,
    record_source           varchar(32)                   -- SAP_PM
);

create table if not exists refinery_operations_vault.h_equipment (
    hk_equipment            varchar(32) primary key,      -- MD5(equipment_id)
    equipment_id            varchar(24) unique,           -- maker's serial
    load_dts                timestamp,
    record_source           varchar(32)
);

create table if not exists refinery_operations_vault.h_material_lot (
    hk_material_lot         varchar(32) primary key,
    lot_id                  varchar(16) unique,
    load_dts                timestamp,
    record_source           varchar(32)                   -- MAKER_ERP
);

create table if not exists refinery_operations_vault.h_engineering_change (
    hk_engineering_change   varchar(32) primary key,
    engineering_change_id   varchar(16) unique,
    load_dts                timestamp,
    record_source           varchar(32)                   -- MAKER_PLM
);

create table if not exists refinery_operations_vault.h_signal (
    hk_signal               varchar(32) primary key,
    signal_id               varchar(48) unique,
    load_dts                timestamp,
    record_source           varchar(32)                   -- PI
);

-- ---------- LINKS ----------
create table if not exists refinery_operations_vault.l_installation (
    hk_installation         varchar(32) primary key,      -- MD5(installation_id)
    hk_functional_location  varchar(32) references refinery_operations_vault.h_functional_location (hk_functional_location),
    hk_equipment            varchar(32) references refinery_operations_vault.h_equipment (hk_equipment),
    installation_id         varchar(16),
    load_dts                timestamp,
    record_source           varchar(32)
);

create table if not exists refinery_operations_vault.l_equipment_lot (
    hk_equipment_lot        varchar(32) primary key,      -- MD5(equipment_id || lot_id)
    hk_equipment            varchar(32) references refinery_operations_vault.h_equipment (hk_equipment),
    hk_material_lot         varchar(32) references refinery_operations_vault.h_material_lot (hk_material_lot),
    component_kind          varchar(24),
    load_dts                timestamp,
    record_source           varchar(32)                   -- MAKER_MES
);

create table if not exists refinery_operations_vault.l_lot_change (
    hk_lot_change           varchar(32) primary key,
    hk_material_lot         varchar(32) references refinery_operations_vault.h_material_lot (hk_material_lot),
    hk_engineering_change   varchar(32) references refinery_operations_vault.h_engineering_change (hk_engineering_change),
    load_dts                timestamp,
    record_source           varchar(32)
);

create table if not exists refinery_operations_vault.l_signal_location (
    hk_signal_location      varchar(32) primary key,
    hk_signal               varchar(32) references refinery_operations_vault.h_signal (hk_signal),
    hk_functional_location  varchar(32) references refinery_operations_vault.h_functional_location (hk_functional_location),
    load_dts                timestamp,
    record_source           varchar(32)
);

-- ---------- SATELLITES ----------
create table if not exists refinery_operations_vault.s_functional_location (
    hk_functional_location  varchar(32) references refinery_operations_vault.h_functional_location (hk_functional_location),
    load_dts                timestamp,
    hash_diff               varchar(32),
    floc_code               varchar(40),
    tag                     varchar(24),
    site_id                 varchar(16),
    service                 varchar(48),
    api_610_type            varchar(8),
    train_letter            char(1),
    rated_flow_m3h          decimal(8, 1),
    primary key (hk_functional_location, load_dts)
);

create table if not exists refinery_operations_vault.s_equipment (
    hk_equipment            varchar(32) references refinery_operations_vault.h_equipment (hk_equipment),
    load_dts                timestamp,
    hash_diff               varchar(32),
    model                   varchar(24),
    maker_id                varchar(24),
    built_on                date,
    shipped_on              date,
    primary key (hk_equipment, load_dts)
);

-- Effectivity of each installation (dates can be corrected later, so they live in a satellite).
create table if not exists refinery_operations_vault.s_installation_effectivity (
    hk_installation         varchar(32) references refinery_operations_vault.l_installation (hk_installation),
    load_dts                timestamp,
    installed_from          date,
    installed_to            date,
    primary key (hk_installation, load_dts)
);

-- Failures hang off the installation: the pump that failed, in the position where it failed.
create table if not exists refinery_operations_vault.s_installation_failure (
    hk_installation         varchar(32) references refinery_operations_vault.l_installation (hk_installation),
    failure_event_id        varchar(16),
    load_dts                timestamp,
    failed_on               date,
    iso14224_failure_mode   varchar(4),
    description             varchar(160),
    repair_days             integer,
    primary key (hk_installation, failure_event_id, load_dts)
);

create table if not exists refinery_operations_vault.s_engineering_change (
    hk_engineering_change   varchar(32) references refinery_operations_vault.h_engineering_change (hk_engineering_change),
    load_dts                timestamp,
    approval_route          varchar(12),
    qualification_waived    boolean,
    approved_on             date,
    status                  varchar(12),
    primary key (hk_engineering_change, load_dts)
);

create table if not exists refinery_operations_vault.s_signal_daily (
    hk_signal               varchar(32) references refinery_operations_vault.h_signal (hk_signal),
    day                     date,
    load_dts                timestamp,
    mean_value              decimal(12, 4),
    min_value               decimal(12, 4),
    max_value               decimal(12, 4),
    sample_count            integer,
    primary key (hk_signal, day, load_dts)
);
