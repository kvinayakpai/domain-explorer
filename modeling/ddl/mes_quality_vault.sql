-- =============================================================================
-- MES & Quality — Data Vault 2.0 (excerpt)
-- Hubs / Links / Satellites for work order, equipment, sensor reads, NCs.
-- =============================================================================

create schema if not exists mes_quality_vault;

-- Hubs
create table if not exists mes_quality_vault.hub_plant (
    plant_hk             bytea primary key,
    plant_bk             varchar not null,
    load_dts             timestamp not null,
    rec_src              varchar not null
);

create table if not exists mes_quality_vault.hub_line (
    line_hk              bytea primary key,
    line_bk              varchar not null,
    load_dts             timestamp not null,
    rec_src              varchar not null
);

create table if not exists mes_quality_vault.hub_equipment (
    equipment_hk         bytea primary key,
    equipment_bk         varchar not null,
    load_dts             timestamp not null,
    rec_src              varchar not null
);

create table if not exists mes_quality_vault.hub_work_order (
    wo_hk                bytea primary key,
    wo_bk                varchar not null,
    load_dts             timestamp not null,
    rec_src              varchar not null
);

create table if not exists mes_quality_vault.hub_product (
    product_hk           bytea primary key,
    product_bk           varchar not null,
    load_dts             timestamp not null,
    rec_src              varchar not null
);

create table if not exists mes_quality_vault.hub_material_lot (
    lot_hk               bytea primary key,
    lot_bk               varchar not null,
    load_dts             timestamp not null,
    rec_src              varchar not null
);

-- Links
create table if not exists mes_quality_vault.link_wo_line (
    link_hk              bytea primary key,
    wo_hk                bytea not null references mes_quality_vault.hub_work_order(wo_hk),
    line_hk              bytea not null references mes_quality_vault.hub_line(line_hk),
    product_hk           bytea not null references mes_quality_vault.hub_product(product_hk),
    load_dts             timestamp not null,
    rec_src              varchar not null
);

create table if not exists mes_quality_vault.link_equipment_line (
    link_hk              bytea primary key,
    equipment_hk         bytea not null references mes_quality_vault.hub_equipment(equipment_hk),
    line_hk              bytea not null references mes_quality_vault.hub_line(line_hk),
    load_dts             timestamp not null,
    rec_src              varchar not null
);

create table if not exists mes_quality_vault.link_genealogy (
    link_hk              bytea primary key,
    parent_lot_hk        bytea not null references mes_quality_vault.hub_material_lot(lot_hk),
    child_lot_hk         bytea not null references mes_quality_vault.hub_material_lot(lot_hk),
    relationship_type    varchar(16) not null,
    load_dts             timestamp not null,
    rec_src              varchar not null
);

create table if not exists mes_quality_vault.link_nc (
    link_hk              bytea primary key,
    wo_hk                bytea not null references mes_quality_vault.hub_work_order(wo_hk),
    equipment_hk         bytea references mes_quality_vault.hub_equipment(equipment_hk),
    nc_bk                varchar not null,
    load_dts             timestamp not null,
    rec_src              varchar not null
);

-- Satellites
create table if not exists mes_quality_vault.sat_equipment_descriptive (
    equipment_hk         bytea not null references mes_quality_vault.hub_equipment(equipment_hk),
    load_dts             timestamp not null,
    load_end_dts         timestamp,
    hash_diff            bytea not null,
    equipment_name       varchar not null,
    serial_number        varchar(64),
    model                varchar(64),
    install_date         date,
    rec_src              varchar not null,
    primary key (equipment_hk, load_dts)
);

create table if not exists mes_quality_vault.sat_wo_state (
    wo_hk                bytea not null references mes_quality_vault.hub_work_order(wo_hk),
    load_dts             timestamp not null,
    load_end_dts         timestamp,
    hash_diff            bytea not null,
    status               varchar(16) not null,
    planned_qty          integer not null,
    actual_qty           integer,
    actual_start         timestamp,
    actual_end           timestamp,
    rec_src              varchar not null,
    primary key (wo_hk, load_dts)
);

create table if not exists mes_quality_vault.sat_sensor_reading (
    equipment_hk         bytea not null references mes_quality_vault.hub_equipment(equipment_hk),
    tag                  varchar not null,
    ts                   timestamp not null,
    load_dts             timestamp not null,
    hash_diff            bytea not null,
    value                numeric(14, 4) not null,
    quality_code         smallint not null,
    rec_src              varchar not null,
    primary key (equipment_hk, tag, ts, load_dts)
);

create table if not exists mes_quality_vault.sat_downtime_event (
    equipment_hk         bytea not null references mes_quality_vault.hub_equipment(equipment_hk),
    started_at           timestamp not null,
    load_dts             timestamp not null,
    hash_diff            bytea not null,
    ended_at             timestamp,
    reason_code          varchar(16) not null,
    is_planned           boolean not null,
    rec_src              varchar not null,
    primary key (equipment_hk, started_at, load_dts)
);

create table if not exists mes_quality_vault.sat_nc_descriptive (
    link_hk              bytea not null,
    load_dts             timestamp not null,
    load_end_dts         timestamp,
    hash_diff            bytea not null,
    nc_code              varchar(16) not null,
    severity             varchar(16) not null,
    quantity_affected    integer not null,
    disposition          varchar(16),
    rec_src              varchar not null,
    primary key (link_hk, load_dts)
);
