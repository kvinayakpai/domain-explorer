-- =============================================================================
-- Merchandising — Data Vault 2.0 (excerpt)
-- Hubs / Links / Satellites for SKU, store, supplier, sales.
-- =============================================================================

create schema if not exists merchandising_vault;

-- Hubs
create table if not exists merchandising_vault.hub_sku (
    sku_hk               bytea primary key,
    sku_bk               varchar not null,
    load_dts             timestamp not null,
    rec_src              varchar not null
);

create table if not exists merchandising_vault.hub_store (
    store_hk             bytea primary key,
    store_bk             varchar not null,
    load_dts             timestamp not null,
    rec_src              varchar not null
);

create table if not exists merchandising_vault.hub_supplier (
    supplier_hk          bytea primary key,
    supplier_bk          varchar not null,
    load_dts             timestamp not null,
    rec_src              varchar not null
);

create table if not exists merchandising_vault.hub_promotion (
    promotion_hk         bytea primary key,
    promotion_bk         varchar not null,
    load_dts             timestamp not null,
    rec_src              varchar not null
);

create table if not exists merchandising_vault.hub_purchase_order (
    po_hk                bytea primary key,
    po_bk                varchar not null,
    load_dts             timestamp not null,
    rec_src              varchar not null
);

create table if not exists merchandising_vault.hub_customer (
    customer_hk          bytea primary key,
    customer_bk          varchar not null,
    load_dts             timestamp not null,
    rec_src              varchar not null
);

-- Links
create table if not exists merchandising_vault.link_sku_supplier (
    link_hk              bytea primary key,
    sku_hk               bytea not null references merchandising_vault.hub_sku(sku_hk),
    supplier_hk          bytea not null references merchandising_vault.hub_supplier(supplier_hk),
    load_dts             timestamp not null,
    rec_src              varchar not null
);

create table if not exists merchandising_vault.link_po_line (
    link_hk              bytea primary key,
    po_hk                bytea not null references merchandising_vault.hub_purchase_order(po_hk),
    sku_hk               bytea not null references merchandising_vault.hub_sku(sku_hk),
    supplier_hk          bytea not null references merchandising_vault.hub_supplier(supplier_hk),
    line_no              smallint not null,
    load_dts             timestamp not null,
    rec_src              varchar not null
);

create table if not exists merchandising_vault.link_inventory_position (
    link_hk              bytea primary key,
    sku_hk               bytea not null references merchandising_vault.hub_sku(sku_hk),
    store_hk             bytea not null references merchandising_vault.hub_store(store_hk),
    snapshot_date        date not null,
    load_dts             timestamp not null,
    rec_src              varchar not null
);

create table if not exists merchandising_vault.link_sales_line (
    link_hk              bytea primary key,
    sku_hk               bytea not null references merchandising_vault.hub_sku(sku_hk),
    store_hk             bytea not null references merchandising_vault.hub_store(store_hk),
    customer_hk          bytea references merchandising_vault.hub_customer(customer_hk),
    promotion_hk         bytea references merchandising_vault.hub_promotion(promotion_hk),
    tx_bk                varchar not null,
    line_no              smallint not null,
    load_dts             timestamp not null,
    rec_src              varchar not null
);

-- Satellites
create table if not exists merchandising_vault.sat_sku_descriptive (
    sku_hk               bytea not null references merchandising_vault.hub_sku(sku_hk),
    load_dts             timestamp not null,
    load_end_dts         timestamp,
    hash_diff            bytea not null,
    upc                  varchar(14),
    style_id             varchar not null,
    color_code           varchar(16),
    size_code            varchar(16),
    description          varchar,
    rec_src              varchar not null,
    primary key (sku_hk, load_dts)
);

create table if not exists merchandising_vault.sat_sku_pricing (
    sku_hk               bytea not null references merchandising_vault.hub_sku(sku_hk),
    load_dts             timestamp not null,
    load_end_dts         timestamp,
    hash_diff            bytea not null,
    list_price           numeric(10, 2) not null,
    cost_amount          numeric(12, 4) not null,
    rec_src              varchar not null,
    primary key (sku_hk, load_dts)
);

create table if not exists merchandising_vault.sat_store_descriptive (
    store_hk             bytea not null references merchandising_vault.hub_store(store_hk),
    load_dts             timestamp not null,
    load_end_dts         timestamp,
    hash_diff            bytea not null,
    store_name           varchar not null,
    region_code          varchar(8) not null,
    cluster_code         varchar(8),
    open_date            date not null,
    rec_src              varchar not null,
    primary key (store_hk, load_dts)
);

create table if not exists merchandising_vault.sat_inventory_position (
    link_hk              bytea not null,
    load_dts             timestamp not null,
    load_end_dts         timestamp,
    hash_diff            bytea not null,
    on_hand_qty          integer not null,
    on_order_qty         integer not null,
    in_transit_qty       integer not null,
    rec_src              varchar not null,
    primary key (link_hk, load_dts)
);

create table if not exists merchandising_vault.sat_sales_line_state (
    link_hk              bytea not null,
    load_dts             timestamp not null,
    load_end_dts         timestamp,
    hash_diff            bytea not null,
    quantity             integer not null,
    unit_price           numeric(10, 2) not null,
    discount_amount      numeric(10, 2) not null,
    rec_src              varchar not null,
    primary key (link_hk, load_dts)
);
