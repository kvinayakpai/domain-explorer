-- =============================================================================
-- Demand Planning — dimensional mart (excerpt)
-- Star schema for forecast accuracy, bias, fill rate, OTIF analytics.
-- =============================================================================

create schema if not exists demand_planning_dim;

create table if not exists demand_planning_dim.dim_date (
    date_key             integer primary key,
    date_actual          date not null,
    week_of_year         smallint not null,
    fiscal_period        varchar(8),
    fiscal_quarter       varchar(8)
);

create table if not exists demand_planning_dim.dim_period (
    period_key           bigint primary key,
    period_id            varchar not null,
    period_type          varchar(8) not null,
    period_start         date not null,
    period_end           date not null
);

create table if not exists demand_planning_dim.dim_product (
    product_key          bigint primary key,
    product_id           varchar not null,
    product_name         varchar not null,
    category_l1          varchar(64),
    category_l2          varchar(64),
    category_l3          varchar(64),
    uom                  varchar(8) not null,
    valid_from           timestamp not null,
    valid_to             timestamp,
    is_current           boolean not null
);

create table if not exists demand_planning_dim.dim_location (
    location_key         bigint primary key,
    location_id          varchar not null,
    location_name        varchar not null,
    location_type        varchar(16) not null,
    region_code          varchar(8) not null,
    valid_from           timestamp not null,
    valid_to             timestamp,
    is_current           boolean not null
);

create table if not exists demand_planning_dim.dim_customer (
    customer_key         bigint primary key,
    customer_id          varchar not null,
    customer_name        varchar not null,
    channel              varchar(16) not null,
    region_code          varchar(8) not null,
    valid_from           timestamp not null,
    valid_to             timestamp,
    is_current           boolean not null
);

create table if not exists demand_planning_dim.dim_forecast_cycle (
    cycle_key            bigint primary key,
    cycle_id             varchar not null,
    cycle_name           varchar not null,
    cycle_start          date not null,
    cycle_close          date not null
);

create table if not exists demand_planning_dim.dim_model (
    model_key            smallint primary key,
    model_code           varchar(16) not null,
    model_name           varchar(64) not null,
    family               varchar(32) not null
);

create table if not exists demand_planning_dim.fact_forecast_vs_actual (
    period_key           bigint not null references demand_planning_dim.dim_period(period_key),
    product_key          bigint not null references demand_planning_dim.dim_product(product_key),
    location_key         bigint not null references demand_planning_dim.dim_location(location_key),
    cycle_key            bigint not null references demand_planning_dim.dim_forecast_cycle(cycle_key),
    model_key            smallint not null references demand_planning_dim.dim_model(model_key),
    statistical_qty      numeric(14, 2) not null,
    consensus_qty        numeric(14, 2) not null,
    actual_qty           numeric(14, 2),
    abs_error            numeric(14, 2),
    bias                 numeric(14, 2),
    primary key (period_key, product_key, location_key, cycle_key, model_key)
);

create table if not exists demand_planning_dim.fact_orders_daily (
    date_key             integer not null references demand_planning_dim.dim_date(date_key),
    product_key          bigint not null references demand_planning_dim.dim_product(product_key),
    location_key         bigint not null references demand_planning_dim.dim_location(location_key),
    customer_key         bigint references demand_planning_dim.dim_customer(customer_key),
    requested_qty        numeric(14, 2) not null,
    promised_qty         numeric(14, 2) not null,
    shipped_qty          numeric(14, 2) not null,
    on_time_in_full      smallint not null,
    primary key (date_key, product_key, location_key)
);

create table if not exists demand_planning_dim.fact_inventory_position (
    date_key             integer not null references demand_planning_dim.dim_date(date_key),
    product_key          bigint not null references demand_planning_dim.dim_product(product_key),
    location_key         bigint not null references demand_planning_dim.dim_location(location_key),
    on_hand_qty          numeric(14, 2) not null,
    safety_stock_units   numeric(14, 2) not null,
    days_of_supply       numeric(8, 2),
    primary key (date_key, product_key, location_key)
);

create table if not exists demand_planning_dim.fact_promo_lift (
    period_key           bigint not null references demand_planning_dim.dim_period(period_key),
    product_key          bigint not null references demand_planning_dim.dim_product(product_key),
    customer_key         bigint not null references demand_planning_dim.dim_customer(customer_key),
    baseline_qty         numeric(14, 2) not null,
    promoted_qty         numeric(14, 2) not null,
    measured_lift_pct    numeric(6, 2)
);
