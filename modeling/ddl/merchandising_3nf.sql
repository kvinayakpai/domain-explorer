-- =============================================================================
-- Merchandising — 3NF schema (excerpt)
-- Assortment, pricing, inventory, allocation, replenishment.
-- =============================================================================

create schema if not exists merchandising_3nf;

create table if not exists merchandising_3nf.product_hierarchy (
    department_id        varchar primary key,
    department_name      varchar not null
);

create table if not exists merchandising_3nf.class (
    class_id             varchar primary key,
    department_id        varchar not null references merchandising_3nf.product_hierarchy(department_id),
    class_name           varchar not null
);

create table if not exists merchandising_3nf.subclass (
    subclass_id          varchar primary key,
    class_id             varchar not null references merchandising_3nf.class(class_id),
    subclass_name        varchar not null
);

create table if not exists merchandising_3nf.sku (
    sku_id               varchar primary key,
    style_id             varchar not null,
    subclass_id          varchar not null references merchandising_3nf.subclass(subclass_id),
    color_code           varchar(16),
    size_code            varchar(16),
    upc                  varchar(14),
    description          varchar,
    is_active            boolean not null default true
);

create table if not exists merchandising_3nf.style (
    style_id             varchar primary key,
    style_name           varchar not null,
    brand_id             varchar not null,
    season_code          varchar(8) not null
);

create table if not exists merchandising_3nf.brand (
    brand_id             varchar primary key,
    brand_name           varchar not null,
    is_private_label     boolean not null default false
);

create table if not exists merchandising_3nf.supplier (
    supplier_id          varchar primary key,
    supplier_name        varchar not null,
    country_iso2         varchar(2),
    payment_terms        varchar(16)
);

create table if not exists merchandising_3nf.sku_supplier (
    sku_id               varchar not null references merchandising_3nf.sku(sku_id),
    supplier_id          varchar not null references merchandising_3nf.supplier(supplier_id),
    cost_amount          numeric(12, 4) not null,
    moq                  integer not null,
    lead_time_days       smallint not null,
    primary key (sku_id, supplier_id)
);

create table if not exists merchandising_3nf.store (
    store_id             varchar primary key,
    store_name           varchar not null,
    region_code          varchar(8) not null,
    cluster_code         varchar(8),
    open_date            date not null
);

create table if not exists merchandising_3nf.distribution_center (
    dc_id                varchar primary key,
    dc_name              varchar not null,
    region_code          varchar(8) not null
);

create table if not exists merchandising_3nf.price (
    price_id             varchar primary key,
    sku_id               varchar not null references merchandising_3nf.sku(sku_id),
    store_id             varchar references merchandising_3nf.store(store_id),
    price_type           varchar(16) not null,
    price_amount         numeric(10, 2) not null,
    valid_from           date not null,
    valid_to             date
);

create table if not exists merchandising_3nf.promotion (
    promo_id             varchar primary key,
    promo_name           varchar not null,
    promo_type           varchar(16) not null,
    valid_from           date not null,
    valid_to             date not null
);

create table if not exists merchandising_3nf.promotion_sku (
    promo_id             varchar not null references merchandising_3nf.promotion(promo_id),
    sku_id               varchar not null references merchandising_3nf.sku(sku_id),
    discount_pct         numeric(5, 2) not null,
    primary key (promo_id, sku_id)
);

create table if not exists merchandising_3nf.purchase_order (
    po_id                varchar primary key,
    supplier_id          varchar not null references merchandising_3nf.supplier(supplier_id),
    placed_at            timestamp not null,
    expected_delivery    date,
    status               varchar(16) not null
);

create table if not exists merchandising_3nf.purchase_order_line (
    po_line_id           varchar primary key,
    po_id                varchar not null references merchandising_3nf.purchase_order(po_id),
    sku_id               varchar not null references merchandising_3nf.sku(sku_id),
    ordered_qty          integer not null,
    unit_cost            numeric(12, 4) not null
);

create table if not exists merchandising_3nf.allocation (
    allocation_id        varchar primary key,
    sku_id               varchar not null references merchandising_3nf.sku(sku_id),
    store_id             varchar not null references merchandising_3nf.store(store_id),
    dc_id                varchar references merchandising_3nf.distribution_center(dc_id),
    allocated_qty        integer not null,
    allocated_at         timestamp not null
);

create table if not exists merchandising_3nf.inventory_position (
    sku_id               varchar not null references merchandising_3nf.sku(sku_id),
    store_id             varchar not null references merchandising_3nf.store(store_id),
    snapshot_date        date not null,
    on_hand_qty          integer not null,
    on_order_qty         integer not null,
    in_transit_qty       integer not null,
    primary key (sku_id, store_id, snapshot_date)
);

create table if not exists merchandising_3nf.sales_transaction (
    tx_id                varchar primary key,
    store_id             varchar not null references merchandising_3nf.store(store_id),
    tx_ts                timestamp not null,
    customer_id          varchar,
    payment_method       varchar(16) not null,
    total_amount         numeric(12, 2) not null
);

create table if not exists merchandising_3nf.sales_line (
    tx_id                varchar not null references merchandising_3nf.sales_transaction(tx_id),
    line_no              smallint not null,
    sku_id               varchar not null references merchandising_3nf.sku(sku_id),
    quantity             integer not null,
    unit_price           numeric(10, 2) not null,
    discount_amount      numeric(10, 2) not null default 0,
    primary key (tx_id, line_no)
);

create table if not exists merchandising_3nf.markdown_event (
    markdown_id          varchar primary key,
    sku_id               varchar not null references merchandising_3nf.sku(sku_id),
    store_id             varchar references merchandising_3nf.store(store_id),
    markdown_pct         numeric(5, 2) not null,
    effective_at         timestamp not null
);

create table if not exists merchandising_3nf.return_transaction (
    return_id            varchar primary key,
    original_tx_id       varchar references merchandising_3nf.sales_transaction(tx_id),
    sku_id               varchar not null references merchandising_3nf.sku(sku_id),
    store_id             varchar not null references merchandising_3nf.store(store_id),
    return_ts            timestamp not null,
    quantity             integer not null,
    refund_amount        numeric(10, 2) not null,
    reason_code          varchar(16)
);
