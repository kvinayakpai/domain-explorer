-- =============================================================================
-- Omnichannel Order Management — Kimball dimensional schema
-- Stars: fct_orders_oms, fct_order_line_oms, fct_allocations, fct_fulfillment_events,
--        fct_shipments_oms, fct_inventory_position_snapshot, fct_returns_oms
-- Conformed dims: dim_customer_oms, dim_location, dim_product_oms,
--                 dim_sourcing_rule, dim_carrier, dim_date_oms
-- The `_oms` suffix on collision-prone names avoids overlap with the
-- merchandising / pricing_and_promotions / trade_promotion_management anchors.
-- =============================================================================

create schema if not exists omnichannel_oms_dim;

-- ---------- DIMS ----------
create table if not exists omnichannel_oms_dim.dim_date_oms (
    date_key       integer primary key,            -- yyyymmdd
    cal_date       date,
    day_of_week    smallint,
    day_name       varchar(12),
    month          smallint,
    month_name     varchar(12),
    quarter        smallint,
    year           smallint,
    is_weekend     boolean
);

create table if not exists omnichannel_oms_dim.dim_customer_oms (
    customer_sk        bigint primary key,
    customer_id        varchar(32) unique,
    golden_record_id   varchar(32),
    home_country_iso2  varchar(2),
    has_loyalty        boolean,
    status             varchar(16),
    valid_from         timestamp,
    valid_to           timestamp,
    is_current         boolean
);

create table if not exists omnichannel_oms_dim.dim_location (
    location_sk              bigint primary key,
    location_id              varchar(16) unique,
    name                     varchar(255),
    location_type            varchar(16),
    country_iso2             varchar(2),
    region                   varchar(64),
    timezone                 varchar(32),
    bopis_enabled            boolean,
    ship_from_enabled        boolean,
    pick_capacity_per_hour   integer,
    status                   varchar(16)
);

create table if not exists omnichannel_oms_dim.dim_product_oms (
    product_sk                  bigint primary key,
    product_id                  varchar(32) unique,
    sku                         varchar(32),
    gtin                        varchar(14),
    name                        varchar(255),
    category_id                 varchar(32),
    hazmat_flag                 boolean,
    weight_grams                integer,
    pack_type                   varchar(16),
    status                      varchar(16)
);

create table if not exists omnichannel_oms_dim.dim_sourcing_rule (
    rule_sk                  bigint primary key,
    rule_id                  varchar(32) unique,
    rule_name                varchar(128),
    priority                 smallint,
    cost_weight              numeric(5,4),
    speed_weight             numeric(5,4),
    capacity_weight          numeric(5,4),
    clearance_pull_weight    numeric(5,4),
    status                   varchar(16)
);

create table if not exists omnichannel_oms_dim.dim_carrier (
    carrier_sk     smallint primary key,
    carrier        varchar(16) unique,
    service_default varchar(32)
);

-- ---------- FACTS ----------

-- One row per order header.
create table if not exists omnichannel_oms_dim.fct_orders_oms (
    order_id              varchar(32) primary key,
    date_key              integer  references omnichannel_oms_dim.dim_date_oms(date_key),
    customer_sk           bigint   references omnichannel_oms_dim.dim_customer_oms(customer_sk),
    capture_location_sk   bigint   references omnichannel_oms_dim.dim_location(location_sk),
    capture_channel       varchar(16),
    order_total_minor     bigint,
    currency              varchar(3),
    order_total_usd       numeric(15,4),
    line_count            smallint,
    is_bopis              boolean,
    is_sfs                boolean,
    is_split_shipment     boolean,
    is_cancelled          boolean,
    is_returned           boolean,
    promise_delivery_ts   timestamp,
    captured_at           timestamp,
    closed_at             timestamp,
    cycle_time_hours      numeric(10,2)
);

-- One row per order_line.
create table if not exists omnichannel_oms_dim.fct_order_line_oms (
    order_line_id          varchar(32) primary key,
    order_id               varchar(32),
    date_key               integer  references omnichannel_oms_dim.dim_date_oms(date_key),
    product_sk             bigint   references omnichannel_oms_dim.dim_product_oms(product_sk),
    customer_sk            bigint   references omnichannel_oms_dim.dim_customer_oms(customer_sk),
    fulfillment_method     varchar(16),
    quantity               integer,
    line_total_minor       bigint,
    line_status            varchar(16),
    is_substituted         boolean,
    is_cancelled           boolean,
    is_first_pick_filled   boolean
);

-- One row per allocation decision.
create table if not exists omnichannel_oms_dim.fct_allocations (
    allocation_id          varchar(32) primary key,
    order_line_id          varchar(32),
    date_key               integer  references omnichannel_oms_dim.dim_date_oms(date_key),
    location_sk            bigint   references omnichannel_oms_dim.dim_location(location_sk),
    rule_sk                bigint   references omnichannel_oms_dim.dim_sourcing_rule(rule_sk),
    allocated_quantity     integer,
    estimated_cost_minor   bigint,
    estimated_cost_usd     numeric(12,2),
    estimated_ready_ts     timestamp,
    estimated_delivery_ts  timestamp,
    is_completed           boolean,
    is_reallocated         boolean,
    allocated_at           timestamp
);

-- One row per fulfillment event (event-sourced lifecycle).
create table if not exists omnichannel_oms_dim.fct_fulfillment_events (
    event_id          varchar(32) primary key,
    allocation_id     varchar(32),
    order_line_id     varchar(32),
    date_key          integer  references omnichannel_oms_dim.dim_date_oms(date_key),
    location_sk       bigint   references omnichannel_oms_dim.dim_location(location_sk),
    event_type        varchar(32),
    actor_role        varchar(16),
    occurred_at       timestamp
);

-- One row per shipment (parcel).
create table if not exists omnichannel_oms_dim.fct_shipments_oms (
    shipment_id              varchar(32) primary key,
    allocation_id            varchar(32),
    date_key                 integer  references omnichannel_oms_dim.dim_date_oms(date_key),
    carrier_sk               smallint references omnichannel_oms_dim.dim_carrier(carrier_sk),
    ship_from_location_sk    bigint   references omnichannel_oms_dim.dim_location(location_sk),
    service_level            varchar(32),
    weight_grams             integer,
    cost_minor               bigint,
    cost_usd                 numeric(12,2),
    shipped_at               timestamp,
    delivered_at             timestamp,
    transit_hours            numeric(10,2),
    is_on_time               boolean,
    is_delivered             boolean
);

-- Snapshot of inventory position by location × product × day.
create table if not exists omnichannel_oms_dim.fct_inventory_position_snapshot (
    snapshot_id            varchar(48) primary key,         -- date_key || '-' || position_id
    date_key               integer  references omnichannel_oms_dim.dim_date_oms(date_key),
    location_sk            bigint   references omnichannel_oms_dim.dim_location(location_sk),
    product_sk             bigint   references omnichannel_oms_dim.dim_product_oms(product_sk),
    on_hand_units          integer,
    allocated_units        integer,
    reserved_safety_units  integer,
    atp_units              integer,
    refresh_lag_seconds    integer,
    as_of_ts               timestamp
);

-- One row per RMA.
create table if not exists omnichannel_oms_dim.fct_returns_oms (
    rma_id                varchar(32) primary key,
    order_id              varchar(32),
    date_key              integer  references omnichannel_oms_dim.dim_date_oms(date_key),
    customer_sk           bigint   references omnichannel_oms_dim.dim_customer_oms(customer_sk),
    return_location_sk    bigint   references omnichannel_oms_dim.dim_location(location_sk),
    return_reason         varchar(32),
    return_method         varchar(16),
    refund_method         varchar(16),
    refund_amount_minor   bigint,
    restock_outcome       varchar(16),
    initiated_at          timestamp,
    refund_issued_at      timestamp,
    return_cycle_days     numeric(10,2),
    is_refunded           boolean
);

-- Helpful indexes
create index if not exists ix_fct_oms_orders_date     on omnichannel_oms_dim.fct_orders_oms(date_key);
create index if not exists ix_fct_oms_orders_cust     on omnichannel_oms_dim.fct_orders_oms(customer_sk);
create index if not exists ix_fct_oms_lines_order     on omnichannel_oms_dim.fct_order_line_oms(order_id);
create index if not exists ix_fct_oms_alloc_loc      on omnichannel_oms_dim.fct_allocations(location_sk);
create index if not exists ix_fct_oms_events_alloc   on omnichannel_oms_dim.fct_fulfillment_events(allocation_id);
create index if not exists ix_fct_oms_events_type    on omnichannel_oms_dim.fct_fulfillment_events(event_type);
create index if not exists ix_fct_oms_ship_carrier   on omnichannel_oms_dim.fct_shipments_oms(carrier_sk);
create index if not exists ix_fct_oms_inv_loc_prod   on omnichannel_oms_dim.fct_inventory_position_snapshot(location_sk, product_sk);
create index if not exists ix_fct_oms_returns_order  on omnichannel_oms_dim.fct_returns_oms(order_id);
