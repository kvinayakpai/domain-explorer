-- =============================================================================
-- S&OP / IBP — Data Vault 2.0 schema
-- Hubs (business keys) + Links (relationships) + Satellites (descriptive,
-- insert-only, time-stamped). Mirrors the IBP source contract.
-- =============================================================================

create schema if not exists sop_supply_chain_planning_vault;

-- ---------- HUBS ----------
create table if not exists sop_supply_chain_planning_vault.h_item (
    hk_item        varchar(32) primary key,        -- MD5(item_id)
    item_id        varchar(64) unique,
    load_dts       timestamp,
    record_source  varchar(64)
);

create table if not exists sop_supply_chain_planning_vault.h_location (
    hk_location    varchar(32) primary key,
    location_id    varchar(64) unique,
    load_dts       timestamp,
    record_source  varchar(64)
);

create table if not exists sop_supply_chain_planning_vault.h_customer (
    hk_customer    varchar(32) primary key,
    customer_id    varchar(64) unique,
    load_dts       timestamp,
    record_source  varchar(64)
);

create table if not exists sop_supply_chain_planning_vault.h_cycle (
    hk_cycle       varchar(32) primary key,
    cycle_id       varchar(32) unique,
    load_dts       timestamp,
    record_source  varchar(64)
);

create table if not exists sop_supply_chain_planning_vault.h_scenario (
    hk_scenario    varchar(32) primary key,
    scenario_id    varchar(64) unique,
    load_dts       timestamp,
    record_source  varchar(64)
);

-- ---------- LINKS ----------
create table if not exists sop_supply_chain_planning_vault.l_forecast (
    hk_link        varchar(32) primary key,
    hk_item        varchar(32) references sop_supply_chain_planning_vault.h_item(hk_item),
    hk_location    varchar(32) references sop_supply_chain_planning_vault.h_location(hk_location),
    hk_customer    varchar(32) references sop_supply_chain_planning_vault.h_customer(hk_customer),
    hk_cycle       varchar(32) references sop_supply_chain_planning_vault.h_cycle(hk_cycle),
    forecast_version varchar(32),
    period_start   date,
    load_dts       timestamp,
    record_source  varchar(64)
);

create table if not exists sop_supply_chain_planning_vault.l_supply_plan (
    hk_link        varchar(32) primary key,
    hk_item        varchar(32) references sop_supply_chain_planning_vault.h_item(hk_item),
    hk_location    varchar(32) references sop_supply_chain_planning_vault.h_location(hk_location),
    hk_cycle       varchar(32) references sop_supply_chain_planning_vault.h_cycle(hk_cycle),
    hk_scenario    varchar(32) references sop_supply_chain_planning_vault.h_scenario(hk_scenario),
    period_start   date,
    load_dts       timestamp,
    record_source  varchar(64)
);

create table if not exists sop_supply_chain_planning_vault.l_inventory_position (
    hk_link        varchar(32) primary key,
    hk_item        varchar(32) references sop_supply_chain_planning_vault.h_item(hk_item),
    hk_location    varchar(32) references sop_supply_chain_planning_vault.h_location(hk_location),
    snapshot_ts    timestamp,
    load_dts       timestamp,
    record_source  varchar(64)
);

create table if not exists sop_supply_chain_planning_vault.l_capacity (
    hk_link        varchar(32) primary key,
    hk_location    varchar(32) references sop_supply_chain_planning_vault.h_location(hk_location),
    resource_id    varchar(64),
    period_start   date,
    load_dts       timestamp,
    record_source  varchar(64)
);

create table if not exists sop_supply_chain_planning_vault.l_bom (
    hk_link             varchar(32) primary key,
    hk_parent_item      varchar(32) references sop_supply_chain_planning_vault.h_item(hk_item),
    hk_component_item   varchar(32) references sop_supply_chain_planning_vault.h_item(hk_item),
    hk_location         varchar(32) references sop_supply_chain_planning_vault.h_location(hk_location),
    bom_version         varchar(16),
    load_dts            timestamp,
    record_source       varchar(64)
);

-- ---------- SATELLITES ----------
create table if not exists sop_supply_chain_planning_vault.s_item_descriptive (
    hk_item         varchar(32) references sop_supply_chain_planning_vault.h_item(hk_item),
    load_dts        timestamp,
    gtin            varchar(14),
    sku             varchar(64),
    item_family     varchar(64),
    item_class      varchar(8),
    xyz_class       varchar(8),
    lifecycle_stage varchar(16),
    uom_base        varchar(8),
    planning_uom    varchar(8),
    unit_cost       numeric(15,4),
    unit_price      numeric(15,4),
    shelf_life_days integer,
    status          varchar(16),
    record_source   varchar(64),
    primary key (hk_item, load_dts)
);

create table if not exists sop_supply_chain_planning_vault.s_location_descriptive (
    hk_location    varchar(32) references sop_supply_chain_planning_vault.h_location(hk_location),
    load_dts       timestamp,
    gln            varchar(13),
    location_type  varchar(16),
    country_iso2   varchar(2),
    region         varchar(32),
    tier           smallint,
    time_zone      varchar(32),
    status         varchar(16),
    record_source  varchar(64),
    primary key (hk_location, load_dts)
);

create table if not exists sop_supply_chain_planning_vault.s_customer_descriptive (
    hk_customer    varchar(32) references sop_supply_chain_planning_vault.h_customer(hk_customer),
    load_dts       timestamp,
    customer_name  varchar(255),
    channel        varchar(32),
    segment        varchar(32),
    country_iso2   varchar(2),
    region         varchar(32),
    priority       smallint,
    status         varchar(16),
    record_source  varchar(64),
    primary key (hk_customer, load_dts)
);

create table if not exists sop_supply_chain_planning_vault.s_cycle_state (
    hk_cycle                       varchar(32) references sop_supply_chain_planning_vault.h_cycle(hk_cycle),
    load_dts                       timestamp,
    cycle_start                    date,
    cycle_end                      date,
    product_review_ts              timestamp,
    demand_review_ts               timestamp,
    supply_review_ts               timestamp,
    integrated_reconciliation_ts   timestamp,
    mbr_ts                         timestamp,
    signed_off_by                  varchar(128),
    signed_off_at                  timestamp,
    status                         varchar(16),
    record_source                  varchar(64),
    primary key (hk_cycle, load_dts)
);

create table if not exists sop_supply_chain_planning_vault.s_scenario_descriptive (
    hk_scenario                varchar(32) references sop_supply_chain_planning_vault.h_scenario(hk_scenario),
    load_dts                   timestamp,
    scenario_name              varchar(255),
    scenario_type              varchar(32),
    description                text,
    created_by                 varchar(64),
    status                     varchar(16),
    revenue_impact_usd         numeric(18,2),
    working_capital_impact_usd numeric(18,2),
    service_level_impact_pct   numeric(5,2),
    record_source              varchar(64),
    primary key (hk_scenario, load_dts)
);

create table if not exists sop_supply_chain_planning_vault.s_forecast_value (
    hk_link          varchar(32) references sop_supply_chain_planning_vault.l_forecast(hk_link),
    load_dts         timestamp,
    forecast_units   numeric(18,4),
    forecast_value   numeric(18,4),
    forecast_low     numeric(18,4),
    forecast_high    numeric(18,4),
    model_id         varchar(64),
    locked           boolean,
    record_source    varchar(64),
    primary key (hk_link, load_dts)
);

create table if not exists sop_supply_chain_planning_vault.s_supply_plan_value (
    hk_link             varchar(32) references sop_supply_chain_planning_vault.l_supply_plan(hk_link),
    load_dts            timestamp,
    supply_type         varchar(16),
    source_location_id  varchar(64),
    planned_units       numeric(18,4),
    planned_value       numeric(18,4),
    lead_time_days      smallint,
    status              varchar(16),
    record_source       varchar(64),
    primary key (hk_link, load_dts)
);

create table if not exists sop_supply_chain_planning_vault.s_inventory_position (
    hk_link             varchar(32) references sop_supply_chain_planning_vault.l_inventory_position(hk_link),
    load_dts            timestamp,
    on_hand_units       numeric(18,4),
    on_order_units      numeric(18,4),
    in_transit_units    numeric(18,4),
    allocated_units     numeric(18,4),
    safety_stock_units  numeric(18,4),
    reorder_point_units numeric(18,4),
    inventory_value     numeric(18,4),
    doh_days            numeric(8,2),
    excess_units        numeric(18,4),
    stockout_flag       boolean,
    record_source       varchar(64),
    primary key (hk_link, load_dts)
);

create table if not exists sop_supply_chain_planning_vault.s_capacity_state (
    hk_link             varchar(32) references sop_supply_chain_planning_vault.l_capacity(hk_link),
    load_dts            timestamp,
    resource_type       varchar(16),
    available_hours     numeric(12,2),
    planned_load_hours  numeric(12,2),
    utilization_pct     numeric(5,2),
    changeover_hours    numeric(8,2),
    status              varchar(16),
    record_source       varchar(64),
    primary key (hk_link, load_dts)
);

create table if not exists sop_supply_chain_planning_vault.s_bom_descriptive (
    hk_link        varchar(32) references sop_supply_chain_planning_vault.l_bom(hk_link),
    load_dts       timestamp,
    quantity_per   numeric(15,6),
    yield_pct      numeric(5,2),
    effective_from date,
    effective_to   date,
    record_source  varchar(64),
    primary key (hk_link, load_dts)
);
