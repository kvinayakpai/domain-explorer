-- =============================================================================
-- MES & Quality — 3NF schema (excerpt)
-- ISA-95 inspired plant model joining work orders, sensor reads, and quality.
-- =============================================================================

create schema if not exists mes_quality_3nf;

create table if not exists mes_quality_3nf.plant (
    plant_id             varchar primary key,
    plant_name           varchar not null,
    country_iso2         varchar(2) not null,
    timezone             varchar(64) not null
);

create table if not exists mes_quality_3nf.area (
    area_id              varchar primary key,
    plant_id             varchar not null references mes_quality_3nf.plant(plant_id),
    area_name            varchar not null
);

create table if not exists mes_quality_3nf.line (
    line_id              varchar primary key,
    area_id              varchar not null references mes_quality_3nf.area(area_id),
    line_name            varchar not null,
    nameplate_speed      numeric(10, 2),
    uom                  varchar(8)
);

create table if not exists mes_quality_3nf.work_cell (
    cell_id              varchar primary key,
    line_id              varchar not null references mes_quality_3nf.line(line_id),
    cell_name            varchar not null
);

create table if not exists mes_quality_3nf.equipment (
    equipment_id         varchar primary key,
    cell_id              varchar not null references mes_quality_3nf.work_cell(cell_id),
    equipment_name       varchar not null,
    serial_number        varchar(64),
    model                varchar(64),
    install_date         date
);

create table if not exists mes_quality_3nf.product (
    product_id           varchar primary key,
    product_name         varchar not null,
    revision             varchar(16) not null,
    bom_revision         varchar(16) not null
);

create table if not exists mes_quality_3nf.bom_item (
    bom_revision         varchar(16) not null,
    component_id         varchar not null,
    qty_per_assembly     numeric(12, 4) not null,
    primary key (bom_revision, component_id)
);

create table if not exists mes_quality_3nf.material_lot (
    lot_id               varchar primary key,
    material_id          varchar not null,
    supplier_id          varchar,
    received_at          timestamp not null,
    expiry_date          date,
    quantity             numeric(14, 4) not null,
    uom                  varchar(8) not null
);

create table if not exists mes_quality_3nf.work_order (
    wo_id                varchar primary key,
    product_id           varchar not null references mes_quality_3nf.product(product_id),
    plant_id             varchar not null references mes_quality_3nf.plant(plant_id),
    line_id              varchar references mes_quality_3nf.line(line_id),
    planned_qty          integer not null,
    actual_qty           integer,
    planned_start        timestamp not null,
    actual_start         timestamp,
    actual_end           timestamp,
    status               varchar(16) not null
);

create table if not exists mes_quality_3nf.operation (
    op_id                varchar primary key,
    wo_id                varchar not null references mes_quality_3nf.work_order(wo_id),
    cell_id              varchar not null references mes_quality_3nf.work_cell(cell_id),
    op_seq               smallint not null,
    op_name              varchar not null,
    setup_time_secs      integer,
    run_time_secs        integer
);

create table if not exists mes_quality_3nf.tag (
    tag                  varchar primary key,
    equipment_id         varchar not null references mes_quality_3nf.equipment(equipment_id),
    description          varchar,
    uom                  varchar(16),
    expected_min         numeric(14, 4),
    expected_max         numeric(14, 4)
);

create table if not exists mes_quality_3nf.sensor_reading (
    tag                  varchar not null references mes_quality_3nf.tag(tag),
    ts                   timestamp not null,
    value                numeric(14, 4) not null,
    quality_code         smallint not null,
    primary key (tag, ts)
);

create table if not exists mes_quality_3nf.downtime_event (
    event_id             varchar primary key,
    line_id              varchar not null references mes_quality_3nf.line(line_id),
    equipment_id         varchar references mes_quality_3nf.equipment(equipment_id),
    started_at           timestamp not null,
    ended_at             timestamp,
    reason_code          varchar(16) not null,
    is_planned           boolean not null
);

create table if not exists mes_quality_3nf.shift (
    shift_id             varchar primary key,
    plant_id             varchar not null references mes_quality_3nf.plant(plant_id),
    shift_name           varchar not null,
    started_at           timestamp not null,
    ended_at             timestamp not null,
    crew_lead_id         varchar
);

create table if not exists mes_quality_3nf.quality_check (
    check_id             varchar primary key,
    op_id                varchar not null references mes_quality_3nf.operation(op_id),
    check_type           varchar(16) not null,
    measure_value        numeric(14, 4),
    lower_spec           numeric(14, 4),
    upper_spec           numeric(14, 4),
    pass                 boolean not null,
    inspector_id         varchar,
    checked_at           timestamp not null
);

create table if not exists mes_quality_3nf.non_conformance (
    nc_id                varchar primary key,
    wo_id                varchar not null references mes_quality_3nf.work_order(wo_id),
    op_id                varchar references mes_quality_3nf.operation(op_id),
    nc_code              varchar(16) not null,
    description          varchar,
    quantity_affected    integer not null,
    detected_at          timestamp not null,
    disposition          varchar(16),
    closed_at            timestamp
);

create table if not exists mes_quality_3nf.scrap (
    scrap_id             varchar primary key,
    wo_id                varchar not null references mes_quality_3nf.work_order(wo_id),
    nc_id                varchar references mes_quality_3nf.non_conformance(nc_id),
    quantity             integer not null,
    scrap_reason         varchar(16) not null,
    scrapped_at          timestamp not null
);

create table if not exists mes_quality_3nf.genealogy (
    parent_serial        varchar not null,
    child_serial         varchar not null,
    relationship_type    varchar(16) not null,
    captured_at          timestamp not null,
    primary key (parent_serial, child_serial)
);

create table if not exists mes_quality_3nf.maintenance_event (
    me_id                varchar primary key,
    equipment_id         varchar not null references mes_quality_3nf.equipment(equipment_id),
    event_type           varchar(16) not null,
    started_at           timestamp not null,
    completed_at         timestamp,
    technician_id        varchar
);
