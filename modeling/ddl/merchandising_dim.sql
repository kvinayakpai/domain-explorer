-- =============================================================================
-- Merchandising — dimensional mart (excerpt)
-- Star schema for sales, inventory, and markdown analytics.
-- =============================================================================

create schema if not exists merchandising_dim;

create table if not exists merchandising_dim.dim_date (
    date_key             integer primary key,
    date_actual          date not null,
    day_of_week          smallint not null,
    week_of_year         smallint not null,
    fiscal_period        varchar(8),
    fiscal_quarter       varchar(8),
    season_code          varchar(8)
);

create table if not exists merchandising_dim.dim_sku (
    sku_key              bigint primary key,
    sku_id               varchar not null,
    upc                  varchar(14),
    style_id             varchar not null,
    style_name           varchar not null,
    brand_name           varchar not null,
    department_name      varchar not null,
    class_name           varchar not null,
    subclass_name        varchar not null,
    color_code           varchar(16),
    size_code            varchar(16),
    is_private_label     boolean not null,
    valid_from           timestamp not null,
    valid_to             timestamp,
    is_current           boolean not null
);

create table if not exists merchandising_dim.dim_store (
    store_key            bigint primary key,
    store_id             varchar not null,
    store_name           varchar not null,
    region_code          varchar(8) not null,
    cluster_code         varchar(8),
    open_date            date not null,
    valid_from           timestamp not null,
    valid_to             timestamp,
    is_current           boolean not null
);

create table if not exists merchandising_dim.dim_promotion (
    promotion_key        bigint primary key,
    promo_id             varchar not null,
    promo_name           varchar not null,
    promo_type           varchar(16) not null,
    valid_from           date not null,
    valid_to             date not null
);

create table if not exists merchandising_dim.dim_supplier (
    supplier_key         bigint primary key,
    supplier_id          varchar not null,
    supplier_name        varchar not null,
    country_iso2         varchar(2)
);

create table if not exists merchandising_dim.dim_channel (
    channel_key          smallint primary key,
    channel_code         varchar(16) not null,
    channel_name         varchar(32) not null
);

create table if not exists merchandising_dim.dim_customer (
    customer_key         bigint primary key,
    customer_id          varchar not null,
    loyalty_tier         varchar(16),
    enrolled_date        date,
    valid_from           timestamp not null,
    valid_to             timestamp,
    is_current           boolean not null
);

create table if not exists merchandising_dim.fact_sales_daily (
    date_key             integer not null references merchandising_dim.dim_date(date_key),
    sku_key              bigint not null references merchandising_dim.dim_sku(sku_key),
    store_key            bigint not null references merchandising_dim.dim_store(store_key),
    channel_key          smallint not null references merchandising_dim.dim_channel(channel_key),
    promotion_key        bigint references merchandising_dim.dim_promotion(promotion_key),
    units_sold           integer not null,
    gross_sales          numeric(14, 2) not null,
    discount_amount      numeric(14, 2) not null,
    net_sales            numeric(14, 2) not null,
    cogs_amount          numeric(14, 2) not null,
    gross_margin         numeric(14, 2) not null,
    primary key (date_key, sku_key, store_key, channel_key)
);

create table if not exists merchandising_dim.fact_inventory_snapshot (
    date_key             integer not null references merchandising_dim.dim_date(date_key),
    sku_key              bigint not null references merchandising_dim.dim_sku(sku_key),
    store_key            bigint not null references merchandising_dim.dim_store(store_key),
    on_hand_qty          integer not null,
    on_order_qty         integer not null,
    in_transit_qty       integer not null,
    weeks_of_supply      numeric(8, 2),
    primary key (date_key, sku_key, store_key)
);

create table if not exists merchandising_dim.fact_markdown (
    date_key             integer not null references merchandising_dim.dim_date(date_key),
    sku_key              bigint not null references merchandising_dim.dim_sku(sku_key),
    store_key            bigint references merchandising_dim.dim_store(store_key),
    markdown_pct         numeric(5, 2) not null,
    units_at_markdown    integer not null,
    markdown_dollars     numeric(14, 2) not null
);

create table if not exists merchandising_dim.fact_returns (
    date_key             integer not null references merchandising_dim.dim_date(date_key),
    sku_key              bigint not null references merchandising_dim.dim_sku(sku_key),
    store_key            bigint not null references merchandising_dim.dim_store(store_key),
    units_returned       integer not null,
    refund_amount        numeric(14, 2) not null
);
