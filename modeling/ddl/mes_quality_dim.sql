-- =============================================================================
-- MES & Quality — dimensional mart (excerpt)
-- Star schema for OEE, FPY, scrap, MTBF/MTTR analytics.
-- =============================================================================

create schema if not exists mes_quality_dim;

create table if not exists mes_quality_dim.dim_date (
    date_key             integer primary key,
    date_actual          date not null,
    day_of_week          smallint not null,
    fiscal_period        varchar(8)
);

create table if not exists mes_quality_dim.dim_shift (
    shift_key            bigint primary key,
    shift_id             varchar not null,
    shift_name           varchar not null,
    plant_id             varchar not null,
    started_at           timestamp not null,
    ended_at             timestamp not null
);

create table if not exists mes_quality_dim.dim_plant (
    plant_key            smallint primary key,
    plant_id             varchar not null,
    plant_name           varchar not null,
    country_iso2         varchar(2) not null,
    region               varchar(16)
);

create table if not exists mes_quality_dim.dim_line (
    line_key             integer primary key,
    line_id              varchar not null,
    line_name            varchar not null,
    plant_key            smallint not null references mes_quality_dim.dim_plant(plant_key),
    nameplate_speed      numeric(10, 2)
);

create table if not exists mes_quality_dim.dim_equipment (
    equipment_key        bigint primary key,
    equipment_id         varchar not null,
    equipment_name       varchar not null,
    line_key             integer not null references mes_quality_dim.dim_line(line_key),
    serial_number        varchar(64),
    model                varchar(64),
    valid_from           timestamp not null,
    valid_to             timestamp,
    is_current           boolean not null
);

create table if not exists mes_quality_dim.dim_product (
    product_key          bigint primary key,
    product_id           varchar not null,
    product_name         varchar not null,
    revision             varchar(16) not null,
    valid_from           timestamp not null,
    valid_to             timestamp,
    is_current           boolean not null
);

create table if not exists mes_quality_dim.dim_downtime_reason (
    reason_key           smallint primary key,
    reason_code          varchar(16) not null,
    reason_name          varchar(64) not null,
    reason_category      varchar(32) not null,
    is_planned           boolean not null
);

create table if not exists mes_quality_dim.dim_nc_code (
    nc_key               smallint primary key,
    nc_code              varchar(16) not null,
    nc_name              varchar(64) not null,
    severity             varchar(16) not null
);

create table if not exists mes_quality_dim.fact_oee_hourly (
    date_key             integer not null references mes_quality_dim.dim_date(date_key),
    hour_of_day          smallint not null,
    line_key             integer not null references mes_quality_dim.dim_line(line_key),
    shift_key            bigint not null references mes_quality_dim.dim_shift(shift_key),
    product_key          bigint references mes_quality_dim.dim_product(product_key),
    runtime_secs         integer not null,
    downtime_secs        integer not null,
    units_produced       integer not null,
    units_good           integer not null,
    units_scrapped       integer not null,
    availability         numeric(5, 4),
    performance          numeric(5, 4),
    quality              numeric(5, 4),
    oee                  numeric(5, 4),
    primary key (date_key, hour_of_day, line_key, shift_key)
);

create table if not exists mes_quality_dim.fact_quality_check (
    date_key             integer not null references mes_quality_dim.dim_date(date_key),
    line_key             integer not null references mes_quality_dim.dim_line(line_key),
    product_key          bigint not null references mes_quality_dim.dim_product(product_key),
    nc_key               smallint references mes_quality_dim.dim_nc_code(nc_key),
    checks_total         integer not null,
    checks_passed        integer not null,
    cpk_avg              numeric(8, 4),
    primary key (date_key, line_key, product_key)
);

create table if not exists mes_quality_dim.fact_downtime (
    date_key             integer not null references mes_quality_dim.dim_date(date_key),
    line_key             integer not null references mes_quality_dim.dim_line(line_key),
    equipment_key        bigint references mes_quality_dim.dim_equipment(equipment_key),
    reason_key           smallint not null references mes_quality_dim.dim_downtime_reason(reason_key),
    event_count          integer not null,
    duration_secs        integer not null,
    primary key (date_key, line_key, reason_key)
);

create table if not exists mes_quality_dim.fact_equipment_reliability (
    date_key             integer not null references mes_quality_dim.dim_date(date_key),
    equipment_key        bigint not null references mes_quality_dim.dim_equipment(equipment_key),
    failure_count        integer not null,
    operational_hours    numeric(10, 2) not null,
    repair_hours         numeric(10, 2) not null,
    mtbf_hours           numeric(10, 2),
    mttr_hours           numeric(10, 2),
    primary key (date_key, equipment_key)
);
