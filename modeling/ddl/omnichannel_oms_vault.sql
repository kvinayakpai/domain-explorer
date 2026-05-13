-- =============================================================================
-- Omnichannel Order Management — Data Vault 2.0 schema
-- Hubs (business keys) + Links (relationships) + Satellites (descriptive,
-- insert-only, time-stamped). Mirrors Manhattan / Sterling / Salesforce OMS
-- and the EDI 940/945/846 source contracts.
-- =============================================================================

create schema if not exists omnichannel_oms_vault;

-- ---------- HUBS ----------
create table if not exists omnichannel_oms_vault.h_customer (
    hk_customer    varchar(32) primary key,         -- MD5(customer_id)
    customer_id    varchar(32) unique,
    load_dts       timestamp,
    record_source  varchar(64)
);

create table if not exists omnichannel_oms_vault.h_location (
    hk_location    varchar(32) primary key,
    location_id    varchar(16) unique,
    load_dts       timestamp,
    record_source  varchar(64)
);

create table if not exists omnichannel_oms_vault.h_product (
    hk_product     varchar(32) primary key,
    product_id     varchar(32) unique,
    load_dts       timestamp,
    record_source  varchar(64)
);

create table if not exists omnichannel_oms_vault.h_order (
    hk_order       varchar(32) primary key,
    order_id       varchar(32) unique,
    load_dts       timestamp,
    record_source  varchar(64)
);

create table if not exists omnichannel_oms_vault.h_order_line (
    hk_order_line  varchar(32) primary key,
    order_line_id  varchar(32) unique,
    load_dts       timestamp,
    record_source  varchar(64)
);

create table if not exists omnichannel_oms_vault.h_allocation (
    hk_allocation  varchar(32) primary key,
    allocation_id  varchar(32) unique,
    load_dts       timestamp,
    record_source  varchar(64)
);

create table if not exists omnichannel_oms_vault.h_shipment (
    hk_shipment    varchar(32) primary key,
    shipment_id    varchar(32) unique,
    load_dts       timestamp,
    record_source  varchar(64)
);

create table if not exists omnichannel_oms_vault.h_rma (
    hk_rma         varchar(32) primary key,
    rma_id         varchar(32) unique,
    load_dts       timestamp,
    record_source  varchar(64)
);

create table if not exists omnichannel_oms_vault.h_sourcing_rule (
    hk_rule        varchar(32) primary key,
    rule_id        varchar(32) unique,
    load_dts       timestamp,
    record_source  varchar(64)
);

-- ---------- LINKS ----------
create table if not exists omnichannel_oms_vault.l_order_customer (
    hk_link        varchar(32) primary key,
    hk_order       varchar(32) references omnichannel_oms_vault.h_order(hk_order),
    hk_customer    varchar(32) references omnichannel_oms_vault.h_customer(hk_customer),
    load_dts       timestamp,
    record_source  varchar(64)
);

create table if not exists omnichannel_oms_vault.l_line_order (
    hk_link        varchar(32) primary key,
    hk_order_line  varchar(32) references omnichannel_oms_vault.h_order_line(hk_order_line),
    hk_order       varchar(32) references omnichannel_oms_vault.h_order(hk_order),
    hk_product     varchar(32) references omnichannel_oms_vault.h_product(hk_product),
    load_dts       timestamp,
    record_source  varchar(64)
);

create table if not exists omnichannel_oms_vault.l_allocation_line (
    hk_link        varchar(32) primary key,
    hk_allocation  varchar(32) references omnichannel_oms_vault.h_allocation(hk_allocation),
    hk_order_line  varchar(32) references omnichannel_oms_vault.h_order_line(hk_order_line),
    hk_location    varchar(32) references omnichannel_oms_vault.h_location(hk_location),
    hk_rule        varchar(32) references omnichannel_oms_vault.h_sourcing_rule(hk_rule),
    load_dts       timestamp,
    record_source  varchar(64)
);

create table if not exists omnichannel_oms_vault.l_shipment_alloc (
    hk_link        varchar(32) primary key,
    hk_shipment    varchar(32) references omnichannel_oms_vault.h_shipment(hk_shipment),
    hk_allocation  varchar(32) references omnichannel_oms_vault.h_allocation(hk_allocation),
    load_dts       timestamp,
    record_source  varchar(64)
);

create table if not exists omnichannel_oms_vault.l_rma_order (
    hk_link        varchar(32) primary key,
    hk_rma         varchar(32) references omnichannel_oms_vault.h_rma(hk_rma),
    hk_order       varchar(32) references omnichannel_oms_vault.h_order(hk_order),
    hk_customer    varchar(32) references omnichannel_oms_vault.h_customer(hk_customer),
    load_dts       timestamp,
    record_source  varchar(64)
);

create table if not exists omnichannel_oms_vault.l_inventory_position (
    hk_link        varchar(32) primary key,
    hk_location    varchar(32) references omnichannel_oms_vault.h_location(hk_location),
    hk_product     varchar(32) references omnichannel_oms_vault.h_product(hk_product),
    load_dts       timestamp,
    record_source  varchar(64)
);

-- ---------- SATELLITES ----------
create table if not exists omnichannel_oms_vault.s_customer_descriptive (
    hk_customer        varchar(32) references omnichannel_oms_vault.h_customer(hk_customer),
    load_dts           timestamp,
    golden_record_id   varchar(32),
    home_country_iso2  varchar(2),
    loyalty_id         varchar(32),
    status             varchar(16),
    record_source      varchar(64),
    primary key (hk_customer, load_dts)
);

create table if not exists omnichannel_oms_vault.s_location_descriptive (
    hk_location              varchar(32) references omnichannel_oms_vault.h_location(hk_location),
    load_dts                 timestamp,
    name                     varchar(255),
    location_type            varchar(16),
    country_iso2             varchar(2),
    region                   varchar(64),
    timezone                 varchar(32),
    bopis_enabled            boolean,
    ship_from_enabled        boolean,
    pick_capacity_per_hour   integer,
    status                   varchar(16),
    record_source            varchar(64),
    primary key (hk_location, load_dts)
);

create table if not exists omnichannel_oms_vault.s_product_descriptive (
    hk_product                  varchar(32) references omnichannel_oms_vault.h_product(hk_product),
    load_dts                    timestamp,
    sku                         varchar(32),
    gtin                        varchar(14),
    name                        varchar(255),
    category_id                 varchar(32),
    hazmat_flag                 boolean,
    weight_grams                integer,
    dimensional_weight_grams    integer,
    pack_type                   varchar(16),
    status                      varchar(16),
    record_source               varchar(64),
    primary key (hk_product, load_dts)
);

create table if not exists omnichannel_oms_vault.s_inventory_state (
    hk_location            varchar(32) references omnichannel_oms_vault.h_location(hk_location),
    hk_product             varchar(32) references omnichannel_oms_vault.h_product(hk_product),
    load_dts               timestamp,
    on_hand_units          integer,
    allocated_units        integer,
    in_transit_units       integer,
    reserved_safety_units  integer,
    atp_units              integer,
    source_system          varchar(32),
    refresh_lag_seconds    integer,
    record_source          varchar(64),
    primary key (hk_location, hk_product, load_dts)
);

create table if not exists omnichannel_oms_vault.s_order_status (
    hk_order             varchar(32) references omnichannel_oms_vault.h_order(hk_order),
    load_dts             timestamp,
    capture_channel      varchar(16),
    payment_status       varchar(16),
    order_status         varchar(16),
    promise_delivery_ts  timestamp,
    closed_at            timestamp,
    record_source        varchar(64),
    primary key (hk_order, load_dts)
);

create table if not exists omnichannel_oms_vault.s_order_line_state (
    hk_order_line              varchar(32) references omnichannel_oms_vault.h_order_line(hk_order_line),
    load_dts                   timestamp,
    quantity                   integer,
    fulfillment_method         varchar(16),
    requested_location_id      varchar(16),
    line_status                varchar(16),
    substitution_for_line_id   varchar(32),
    record_source              varchar(64),
    primary key (hk_order_line, load_dts)
);

create table if not exists omnichannel_oms_vault.s_allocation_state (
    hk_allocation           varchar(32) references omnichannel_oms_vault.h_allocation(hk_allocation),
    load_dts                timestamp,
    allocated_quantity      integer,
    estimated_cost_minor    bigint,
    estimated_ready_ts      timestamp,
    estimated_delivery_ts   timestamp,
    status                  varchar(16),
    record_source           varchar(64),
    primary key (hk_allocation, load_dts)
);

create table if not exists omnichannel_oms_vault.s_shipment_status (
    hk_shipment       varchar(32) references omnichannel_oms_vault.h_shipment(hk_shipment),
    load_dts          timestamp,
    carrier           varchar(16),
    service_level     varchar(32),
    weight_grams      integer,
    cost_minor        bigint,
    shipped_at        timestamp,
    delivered_at      timestamp,
    status            varchar(16),
    record_source     varchar(64),
    primary key (hk_shipment, load_dts)
);

create table if not exists omnichannel_oms_vault.s_rma_status (
    hk_rma                varchar(32) references omnichannel_oms_vault.h_rma(hk_rma),
    load_dts              timestamp,
    return_reason         varchar(32),
    return_method         varchar(16),
    refund_method         varchar(16),
    refund_amount_minor   bigint,
    restock_outcome       varchar(16),
    received_at           timestamp,
    refund_issued_at      timestamp,
    status                varchar(16),
    record_source         varchar(64),
    primary key (hk_rma, load_dts)
);

create table if not exists omnichannel_oms_vault.s_sourcing_rule (
    hk_rule                  varchar(32) references omnichannel_oms_vault.h_sourcing_rule(hk_rule),
    load_dts                 timestamp,
    rule_name                varchar(128),
    priority                 smallint,
    cost_weight              numeric(5,4),
    speed_weight             numeric(5,4),
    capacity_weight          numeric(5,4),
    clearance_pull_weight    numeric(5,4),
    effective_from           timestamp,
    effective_to             timestamp,
    status                   varchar(16),
    record_source            varchar(64),
    primary key (hk_rule, load_dts)
);
