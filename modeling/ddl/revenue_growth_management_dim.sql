-- =============================================================================
-- Revenue Growth Management — Kimball dimensional schema
-- Star: fct_price_events_rgm, fct_deals, fct_net_revenue, fct_mix_analysis
-- Conformed dims: dim_date_rgm, dim_product_rgm, dim_account_rgm, dim_pack,
--                 dim_price_list, dim_mix_segment
-- Suffix `_rgm` on collisions with other anchors (date, product, account).
-- =============================================================================

create schema if not exists revenue_growth_management_dim;

-- ---------- DIMS ----------
create table if not exists revenue_growth_management_dim.dim_date_rgm (
    date_key       integer primary key,        -- yyyymmdd
    cal_date       date,
    day_of_week    smallint,
    day_name       varchar(12),
    month          smallint,
    month_name     varchar(12),
    quarter        smallint,
    year           smallint,
    fiscal_year    smallint,
    fiscal_quarter smallint,
    is_weekend     boolean
);

create table if not exists revenue_growth_management_dim.dim_account_rgm (
    account_sk          bigint primary key,
    account_id          varchar(32) unique,
    account_name        varchar(255),
    parent_account_id   varchar(32),
    channel             varchar(32),
    channel_tier        varchar(16),
    country_iso2        varchar(2),
    gln                 varchar(13),
    status              varchar(16),
    valid_from          timestamp,
    valid_to            timestamp,
    is_current          boolean
);

create table if not exists revenue_growth_management_dim.dim_product_rgm (
    product_sk          bigint primary key,
    sku_id              varchar(32) unique,
    gtin                varchar(14),
    brand               varchar(64),
    sub_brand           varchar(64),
    category            varchar(64),
    subcategory         varchar(64),
    lifecycle_stage     varchar(16),
    innovation_flag     boolean,
    status              varchar(16)
);

create table if not exists revenue_growth_management_dim.dim_pack (
    pack_sk                       bigint primary key,
    pack_id                       varchar(32) unique,
    sku_id                        varchar(32),
    pack_name                     varchar(128),
    pack_size_count               smallint,
    pack_format                   varchar(32),
    ppa_tier                      varchar(16),
    ladder_rank                   smallint,
    benchmark_net_price_cents     bigint,
    benchmark_margin_cents        bigint,
    status                        varchar(16)
);

create table if not exists revenue_growth_management_dim.dim_price_list (
    price_list_sk       bigint primary key,
    price_list_id       varchar(40) unique,
    pack_id             varchar(32),
    account_id          varchar(32),
    list_price_cents    bigint,
    srp_cents           bigint,
    currency            varchar(3),
    effective_from      date,
    effective_to        date,
    source_system       varchar(32),
    is_current          boolean
);

create table if not exists revenue_growth_management_dim.dim_mix_segment (
    segment_sk                          bigint primary key,
    segment_id                          varchar(32) unique,
    channel                             varchar(32),
    ppa_tier                            varchar(16),
    category                            varchar(64),
    target_share_pct                    numeric(6,4),
    target_net_revenue_per_unit_cents   bigint
);

-- ---------- FACTS ----------
create table if not exists revenue_growth_management_dim.fct_price_events_rgm (
    price_event_id          varchar(40) primary key,
    date_key                integer references revenue_growth_management_dim.dim_date_rgm(date_key),
    account_sk              bigint  references revenue_growth_management_dim.dim_account_rgm(account_sk),
    pack_sk                 bigint  references revenue_growth_management_dim.dim_pack(pack_sk),
    event_type              varchar(16),
    prior_list_price_cents  bigint,
    new_list_price_cents    bigint,
    price_delta_cents       bigint,
    price_delta_pct         numeric(8,4),
    prior_srp_cents         bigint,
    new_srp_cents           bigint,
    currency                varchar(3),
    announced_at            timestamp,
    effective_from          date,
    source_system           varchar(32)
);

create table if not exists revenue_growth_management_dim.fct_deals (
    deal_id                    varchar(40) primary key,
    date_key                   integer references revenue_growth_management_dim.dim_date_rgm(date_key),
    account_sk                 bigint  references revenue_growth_management_dim.dim_account_rgm(account_sk),
    pack_sk                    bigint  references revenue_growth_management_dim.dim_pack(pack_sk),
    promo_plan_id              varchar(32),
    tactic_type                varchar(32),
    mechanic                   varchar(32),
    discount_per_unit_cents    bigint,
    rebate_pct                 numeric(6,4),
    deal_floor_cents           bigint,
    planned_units              bigint,
    planned_spend_cents        bigint,
    actual_units               bigint,
    actual_spend_cents         bigint,
    forward_buy_cost_cents     bigint,
    incremental_units          bigint,                 -- actual - baseline (joined in mart)
    incremental_revenue_cents  bigint,
    roi                        numeric(8,4),
    start_date                 date,
    end_date                   date,
    settlement_method          varchar(16),
    status                     varchar(16)
);

create table if not exists revenue_growth_management_dim.fct_net_revenue (
    transaction_id              varchar(40) primary key,
    date_key                    integer references revenue_growth_management_dim.dim_date_rgm(date_key),
    account_sk                  bigint  references revenue_growth_management_dim.dim_account_rgm(account_sk),
    pack_sk                     bigint  references revenue_growth_management_dim.dim_pack(pack_sk),
    deal_id                     varchar(40),
    units                       bigint,
    gross_revenue_cents         bigint,
    off_invoice_cents           bigint,
    rebate_accrual_cents        bigint,
    scan_down_cents             bigint,
    bill_back_cents             bigint,
    mcb_cents                   bigint,
    slotting_cents              bigint,
    marketing_dev_funds_cents   bigint,
    total_gtn_cents             bigint,                -- sum of trade lines (negative deltas)
    net_revenue_cents           bigint,                -- gross - total_gtn
    cogs_cents                  bigint,
    gross_margin_cents          bigint,                -- net_revenue - cogs
    price_realization           numeric(8,6),          -- net_revenue / gross_revenue (per row)
    currency                    varchar(3),
    invoice_date                date
);

create table if not exists revenue_growth_management_dim.fct_mix_analysis (
    mix_row_id                  varchar(40) primary key,
    date_key                    integer references revenue_growth_management_dim.dim_date_rgm(date_key),
    segment_sk                  bigint  references revenue_growth_management_dim.dim_mix_segment(segment_sk),
    account_sk                  bigint  references revenue_growth_management_dim.dim_account_rgm(account_sk),
    pack_sk                     bigint  references revenue_growth_management_dim.dim_pack(pack_sk),
    actual_units                bigint,
    plan_units                  bigint,
    actual_share_pct            numeric(8,6),
    plan_share_pct              numeric(8,6),
    actual_net_revenue_cents    bigint,
    plan_net_revenue_cents      bigint,
    volume_variance_cents       bigint,
    price_variance_cents        bigint,
    mix_variance_cents          bigint,
    residual_variance_cents     bigint
);

-- Helpful indexes.
create index if not exists ix_fct_price_evt_date     on revenue_growth_management_dim.fct_price_events_rgm(date_key);
create index if not exists ix_fct_price_evt_pack     on revenue_growth_management_dim.fct_price_events_rgm(pack_sk);
create index if not exists ix_fct_deal_date          on revenue_growth_management_dim.fct_deals(date_key);
create index if not exists ix_fct_deal_account_pack  on revenue_growth_management_dim.fct_deals(account_sk, pack_sk);
create index if not exists ix_fct_nr_date            on revenue_growth_management_dim.fct_net_revenue(date_key);
create index if not exists ix_fct_nr_account_pack    on revenue_growth_management_dim.fct_net_revenue(account_sk, pack_sk);
create index if not exists ix_fct_mix_segment        on revenue_growth_management_dim.fct_mix_analysis(segment_sk);
