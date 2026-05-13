-- =============================================================================
-- S&OP / IBP — Kimball dimensional schema
-- Star marts:
--   fct_forecasts           (one row per item-location-customer-period-version)
--   fct_supply_plans        (one row per item-location-period-scenario)
--   fct_inventory_positions_sop  (one row per item-location-snapshot)
--   fct_forecast_accuracy   (forecast vs actual at item-location-period)
--   fct_capacity_load       (capacity vs planned load per resource-period)
-- Conformed dims (with _sop suffix where they collide with other anchors):
--   dim_date_sop, dim_item_sop, dim_location_sop, dim_customer_sop,
--   dim_scenario, dim_sop_cycle
-- =============================================================================

create schema if not exists sop_supply_chain_planning_dim;

-- ---------- DIMS ----------
create table if not exists sop_supply_chain_planning_dim.dim_date_sop (
    date_key       integer primary key,        -- yyyymmdd
    cal_date       date,
    day_of_week    smallint,
    day_name       varchar(12),
    iso_week       smallint,
    month          smallint,
    month_name     varchar(12),
    quarter        smallint,
    year           smallint,
    fiscal_period  varchar(8),
    is_weekend     boolean
);

create table if not exists sop_supply_chain_planning_dim.dim_item_sop (
    item_sk          bigint primary key,
    item_id          varchar(64) unique,
    gtin             varchar(14),
    sku              varchar(64),
    item_family      varchar(64),
    item_class       varchar(8),
    xyz_class        varchar(8),
    lifecycle_stage  varchar(16),
    uom_base         varchar(8),
    planning_uom     varchar(8),
    unit_cost        numeric(15,4),
    unit_price       numeric(15,4),
    shelf_life_days  integer,
    status           varchar(16),
    valid_from       timestamp,
    valid_to         timestamp,
    is_current       boolean
);

create table if not exists sop_supply_chain_planning_dim.dim_location_sop (
    location_sk     bigint primary key,
    location_id     varchar(64) unique,
    gln             varchar(13),
    location_type   varchar(16),
    country_iso2    varchar(2),
    region          varchar(32),
    tier            smallint,
    time_zone       varchar(32),
    status          varchar(16)
);

create table if not exists sop_supply_chain_planning_dim.dim_customer_sop (
    customer_sk     bigint primary key,
    customer_id     varchar(64) unique,
    customer_name   varchar(255),
    channel         varchar(32),
    segment         varchar(32),
    country_iso2    varchar(2),
    region          varchar(32),
    priority        smallint,
    status          varchar(16)
);

create table if not exists sop_supply_chain_planning_dim.dim_scenario (
    scenario_sk                bigint primary key,
    scenario_id                varchar(64) unique,
    cycle_id                   varchar(32),
    scenario_name              varchar(255),
    scenario_type              varchar(32),
    status                     varchar(16),
    revenue_impact_usd         numeric(18,2),
    working_capital_impact_usd numeric(18,2),
    service_level_impact_pct   numeric(5,2)
);

create table if not exists sop_supply_chain_planning_dim.dim_sop_cycle (
    cycle_sk                       bigint primary key,
    cycle_id                       varchar(32) unique,
    cycle_start                    date,
    cycle_end                      date,
    product_review_ts              timestamp,
    demand_review_ts               timestamp,
    supply_review_ts               timestamp,
    integrated_reconciliation_ts   timestamp,
    mbr_ts                         timestamp,
    signed_off_by                  varchar(128),
    signed_off_at                  timestamp,
    status                         varchar(16)
);

-- ---------- FACTS ----------
create table if not exists sop_supply_chain_planning_dim.fct_forecasts (
    forecast_id        bigint primary key,
    date_key           integer references sop_supply_chain_planning_dim.dim_date_sop(date_key),
    item_sk            bigint  references sop_supply_chain_planning_dim.dim_item_sop(item_sk),
    location_sk        bigint  references sop_supply_chain_planning_dim.dim_location_sop(location_sk),
    customer_sk        bigint  references sop_supply_chain_planning_dim.dim_customer_sop(customer_sk),
    cycle_sk           bigint  references sop_supply_chain_planning_dim.dim_sop_cycle(cycle_sk),
    forecast_version   varchar(32),
    period_grain       varchar(8),
    forecast_units     numeric(18,4),
    forecast_value_usd numeric(18,4),
    forecast_low       numeric(18,4),
    forecast_high      numeric(18,4),
    model_id           varchar(64),
    locked             boolean,
    published_at       timestamp
);

create table if not exists sop_supply_chain_planning_dim.fct_supply_plans (
    supply_plan_id     bigint primary key,
    date_key           integer references sop_supply_chain_planning_dim.dim_date_sop(date_key),
    item_sk            bigint  references sop_supply_chain_planning_dim.dim_item_sop(item_sk),
    location_sk        bigint  references sop_supply_chain_planning_dim.dim_location_sop(location_sk),
    source_location_id varchar(64),
    cycle_sk           bigint  references sop_supply_chain_planning_dim.dim_sop_cycle(cycle_sk),
    scenario_sk        bigint  references sop_supply_chain_planning_dim.dim_scenario(scenario_sk),
    supply_type        varchar(16),
    period_grain       varchar(8),
    planned_units      numeric(18,4),
    planned_value_usd  numeric(18,4),
    lead_time_days     smallint,
    status             varchar(16),
    published_at       timestamp
);

create table if not exists sop_supply_chain_planning_dim.fct_inventory_positions_sop (
    inventory_position_id  bigint primary key,
    date_key               integer references sop_supply_chain_planning_dim.dim_date_sop(date_key),
    item_sk                bigint  references sop_supply_chain_planning_dim.dim_item_sop(item_sk),
    location_sk            bigint  references sop_supply_chain_planning_dim.dim_location_sop(location_sk),
    on_hand_units          numeric(18,4),
    on_order_units         numeric(18,4),
    in_transit_units       numeric(18,4),
    allocated_units        numeric(18,4),
    safety_stock_units     numeric(18,4),
    reorder_point_units    numeric(18,4),
    inventory_value_usd    numeric(18,4),
    doh_days               numeric(8,2),
    excess_units           numeric(18,4),
    stockout_flag          boolean,
    snapshot_ts            timestamp
);

create table if not exists sop_supply_chain_planning_dim.fct_forecast_accuracy (
    accuracy_id        bigint primary key,
    date_key           integer references sop_supply_chain_planning_dim.dim_date_sop(date_key),
    item_sk            bigint  references sop_supply_chain_planning_dim.dim_item_sop(item_sk),
    location_sk        bigint  references sop_supply_chain_planning_dim.dim_location_sop(location_sk),
    customer_sk        bigint  references sop_supply_chain_planning_dim.dim_customer_sop(customer_sk),
    cycle_sk           bigint  references sop_supply_chain_planning_dim.dim_sop_cycle(cycle_sk),
    forecast_version   varchar(32),
    period_grain       varchar(8),
    forecast_units     numeric(18,4),
    actual_units       numeric(18,4),
    abs_error_units    numeric(18,4),
    pct_error          numeric(10,4),
    bias_units         numeric(18,4),
    lag_days           integer,                          -- days between forecast publish and actual arrival
    mape_lag1          numeric(8,4),
    wape_lag1          numeric(8,4)
);

create table if not exists sop_supply_chain_planning_dim.fct_capacity_load (
    capacity_load_id   bigint primary key,
    date_key           integer references sop_supply_chain_planning_dim.dim_date_sop(date_key),
    location_sk        bigint  references sop_supply_chain_planning_dim.dim_location_sop(location_sk),
    resource_id        varchar(64),
    resource_type      varchar(16),
    available_hours    numeric(12,2),
    planned_load_hours numeric(12,2),
    utilization_pct    numeric(5,2),
    changeover_hours   numeric(8,2),
    is_constrained     boolean,
    status             varchar(16)
);

-- Helpful indexes.
create index if not exists ix_fct_fcst_item     on sop_supply_chain_planning_dim.fct_forecasts(item_sk);
create index if not exists ix_fct_fcst_cycle   on sop_supply_chain_planning_dim.fct_forecasts(cycle_sk);
create index if not exists ix_fct_supply_item  on sop_supply_chain_planning_dim.fct_supply_plans(item_sk);
create index if not exists ix_fct_supply_scen  on sop_supply_chain_planning_dim.fct_supply_plans(scenario_sk);
create index if not exists ix_fct_invpos_item  on sop_supply_chain_planning_dim.fct_inventory_positions_sop(item_sk);
create index if not exists ix_fct_acc_item     on sop_supply_chain_planning_dim.fct_forecast_accuracy(item_sk);
create index if not exists ix_fct_cap_loc      on sop_supply_chain_planning_dim.fct_capacity_load(location_sk);
