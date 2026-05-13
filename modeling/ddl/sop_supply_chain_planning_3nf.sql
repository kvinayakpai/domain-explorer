-- =============================================================================
-- S&OP / Integrated Business Planning — 3NF schema
-- Source standards (verbatim where the spec names a field):
--   ASCM/APICS SCOR Digital Standard — Plan / Source / Make / Deliver / Return / Enable
--     metric tree (Perfect Order, Cash-to-Cash, Forecast Accuracy, etc.).
--   ASCM IBP / Oliver Wight five-step S&OP — Product Review / Demand Review /
--     Supply Review / Integrated Reconciliation / MBR.
--   GS1 GTIN-14 (item.gtin) and GLN (location.gln).
--   SAP IBP / Kinaxis / o9 / Blue Yonder / Oracle SCP / Anaplan / Logility /
--     ToolsGroup / Demand Solutions / John Galt / GAINSystems — vendor field
--     conventions (forecast_version, scenario_id, cycle_id, lot_sizing).
--   X12 EDI 852 / 830 / 862 for trading-partner planning collaboration.
-- =============================================================================

create schema if not exists sop_supply_chain_planning;

-- Planning item. GS1 GTIN where assigned.
create table if not exists sop_supply_chain_planning.item (
    item_id            varchar(64) primary key,
    gtin               varchar(14),                       -- GS1 Global Trade Item Number
    sku                varchar(64),
    item_family        varchar(64),
    item_class         varchar(8),                        -- ABC class
    xyz_class          varchar(8),                        -- XYZ variability class
    lifecycle_stage    varchar(16),                       -- intro|growth|mature|decline|eol
    uom_base           varchar(8),
    planning_uom       varchar(8),
    unit_cost          numeric(15,4),
    unit_price         numeric(15,4),
    shelf_life_days    integer,
    created_at         timestamp,
    status             varchar(16)
);

-- Planning location. GS1 GLN where assigned.
create table if not exists sop_supply_chain_planning.location (
    location_id        varchar(64) primary key,
    gln                varchar(13),                       -- GS1 Global Location Number
    location_type      varchar(16),                       -- plant|dc|warehouse|supplier|customer_dc|consignment
    country_iso2       varchar(2),
    region             varchar(32),
    tier               smallint,                          -- network tier
    time_zone          varchar(32),
    status             varchar(16)
);

-- Demand-side customer / channel bucket.
create table if not exists sop_supply_chain_planning.customer (
    customer_id        varchar(64) primary key,
    customer_name      varchar(255),
    channel            varchar(32),                       -- retail|ecom|distributor|direct|ota|other
    segment            varchar(32),                       -- strategic|key|growth|tail
    country_iso2       varchar(2),
    region             varchar(32),
    priority           smallint,                          -- allocation priority 1..5
    status             varchar(16)
);

-- Actual shipments / consumption history (the truth source for accuracy).
create table if not exists sop_supply_chain_planning.sales_history (
    sales_history_id   bigint primary key,
    item_id            varchar(64) references sop_supply_chain_planning.item(item_id),
    location_id        varchar(64) references sop_supply_chain_planning.location(location_id),
    customer_id        varchar(64) references sop_supply_chain_planning.customer(customer_id),
    period_start       date,
    period_grain       varchar(8),                        -- day|week|month
    shipped_units      numeric(18,4),
    shipped_value      numeric(18,4),
    returns_units      numeric(18,4),
    source_system      varchar(32),                       -- ERP|POS|EDI_852|syndicated
    ingested_at        timestamp
);

-- S&OP monthly cycle metadata (Oliver Wight 5-step).
create table if not exists sop_supply_chain_planning.sop_cycle (
    cycle_id                       varchar(32) primary key,    -- YYYY-MM
    cycle_start                    date,
    cycle_end                      date,
    product_review_ts              timestamp,
    demand_review_ts               timestamp,
    supply_review_ts               timestamp,
    integrated_reconciliation_ts   timestamp,
    mbr_ts                         timestamp,                  -- Management Business Review / exec S&OP
    signed_off_by                  varchar(128),
    signed_off_at                  timestamp,
    status                         varchar(16)                 -- open|locked|signed_off|reopened
);

-- Time-phased demand forecast. Multi-version stream (baseline → consensus).
create table if not exists sop_supply_chain_planning.forecast (
    forecast_id        bigint primary key,
    item_id            varchar(64) references sop_supply_chain_planning.item(item_id),
    location_id        varchar(64) references sop_supply_chain_planning.location(location_id),
    customer_id        varchar(64) references sop_supply_chain_planning.customer(customer_id),
    forecast_version   varchar(32),                       -- statistical_baseline|sales_input|marketing_input|finance_aligned|consensus
    cycle_id           varchar(32) references sop_supply_chain_planning.sop_cycle(cycle_id),
    period_start       date,
    period_grain       varchar(8),                        -- week|month
    forecast_units     numeric(18,4),
    forecast_value     numeric(18,4),
    forecast_low       numeric(18,4),                     -- P10 / probabilistic
    forecast_high      numeric(18,4),                     -- P90
    model_id           varchar(64),                       -- ARIMA, ETS, Prophet, GBM, transformer
    published_at       timestamp,
    locked             boolean
);

-- A what-if planning scenario.
create table if not exists sop_supply_chain_planning.scenario (
    scenario_id                varchar(64) primary key,
    cycle_id                   varchar(32) references sop_supply_chain_planning.sop_cycle(cycle_id),
    scenario_name              varchar(255),
    scenario_type              varchar(32),               -- base|upside|downside|disruption|capacity_invest|tariff|new_product|eol
    description                text,
    created_by                 varchar(64),
    created_at                 timestamp,
    published_at               timestamp,
    status                     varchar(16),               -- draft|evaluated|adopted|rejected|archived
    revenue_impact_usd         numeric(18,2),
    working_capital_impact_usd numeric(18,2),
    service_level_impact_pct   numeric(5,2)
);

-- Time-phased supply plan.
create table if not exists sop_supply_chain_planning.supply_plan (
    supply_plan_id       bigint primary key,
    item_id              varchar(64) references sop_supply_chain_planning.item(item_id),
    location_id          varchar(64) references sop_supply_chain_planning.location(location_id),
    source_location_id   varchar(64),                     -- origin plant/supplier; NULL = same location
    supply_type          varchar(16),                     -- produce|transfer|purchase|co_manufacture|alternate
    cycle_id             varchar(32) references sop_supply_chain_planning.sop_cycle(cycle_id),
    scenario_id          varchar(64) references sop_supply_chain_planning.scenario(scenario_id),
    period_start         date,
    period_grain         varchar(8),
    planned_units        numeric(18,4),
    planned_value        numeric(18,4),
    lead_time_days       smallint,
    status               varchar(16),                     -- draft|firm|released|cancelled
    published_at         timestamp
);

-- On-hand + on-order + in-transit inventory snapshot per item-location-period.
create table if not exists sop_supply_chain_planning.inventory_position (
    inventory_position_id  bigint primary key,
    item_id                varchar(64) references sop_supply_chain_planning.item(item_id),
    location_id            varchar(64) references sop_supply_chain_planning.location(location_id),
    snapshot_ts            timestamp,
    on_hand_units          numeric(18,4),
    on_order_units         numeric(18,4),
    in_transit_units       numeric(18,4),
    allocated_units        numeric(18,4),
    safety_stock_units     numeric(18,4),
    reorder_point_units    numeric(18,4),
    inventory_value        numeric(18,4),
    doh_days               numeric(8,2),
    excess_units           numeric(18,4),
    stockout_flag          boolean
);

-- Available capacity per location-resource-period (constrains supply plan).
create table if not exists sop_supply_chain_planning.capacity (
    capacity_id          varchar(64) primary key,
    location_id          varchar(64) references sop_supply_chain_planning.location(location_id),
    resource_id          varchar(64),
    resource_type        varchar(16),                     -- line|machine|labor|supplier|tooling
    period_start         date,
    period_grain         varchar(8),
    available_hours      numeric(12,2),
    planned_load_hours   numeric(12,2),
    utilization_pct      numeric(5,2),
    changeover_hours     numeric(8,2),
    status               varchar(16)                      -- available|reduced|down|qualified_alt
);

-- Bill of Materials — parent ↔ component.
create table if not exists sop_supply_chain_planning.bom (
    bom_id              varchar(64) primary key,
    parent_item_id      varchar(64) references sop_supply_chain_planning.item(item_id),
    component_item_id   varchar(64) references sop_supply_chain_planning.item(item_id),
    location_id         varchar(64) references sop_supply_chain_planning.location(location_id),
    quantity_per        numeric(15,6),
    yield_pct           numeric(5,2),
    effective_from      date,
    effective_to        date,
    bom_version         varchar(16)
);

-- Helpful indexes on time and cardinality.
create index if not exists ix_fcst_item_loc      on sop_supply_chain_planning.forecast(item_id, location_id, period_start);
create index if not exists ix_fcst_cycle_version on sop_supply_chain_planning.forecast(cycle_id, forecast_version);
create index if not exists ix_supply_item_loc    on sop_supply_chain_planning.supply_plan(item_id, location_id, period_start);
create index if not exists ix_supply_scenario    on sop_supply_chain_planning.supply_plan(scenario_id);
create index if not exists ix_invpos_item_loc    on sop_supply_chain_planning.inventory_position(item_id, location_id, snapshot_ts);
create index if not exists ix_cap_loc_period     on sop_supply_chain_planning.capacity(location_id, period_start);
create index if not exists ix_sh_item_loc        on sop_supply_chain_planning.sales_history(item_id, location_id, period_start);
create index if not exists ix_bom_parent         on sop_supply_chain_planning.bom(parent_item_id);
