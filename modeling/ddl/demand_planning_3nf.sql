-- =============================================================================
-- Demand Planning — 3NF schema (excerpt)
-- Statistical + consensus forecasting feeding S&OP, replenishment, capacity.
-- =============================================================================

create schema if not exists demand_planning_3nf;

create table if not exists demand_planning_3nf.product (
    product_id           varchar primary key,
    product_name         varchar not null,
    category_id          varchar not null,
    uom                  varchar(8) not null,
    is_active            boolean not null default true
);

create table if not exists demand_planning_3nf.product_category (
    category_id          varchar primary key,
    category_name        varchar not null,
    parent_category_id   varchar references demand_planning_3nf.product_category(category_id)
);

create table if not exists demand_planning_3nf.location (
    location_id          varchar primary key,
    location_name        varchar not null,
    location_type        varchar(16) not null,
    region_code          varchar(8) not null,
    parent_location_id   varchar references demand_planning_3nf.location(location_id)
);

create table if not exists demand_planning_3nf.customer (
    customer_id          varchar primary key,
    customer_name        varchar not null,
    channel              varchar(16) not null,
    region_code          varchar(8) not null
);

create table if not exists demand_planning_3nf.product_customer_xref (
    product_id           varchar not null references demand_planning_3nf.product(product_id),
    customer_id          varchar not null references demand_planning_3nf.customer(customer_id),
    customer_sku         varchar not null,
    primary key (product_id, customer_id)
);

create table if not exists demand_planning_3nf.calendar_period (
    period_id            varchar primary key,
    period_start         date not null,
    period_end           date not null,
    period_type          varchar(8) not null
);

create table if not exists demand_planning_3nf.statistical_forecast (
    forecast_run_id      varchar not null,
    product_id           varchar not null references demand_planning_3nf.product(product_id),
    location_id          varchar not null references demand_planning_3nf.location(location_id),
    period_id            varchar not null references demand_planning_3nf.calendar_period(period_id),
    forecast_qty         numeric(14, 2) not null,
    model_code           varchar(16) not null,
    generated_at         timestamp not null,
    primary key (forecast_run_id, product_id, location_id, period_id)
);

create table if not exists demand_planning_3nf.consensus_forecast (
    cycle_id             varchar not null,
    product_id           varchar not null references demand_planning_3nf.product(product_id),
    location_id          varchar not null references demand_planning_3nf.location(location_id),
    period_id            varchar not null references demand_planning_3nf.calendar_period(period_id),
    consensus_qty        numeric(14, 2) not null,
    locked_at            timestamp,
    locked_by            varchar,
    primary key (cycle_id, product_id, location_id, period_id)
);

create table if not exists demand_planning_3nf.forecast_override (
    override_id          varchar primary key,
    cycle_id             varchar not null,
    product_id           varchar not null references demand_planning_3nf.product(product_id),
    location_id          varchar not null references demand_planning_3nf.location(location_id),
    period_id            varchar not null references demand_planning_3nf.calendar_period(period_id),
    override_qty         numeric(14, 2) not null,
    reason_code          varchar(16) not null,
    submitted_by         varchar not null,
    submitted_at         timestamp not null
);

create table if not exists demand_planning_3nf.actual_demand (
    product_id           varchar not null references demand_planning_3nf.product(product_id),
    location_id          varchar not null references demand_planning_3nf.location(location_id),
    period_id            varchar not null references demand_planning_3nf.calendar_period(period_id),
    actual_qty           numeric(14, 2) not null,
    primary key (product_id, location_id, period_id)
);

create table if not exists demand_planning_3nf.sales_order (
    order_id             varchar primary key,
    customer_id          varchar not null references demand_planning_3nf.customer(customer_id),
    placed_at            timestamp not null,
    requested_delivery   date not null,
    status               varchar(16) not null
);

create table if not exists demand_planning_3nf.sales_order_line (
    order_id             varchar not null references demand_planning_3nf.sales_order(order_id),
    line_no              smallint not null,
    product_id           varchar not null references demand_planning_3nf.product(product_id),
    location_id          varchar not null references demand_planning_3nf.location(location_id),
    requested_qty        numeric(14, 2) not null,
    promised_qty         numeric(14, 2),
    unit_price           numeric(12, 4) not null,
    primary key (order_id, line_no)
);

create table if not exists demand_planning_3nf.shipment (
    shipment_id          varchar primary key,
    order_id             varchar not null references demand_planning_3nf.sales_order(order_id),
    shipped_at           timestamp not null,
    delivered_at         timestamp,
    carrier              varchar(32) not null
);

create table if not exists demand_planning_3nf.shipment_line (
    shipment_id          varchar not null references demand_planning_3nf.shipment(shipment_id),
    line_no              smallint not null,
    product_id           varchar not null references demand_planning_3nf.product(product_id),
    shipped_qty          numeric(14, 2) not null,
    primary key (shipment_id, line_no)
);

create table if not exists demand_planning_3nf.promotion_event (
    promo_id             varchar primary key,
    promo_name           varchar not null,
    customer_id          varchar references demand_planning_3nf.customer(customer_id),
    valid_from           date not null,
    valid_to             date not null,
    expected_lift_pct    numeric(6, 2)
);

create table if not exists demand_planning_3nf.promotion_product (
    promo_id             varchar not null references demand_planning_3nf.promotion_event(promo_id),
    product_id           varchar not null references demand_planning_3nf.product(product_id),
    primary key (promo_id, product_id)
);

create table if not exists demand_planning_3nf.safety_stock (
    product_id           varchar not null references demand_planning_3nf.product(product_id),
    location_id          varchar not null references demand_planning_3nf.location(location_id),
    effective_from       date not null,
    safety_stock_units   numeric(14, 2) not null,
    service_target_pct   numeric(5, 2) not null,
    primary key (product_id, location_id, effective_from)
);

create table if not exists demand_planning_3nf.npi_event (
    npi_id               varchar primary key,
    product_id           varchar not null references demand_planning_3nf.product(product_id),
    launch_date          date not null,
    cannibalised_product_id varchar references demand_planning_3nf.product(product_id),
    cannibalisation_pct  numeric(5, 2)
);

create table if not exists demand_planning_3nf.forecast_cycle (
    cycle_id             varchar primary key,
    cycle_name           varchar not null,
    cycle_start          date not null,
    cycle_close          date not null,
    status               varchar(16) not null
);
