-- =============================================================================
-- Omnichannel Order Management — 3NF schema
-- Source standards (verbatim where the spec names a field):
--   Manhattan Active Order Management — DOM, ATP, store fulfillment.
--   IBM Sterling Order Management — global inventory visibility, business rules.
--   Salesforce Order Management — Commerce Cloud OMS.
--   Shopify Admin GraphQL — fulfillmentOrder + inventoryLevel grain.
--   Oracle Retail Order Management Cloud Service (ROMS).
--   Fluent Commerce — event-sourced order state.
--   GS1 GTIN-14 / GLN; X12 EDI 940/943/944/945/846/856.
-- =============================================================================

create schema if not exists omnichannel_oms;

-- Unified customer (golden record).
create table if not exists omnichannel_oms.customer (
    customer_id        varchar(32) primary key,
    golden_record_id   varchar(32),
    email_hash         varchar(64),
    phone_hash         varchar(64),
    loyalty_id         varchar(32),
    home_country_iso2  varchar(2),
    created_at         timestamp,
    status             varchar(16)
);

-- Any inventory-holding / fulfilling node — store, DC, dark store, drop-ship, locker.
create table if not exists omnichannel_oms.location (
    location_id              varchar(16) primary key,
    gln                      varchar(13),                 -- GS1 Global Location Number
    name                     varchar(255),
    location_type            varchar(16),                 -- store|dc|dark_store|drop_ship|partner|locker
    country_iso2             varchar(2),
    region                   varchar(64),
    timezone                 varchar(32),
    lat                      numeric(9,6),
    lon                      numeric(9,6),
    bopis_enabled            boolean,
    ship_from_enabled        boolean,
    pick_capacity_per_hour   integer,
    status                   varchar(16)
);

-- SKU master mirrored from RMS.
create table if not exists omnichannel_oms.product (
    product_id                  varchar(32) primary key,
    gtin                        varchar(14),               -- GS1 GTIN-14
    sku                         varchar(32),
    name                        varchar(255),
    category_id                 varchar(32),
    hazmat_flag                 boolean,
    weight_grams                integer,
    dimensional_weight_grams    integer,
    pack_type                   varchar(16),
    status                      varchar(16)
);

-- Effective-dated quantity at a location × product. The atomic input to ATP.
create table if not exists omnichannel_oms.inventory_position (
    position_id            varchar(32) primary key,
    location_id            varchar(16) references omnichannel_oms.location(location_id),
    product_id             varchar(32) references omnichannel_oms.product(product_id),
    on_hand_units          integer,
    allocated_units        integer,
    in_transit_units       integer,
    reserved_safety_units  integer,
    atp_units              integer,
    source_system          varchar(32),                    -- Manhattan|Sterling|SFOMS|Shopify|RMS|Kibo|Fluent|WMS
    as_of_ts               timestamp,
    refresh_lag_seconds    integer
);

-- Order header. Capture channel + lifecycle state.
create table if not exists omnichannel_oms.oms_order (
    order_id               varchar(32) primary key,
    customer_id            varchar(32) references omnichannel_oms.customer(customer_id),
    capture_channel        varchar(16),                    -- web|app|store_pos|kiosk|call_center|marketplace|agent
    capture_location_id    varchar(16) references omnichannel_oms.location(location_id),
    order_total_minor      bigint,
    currency               varchar(3),
    tax_minor              bigint,
    shipping_minor         bigint,
    discount_minor         bigint,
    payment_status         varchar(16),
    order_status           varchar(16),
    promise_delivery_ts    timestamp,
    captured_at            timestamp,
    closed_at              timestamp
);

-- One SKU on an order — the fulfillment grain.
create table if not exists omnichannel_oms.order_line (
    order_line_id              varchar(32) primary key,
    order_id                   varchar(32) references omnichannel_oms.oms_order(order_id),
    product_id                 varchar(32) references omnichannel_oms.product(product_id),
    line_number                smallint,
    quantity                   integer,
    unit_price_minor           bigint,
    line_total_minor           bigint,
    fulfillment_method         varchar(16),                -- ship_to_home|bopis|sfs|curbside|delivery|drop_ship|same_day
    requested_location_id      varchar(16),                -- BOPIS pickup store
    line_status                varchar(16),
    substitution_for_line_id   varchar(32)
);

-- Sourcing rule fragment used by the DOM broker.
create table if not exists omnichannel_oms.sourcing_rule (
    rule_id                  varchar(32) primary key,
    rule_name                varchar(128),
    priority                 smallint,
    condition_json           text,                          -- vendor-neutral DSL
    cost_weight              numeric(5,4),
    speed_weight             numeric(5,4),
    capacity_weight          numeric(5,4),
    clearance_pull_weight    numeric(5,4),
    effective_from           timestamp,
    effective_to             timestamp,
    status                   varchar(16)
);

-- Allocation = order_line ↔ fulfillment node binding.
create table if not exists omnichannel_oms.allocation (
    allocation_id           varchar(32) primary key,
    order_line_id           varchar(32) references omnichannel_oms.order_line(order_line_id),
    location_id             varchar(16) references omnichannel_oms.location(location_id),
    rule_id                 varchar(32) references omnichannel_oms.sourcing_rule(rule_id),
    allocated_quantity      integer,
    estimated_cost_minor    bigint,
    estimated_ready_ts      timestamp,
    estimated_delivery_ts   timestamp,
    status                  varchar(16),                    -- issued|accepted|rejected|reallocated|completed
    allocated_at            timestamp
);

-- One state-transition event in the lifecycle of an allocation. Event-sourced.
create table if not exists omnichannel_oms.fulfillment_event (
    event_id          varchar(32) primary key,
    allocation_id     varchar(32) references omnichannel_oms.allocation(allocation_id),
    order_line_id     varchar(32) references omnichannel_oms.order_line(order_line_id),
    location_id       varchar(16) references omnichannel_oms.location(location_id),
    event_type        varchar(32),                          -- pick_started|pick_complete|substitution|short_pick|pack|label|ship|in_transit|out_for_delivery|delivered|pickup_ready|pickup_complete|cancel|reallocate|return_initiated|return_received|refund_issued
    occurred_at       timestamp,
    actor_role        varchar(16),                          -- system|store_associate|warehouse_picker|carrier|customer
    actor_id          varchar(32),
    payload_json      text
);

-- Physical parcel handed to a carrier; one-to-one with EDI 945.
create table if not exists omnichannel_oms.shipment (
    shipment_id              varchar(32) primary key,
    allocation_id            varchar(32) references omnichannel_oms.allocation(allocation_id),
    tracking_number          varchar(64),
    carrier                  varchar(16),                   -- fedex|ups|usps|dhl|store_courier|ontrac|lasership|same_day
    service_level            varchar(32),
    ship_from_location_id    varchar(16) references omnichannel_oms.location(location_id),
    ship_to_postal           varchar(16),
    ship_to_country_iso2     varchar(2),
    weight_grams             integer,
    cost_minor               bigint,
    shipped_at               timestamp,
    delivered_at             timestamp,
    status                   varchar(16)
);

-- Return Merchandise Authorization (RMA).
create table if not exists omnichannel_oms.return_authorization (
    rma_id                varchar(32) primary key,
    order_id              varchar(32) references omnichannel_oms.oms_order(order_id),
    customer_id           varchar(32) references omnichannel_oms.customer(customer_id),
    return_reason         varchar(32),
    return_method         varchar(16),                       -- in_store|mail|carrier_pickup|locker
    return_location_id    varchar(16) references omnichannel_oms.location(location_id),
    refund_method         varchar(16),                       -- original_tender|store_credit|gift_card|exchange
    refund_amount_minor   bigint,
    restock_outcome       varchar(16),                       -- restocked|damaged|donated|destroyed|return_to_vendor
    initiated_at          timestamp,
    received_at           timestamp,
    refund_issued_at      timestamp,
    status                varchar(16)
);

-- Helpful indexes on time and cardinality.
create index if not exists ix_oms_inv_loc_prod      on omnichannel_oms.inventory_position(location_id, product_id);
create index if not exists ix_oms_order_customer    on omnichannel_oms.oms_order(customer_id);
create index if not exists ix_oms_line_order        on omnichannel_oms.order_line(order_id);
create index if not exists ix_oms_alloc_line        on omnichannel_oms.allocation(order_line_id);
create index if not exists ix_oms_alloc_loc         on omnichannel_oms.allocation(location_id);
create index if not exists ix_oms_event_alloc       on omnichannel_oms.fulfillment_event(allocation_id);
create index if not exists ix_oms_event_type_ts     on omnichannel_oms.fulfillment_event(event_type, occurred_at);
create index if not exists ix_oms_shipment_alloc    on omnichannel_oms.shipment(allocation_id);
create index if not exists ix_oms_rma_order         on omnichannel_oms.return_authorization(order_id);
