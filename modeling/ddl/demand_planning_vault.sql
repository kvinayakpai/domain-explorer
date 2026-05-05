-- =============================================================================
-- Demand Planning — Data Vault 2.0 (excerpt)
-- Hubs / Links / Satellites for product, location, forecast, order.
-- =============================================================================

create schema if not exists demand_planning_vault;

-- Hubs
create table if not exists demand_planning_vault.hub_product (
    product_hk           bytea primary key,
    product_bk           varchar not null,
    load_dts             timestamp not null,
    rec_src              varchar not null
);

create table if not exists demand_planning_vault.hub_location (
    location_hk          bytea primary key,
    location_bk          varchar not null,
    load_dts             timestamp not null,
    rec_src              varchar not null
);

create table if not exists demand_planning_vault.hub_customer (
    customer_hk          bytea primary key,
    customer_bk          varchar not null,
    load_dts             timestamp not null,
    rec_src              varchar not null
);

create table if not exists demand_planning_vault.hub_forecast_cycle (
    cycle_hk             bytea primary key,
    cycle_bk             varchar not null,
    load_dts             timestamp not null,
    rec_src              varchar not null
);

create table if not exists demand_planning_vault.hub_sales_order (
    order_hk             bytea primary key,
    order_bk             varchar not null,
    load_dts             timestamp not null,
    rec_src              varchar not null
);

create table if not exists demand_planning_vault.hub_promo (
    promo_hk             bytea primary key,
    promo_bk             varchar not null,
    load_dts             timestamp not null,
    rec_src              varchar not null
);

-- Links
create table if not exists demand_planning_vault.link_forecast_point (
    link_hk              bytea primary key,
    cycle_hk             bytea not null references demand_planning_vault.hub_forecast_cycle(cycle_hk),
    product_hk           bytea not null references demand_planning_vault.hub_product(product_hk),
    location_hk          bytea not null references demand_planning_vault.hub_location(location_hk),
    period_bk            varchar not null,
    load_dts             timestamp not null,
    rec_src              varchar not null
);

create table if not exists demand_planning_vault.link_order_line (
    link_hk              bytea primary key,
    order_hk             bytea not null references demand_planning_vault.hub_sales_order(order_hk),
    product_hk           bytea not null references demand_planning_vault.hub_product(product_hk),
    location_hk          bytea not null references demand_planning_vault.hub_location(location_hk),
    customer_hk          bytea not null references demand_planning_vault.hub_customer(customer_hk),
    line_no              smallint not null,
    load_dts             timestamp not null,
    rec_src              varchar not null
);

create table if not exists demand_planning_vault.link_promo_product (
    link_hk              bytea primary key,
    promo_hk             bytea not null references demand_planning_vault.hub_promo(promo_hk),
    product_hk           bytea not null references demand_planning_vault.hub_product(product_hk),
    customer_hk          bytea references demand_planning_vault.hub_customer(customer_hk),
    load_dts             timestamp not null,
    rec_src              varchar not null
);

create table if not exists demand_planning_vault.link_safety_stock (
    link_hk              bytea primary key,
    product_hk           bytea not null references demand_planning_vault.hub_product(product_hk),
    location_hk          bytea not null references demand_planning_vault.hub_location(location_hk),
    effective_from       date not null,
    load_dts             timestamp not null,
    rec_src              varchar not null
);

-- Satellites
create table if not exists demand_planning_vault.sat_product_descriptive (
    product_hk           bytea not null references demand_planning_vault.hub_product(product_hk),
    load_dts             timestamp not null,
    load_end_dts         timestamp,
    hash_diff            bytea not null,
    product_name         varchar not null,
    category_id          varchar not null,
    uom                  varchar(8) not null,
    rec_src              varchar not null,
    primary key (product_hk, load_dts)
);

create table if not exists demand_planning_vault.sat_forecast_point_value (
    link_hk              bytea not null,
    load_dts             timestamp not null,
    load_end_dts         timestamp,
    hash_diff            bytea not null,
    statistical_qty      numeric(14, 2),
    consensus_qty        numeric(14, 2),
    override_qty         numeric(14, 2),
    model_code           varchar(16),
    rec_src              varchar not null,
    primary key (link_hk, load_dts)
);

create table if not exists demand_planning_vault.sat_order_line_state (
    link_hk              bytea not null,
    load_dts             timestamp not null,
    load_end_dts         timestamp,
    hash_diff            bytea not null,
    requested_qty        numeric(14, 2) not null,
    promised_qty         numeric(14, 2),
    unit_price           numeric(12, 4) not null,
    rec_src              varchar not null,
    primary key (link_hk, load_dts)
);

create table if not exists demand_planning_vault.sat_safety_stock_value (
    link_hk              bytea not null,
    load_dts             timestamp not null,
    load_end_dts         timestamp,
    hash_diff            bytea not null,
    safety_stock_units   numeric(14, 2) not null,
    service_target_pct   numeric(5, 2) not null,
    rec_src              varchar not null,
    primary key (link_hk, load_dts)
);

create table if not exists demand_planning_vault.sat_customer_descriptive (
    customer_hk          bytea not null references demand_planning_vault.hub_customer(customer_hk),
    load_dts             timestamp not null,
    load_end_dts         timestamp,
    hash_diff            bytea not null,
    customer_name        varchar not null,
    channel              varchar(16) not null,
    region_code          varchar(8) not null,
    rec_src              varchar not null,
    primary key (customer_hk, load_dts)
);
