-- =============================================================================
-- Category Management — Kimball dimensional schema
-- Facts: fct_syndicated_measurements, fct_distribution, fct_planogram_compliance,
--        fct_range_reviews
-- Conformed dims (with _cm suffix on collisions):
--        dim_date_cm, dim_product_cm, dim_store_cm, dim_category, dim_planogram,
--        dim_range_review
-- =============================================================================

create schema if not exists category_management_dim;

-- ---------- DIMS ----------
create table if not exists category_management_dim.dim_date_cm (
    date_key       integer primary key,        -- yyyymmdd
    cal_date       date,
    day_of_week    smallint,
    day_name       varchar(12),
    week_start_date date,
    week_of_year   smallint,
    month          smallint,
    month_name     varchar(12),
    quarter        smallint,
    year           smallint,
    fiscal_year    smallint,
    fiscal_quarter smallint,
    is_weekend     boolean
);

create table if not exists category_management_dim.dim_category (
    category_sk          bigint primary key,
    category_id          varchar(32) unique,
    category_name        varchar(128),
    parent_category_id   varchar(32),
    category_level       varchar(16),
    category_role        varchar(16),
    linear_ft_target     numeric(10,2),
    gpc_brick            varchar(16),
    status               varchar(16)
);

create table if not exists category_management_dim.dim_product_cm (
    product_sk            bigint primary key,
    sku_id                varchar(32) unique,
    gtin                  varchar(14),
    brand                 varchar(64),
    sub_brand             varchar(64),
    manufacturer          varchar(128),
    category_id           varchar(32),
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
    valid_from            timestamp,
    valid_to              timestamp,
    is_current            boolean
);

create table if not exists category_management_dim.dim_store_cm (
    store_sk            bigint primary key,
    store_id            varchar(32) unique,
    banner              varchar(64),
    gln                 varchar(13),
    country_iso2        varchar(2),
    state_region        varchar(8),
    postal_code         varchar(16),
    format              varchar(32),
    cluster_id          varchar(32),
    shopper_segment     varchar(32),
    total_linear_ft     numeric(10,2),
    status              varchar(16)
);

create table if not exists category_management_dim.dim_planogram (
    planogram_sk        bigint primary key,
    planogram_id        varchar(32) unique,
    category_id         varchar(32),
    cluster_id          varchar(32),
    version             varchar(16),
    effective_from      date,
    effective_to        date,
    total_linear_ft     numeric(10,2),
    total_facings       integer,
    total_sku_count     integer,
    authoring_system    varchar(32),
    status              varchar(16),
    is_current          boolean
);

create table if not exists category_management_dim.dim_range_review (
    range_review_sk     bigint primary key,
    range_review_id     varchar(32) unique,
    category_id         varchar(32),
    banner              varchar(64),
    cycle_name          varchar(128),
    scheduled_date      date,
    decision_date       date,
    in_market_date      date,
    status              varchar(16),
    led_by              varchar(64)
);

-- ---------- FACTS ----------
create table if not exists category_management_dim.fct_syndicated_measurements (
    measurement_id          varchar(40) primary key,
    date_key                integer references category_management_dim.dim_date_cm(date_key),
    product_sk              bigint  references category_management_dim.dim_product_cm(product_sk),
    store_sk                bigint  references category_management_dim.dim_store_cm(store_sk),
    category_sk             bigint  references category_management_dim.dim_category(category_sk),
    week_start_date         date,
    geography               varchar(32),
    units_sold              bigint,
    dollars_sold_cents      bigint,
    avg_retail_price_cents  bigint,
    market_share_pct        numeric(7,4),
    penetration_pct         numeric(7,4),
    buy_rate_units          numeric(10,2),
    any_promo_flag          boolean,
    source                  varchar(32),
    panel_id                varchar(16),
    projection_factor       numeric(8,4)
);

create table if not exists category_management_dim.fct_distribution (
    distribution_record_id  varchar(40) primary key,
    date_key                integer references category_management_dim.dim_date_cm(date_key),
    product_sk              bigint  references category_management_dim.dim_product_cm(product_sk),
    store_sk                bigint  references category_management_dim.dim_store_cm(store_sk),
    week_start_date         date,
    is_listed               boolean,
    is_on_shelf             boolean,
    acv_weight              numeric(8,4),
    mandated_flag           boolean,
    compliant_flag          boolean,
    source_doc              varchar(16)
);

create table if not exists category_management_dim.fct_planogram_compliance (
    audit_id                varchar(40) primary key,
    date_key                integer references category_management_dim.dim_date_cm(date_key),
    store_sk                bigint  references category_management_dim.dim_store_cm(store_sk),
    planogram_sk            bigint  references category_management_dim.dim_planogram(planogram_sk),
    audit_date              date,
    positions_audited       integer,
    positions_compliant     integer,
    compliance_pct          numeric(5,2),
    missing_facings         integer,
    out_of_stock_count      integer,
    misplaced_sku_count     integer,
    extra_sku_count         integer,
    source                  varchar(32)
);

create table if not exists category_management_dim.fct_range_reviews (
    range_review_id                 varchar(32) primary key,
    range_review_sk                 bigint  references category_management_dim.dim_range_review(range_review_sk),
    category_sk                     bigint  references category_management_dim.dim_category(category_sk),
    decision_date_key               integer references category_management_dim.dim_date_cm(date_key),
    banner                          varchar(64),
    sku_count_before                integer,
    sku_count_after                 integer,
    sku_adds                        integer,
    sku_drops                       integer,
    net_sku_delta                   integer,
    forecast_category_sales_delta_cents bigint,
    forecast_margin_delta_cents     bigint,
    status                          varchar(16)
);

-- Helpful indexes
create index if not exists ix_fct_meas_date     on category_management_dim.fct_syndicated_measurements(date_key);
create index if not exists ix_fct_meas_product  on category_management_dim.fct_syndicated_measurements(product_sk);
create index if not exists ix_fct_meas_category on category_management_dim.fct_syndicated_measurements(category_sk);
create index if not exists ix_fct_dist_date     on category_management_dim.fct_distribution(date_key);
create index if not exists ix_fct_dist_product  on category_management_dim.fct_distribution(product_sk);
create index if not exists ix_fct_audit_date    on category_management_dim.fct_planogram_compliance(date_key);
create index if not exists ix_fct_audit_pog     on category_management_dim.fct_planogram_compliance(planogram_sk);
create index if not exists ix_fct_rr_category   on category_management_dim.fct_range_reviews(category_sk);
