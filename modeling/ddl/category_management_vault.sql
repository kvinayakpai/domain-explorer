-- =============================================================================
-- Category Management — Data Vault 2.0 schema
-- Hubs (business keys) + Links (relationships) + Satellites (descriptive,
-- insert-only, time-stamped).
-- =============================================================================

create schema if not exists category_management_vault;

-- ---------- HUBS ----------
create table if not exists category_management_vault.h_category (
    hk_category    varchar(32) primary key,    -- MD5(category_id)
    category_id    varchar(32) unique,
    load_dts       timestamp,
    record_source  varchar(64)
);

create table if not exists category_management_vault.h_sku (
    hk_sku         varchar(32) primary key,
    sku_id         varchar(32) unique,
    load_dts       timestamp,
    record_source  varchar(64)
);

create table if not exists category_management_vault.h_store (
    hk_store       varchar(32) primary key,
    store_id       varchar(32) unique,
    load_dts       timestamp,
    record_source  varchar(64)
);

create table if not exists category_management_vault.h_planogram (
    hk_planogram   varchar(32) primary key,
    planogram_id   varchar(32) unique,
    load_dts       timestamp,
    record_source  varchar(64)
);

create table if not exists category_management_vault.h_range_review (
    hk_range_review    varchar(32) primary key,
    range_review_id    varchar(32) unique,
    load_dts           timestamp,
    record_source      varchar(64)
);

-- ---------- LINKS ----------
create table if not exists category_management_vault.l_sku_category (
    hk_link        varchar(32) primary key,
    hk_sku         varchar(32) references category_management_vault.h_sku(hk_sku),
    hk_category    varchar(32) references category_management_vault.h_category(hk_category),
    load_dts       timestamp,
    record_source  varchar(64)
);

create table if not exists category_management_vault.l_planogram_position (
    hk_link        varchar(32) primary key,
    hk_planogram   varchar(32) references category_management_vault.h_planogram(hk_planogram),
    hk_sku         varchar(32) references category_management_vault.h_sku(hk_sku),
    position_id    varchar(40),
    shelf_number   smallint,
    position_index smallint,
    facings        smallint,
    load_dts       timestamp,
    record_source  varchar(64)
);

create table if not exists category_management_vault.l_distribution (
    hk_link        varchar(32) primary key,
    hk_store       varchar(32) references category_management_vault.h_store(hk_store),
    hk_sku         varchar(32) references category_management_vault.h_sku(hk_sku),
    week_start_date date,
    load_dts       timestamp,
    record_source  varchar(64)
);

create table if not exists category_management_vault.l_syndicated (
    hk_link        varchar(32) primary key,
    hk_sku         varchar(32) references category_management_vault.h_sku(hk_sku),
    hk_store       varchar(32) references category_management_vault.h_store(hk_store),
    hk_category    varchar(32) references category_management_vault.h_category(hk_category),
    week_start_date date,
    source         varchar(32),
    load_dts       timestamp,
    record_source  varchar(64)
);

create table if not exists category_management_vault.l_range_decision (
    hk_link            varchar(32) primary key,
    hk_range_review    varchar(32) references category_management_vault.h_range_review(hk_range_review),
    hk_sku             varchar(32) references category_management_vault.h_sku(hk_sku),
    decision_type      varchar(16),
    load_dts           timestamp,
    record_source      varchar(64)
);

create table if not exists category_management_vault.l_compliance_audit (
    hk_link        varchar(32) primary key,
    hk_store       varchar(32) references category_management_vault.h_store(hk_store),
    hk_planogram   varchar(32) references category_management_vault.h_planogram(hk_planogram),
    audit_date     date,
    load_dts       timestamp,
    record_source  varchar(64)
);

-- ---------- SATELLITES ----------
create table if not exists category_management_vault.s_category_descriptive (
    hk_category        varchar(32) references category_management_vault.h_category(hk_category),
    load_dts           timestamp,
    category_name      varchar(128),
    parent_category_id varchar(32),
    category_level     varchar(16),
    category_role      varchar(16),
    linear_ft_target   numeric(10,2),
    gpc_brick          varchar(16),
    status             varchar(16),
    record_source      varchar(64),
    primary key (hk_category, load_dts)
);

create table if not exists category_management_vault.s_sku_descriptive (
    hk_sku                varchar(32) references category_management_vault.h_sku(hk_sku),
    load_dts              timestamp,
    gtin                  varchar(14),
    brand                 varchar(64),
    sub_brand             varchar(64),
    manufacturer          varchar(128),
    pack_size             varchar(32),
    case_pack_qty         smallint,
    width_cm              numeric(8,2),
    height_cm             numeric(8,2),
    depth_cm              numeric(8,2),
    list_price_cents      bigint,
    srp_cents             bigint,
    cost_of_goods_cents   bigint,
    private_label_flag    boolean,
    lifecycle_stage       varchar(16),
    status                varchar(16),
    record_source         varchar(64),
    primary key (hk_sku, load_dts)
);

create table if not exists category_management_vault.s_store_descriptive (
    hk_store         varchar(32) references category_management_vault.h_store(hk_store),
    load_dts         timestamp,
    banner           varchar(64),
    gln              varchar(13),
    country_iso2     varchar(2),
    state_region     varchar(8),
    format           varchar(32),
    cluster_id       varchar(32),
    shopper_segment  varchar(32),
    total_linear_ft  numeric(10,2),
    status           varchar(16),
    record_source    varchar(64),
    primary key (hk_store, load_dts)
);

create table if not exists category_management_vault.s_planogram_state (
    hk_planogram     varchar(32) references category_management_vault.h_planogram(hk_planogram),
    load_dts         timestamp,
    version          varchar(16),
    effective_from   date,
    effective_to     date,
    total_facings    integer,
    total_sku_count  integer,
    total_linear_ft  numeric(10,2),
    authoring_system varchar(32),
    status           varchar(16),
    record_source    varchar(64),
    primary key (hk_planogram, load_dts)
);

create table if not exists category_management_vault.s_distribution_metric (
    hk_link        varchar(32) references category_management_vault.l_distribution(hk_link),
    load_dts       timestamp,
    is_listed      boolean,
    is_on_shelf    boolean,
    acv_weight     numeric(8,4),
    mandated_flag  boolean,
    compliant_flag boolean,
    source_doc     varchar(16),
    record_source  varchar(64),
    primary key (hk_link, load_dts)
);

create table if not exists category_management_vault.s_syndicated_metric (
    hk_link                varchar(32) references category_management_vault.l_syndicated(hk_link),
    load_dts               timestamp,
    units_sold             bigint,
    dollars_sold_cents     bigint,
    avg_retail_price_cents bigint,
    market_share_pct       numeric(7,4),
    penetration_pct        numeric(7,4),
    buy_rate_units         numeric(10,2),
    any_promo_flag         boolean,
    projection_factor      numeric(8,4),
    record_source          varchar(64),
    primary key (hk_link, load_dts)
);

create table if not exists category_management_vault.s_range_review_state (
    hk_range_review                 varchar(32) references category_management_vault.h_range_review(hk_range_review),
    load_dts                        timestamp,
    cycle_name                      varchar(128),
    scheduled_date                  date,
    decision_date                   date,
    in_market_date                  date,
    sku_count_before                integer,
    sku_count_after                 integer,
    sku_adds                        integer,
    sku_drops                       integer,
    forecast_category_sales_delta_cents bigint,
    forecast_margin_delta_cents     bigint,
    status                          varchar(16),
    led_by                          varchar(64),
    record_source                   varchar(64),
    primary key (hk_range_review, load_dts)
);

create table if not exists category_management_vault.s_compliance_score (
    hk_link              varchar(32) references category_management_vault.l_compliance_audit(hk_link),
    load_dts             timestamp,
    positions_audited    integer,
    positions_compliant  integer,
    missing_facings      integer,
    out_of_stock_count   integer,
    misplaced_sku_count  integer,
    extra_sku_count      integer,
    compliance_score     numeric(5,2),
    source               varchar(32),
    record_source        varchar(64),
    primary key (hk_link, load_dts)
);
