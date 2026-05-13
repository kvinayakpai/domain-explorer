-- =============================================================================
-- Returns & Reverse Logistics — Kimball dimensional schema
-- Star: fct_returns_rrl, fct_refunds_rrl, fct_refurb_outcomes, fct_liquidation_lots
-- Conformed dims: dim_date_rrl, dim_customer_rrl, dim_product_rrl,
--                 dim_reason_code, dim_disposition.
-- "_rrl" suffix avoids collisions with payments/merchandising/OMS dims.
-- =============================================================================

create schema if not exists returns_reverse_logistics_dim;

-- ---------- DIMS ----------
create table if not exists returns_reverse_logistics_dim.dim_date_rrl (
    date_key       integer primary key,                          -- yyyymmdd
    cal_date       date,
    day_of_week    smallint,
    day_name       varchar(12),
    month          smallint,
    month_name     varchar(12),
    quarter        smallint,
    year           smallint,
    is_weekend     boolean
);

create table if not exists returns_reverse_logistics_dim.dim_customer_rrl (
    customer_sk              bigint primary key,
    customer_id              varchar(32) unique,
    customer_ref_hash        varchar(64),
    country_iso2             varchar(2),
    loyalty_tier             varchar(16),
    lifetime_orders          integer,
    lifetime_returns         integer,
    chronic_returner_flag    boolean,
    chronic_returner_score   numeric(5,3),
    status                   varchar(16),
    valid_from               timestamp,
    valid_to                 timestamp,
    is_current               boolean
);

create table if not exists returns_reverse_logistics_dim.dim_product_rrl (
    product_sk     bigint primary key,
    sku_id         varchar(32) unique,
    gtin           varchar(14),
    category       varchar(64),
    unit_cogs_minor   bigint,
    unit_retail_minor bigint
);

create table if not exists returns_reverse_logistics_dim.dim_reason_code (
    reason_code_sk        bigint primary key,
    reason_code_id        varchar(16) unique,
    reason_code           varchar(32),
    reason_category       varchar(32),
    customer_facing_text  varchar(255),
    defect_attribution    varchar(32),
    actionable            boolean,
    severity              varchar(8)
);

create table if not exists returns_reverse_logistics_dim.dim_disposition (
    disposition_sk        bigint primary key,
    disposition_id        varchar(16) unique,
    disposition_code      varchar(32),
    disposition_name      varchar(64),
    target_channel        varchar(32),
    typical_recovery_pct  numeric(5,3),
    lane_owner            varchar(64)
);

create table if not exists returns_reverse_logistics_dim.dim_carrier_rrl (
    carrier_sk   smallint primary key,
    carrier      varchar(16) unique,
    description  varchar(128)
);

-- ---------- FACTS ----------
-- fct_returns_rrl — one row per return_item (the disposition grain).
create table if not exists returns_reverse_logistics_dim.fct_returns_rrl (
    return_item_id           varchar(32) primary key,
    rma_id                   varchar(32),
    date_key                 integer references returns_reverse_logistics_dim.dim_date_rrl(date_key),
    customer_sk              bigint  references returns_reverse_logistics_dim.dim_customer_rrl(customer_sk),
    product_sk               bigint  references returns_reverse_logistics_dim.dim_product_rrl(product_sk),
    reason_code_sk           bigint  references returns_reverse_logistics_dim.dim_reason_code(reason_code_sk),
    disposition_sk           bigint  references returns_reverse_logistics_dim.dim_disposition(disposition_sk),
    quantity                 integer,
    unit_cogs_minor          bigint,
    unit_retail_minor        bigint,
    cogs_usd                 numeric(15,4),
    retail_usd               numeric(15,4),
    condition_grade          varchar(8),
    return_method            varchar(32),
    return_platform          varchar(32),
    cross_border             boolean,
    is_fraud_flagged         boolean,
    days_to_disposition      integer,
    rma_issued_at            timestamp,
    received_at              timestamp,
    disposition_decided_at   timestamp
);

-- fct_refunds_rrl — one row per refund event.
create table if not exists returns_reverse_logistics_dim.fct_refunds_rrl (
    refund_id                       varchar(32) primary key,
    date_key                        integer references returns_reverse_logistics_dim.dim_date_rrl(date_key),
    customer_sk                     bigint  references returns_reverse_logistics_dim.dim_customer_rrl(customer_sk),
    order_id                        varchar(32),
    rma_id                          varchar(32),
    refund_type                     varchar(16),
    refund_amount_minor             bigint,
    refund_amount_usd               numeric(15,4),
    restocking_fee_collected_minor  bigint,
    currency                        varchar(3),
    payment_rail                    varchar(16),
    psp_refund_id                   varchar(64),
    is_returnless                   boolean,
    issue_latency_hours             numeric(10,3),
    issued_at                       timestamp,
    status                          varchar(16)
);

-- fct_refurb_outcomes — one row per refurb attempt (CRC).
create table if not exists returns_reverse_logistics_dim.fct_refurb_outcomes (
    refurb_outcome_id              varchar(32) primary key,
    date_key                       integer references returns_reverse_logistics_dim.dim_date_rrl(date_key),
    return_item_id                 varchar(32),
    product_sk                     bigint  references returns_reverse_logistics_dim.dim_product_rrl(product_sk),
    crc_id                         varchar(16),
    started_at                     timestamp,
    completed_at                   timestamp,
    cycle_hours                    numeric(10,3),
    labor_minutes                  integer,
    parts_cost_minor               bigint,
    outcome                        varchar(32),
    post_refurb_grade              varchar(8),
    post_refurb_resale_value_minor bigint,
    refurbed_to_resellable         boolean
);

-- fct_liquidation_lots — one row per sold lot.
create table if not exists returns_reverse_logistics_dim.fct_liquidation_lots (
    lot_id              varchar(32) primary key,
    date_key            integer references returns_reverse_logistics_dim.dim_date_rrl(date_key),
    marketplace         varchar(32),
    item_count          integer,
    total_cogs_minor    bigint,
    proceeds_minor      bigint,
    recovery_pct        numeric(6,4),
    currency            varchar(3),
    buyer_country_iso2  varchar(2),
    listed_at           timestamp,
    sold_at             timestamp,
    auction_days        integer
);

-- ---------- INDEXES ----------
create index if not exists ix_fct_ret_date     on returns_reverse_logistics_dim.fct_returns_rrl(date_key);
create index if not exists ix_fct_ret_cust     on returns_reverse_logistics_dim.fct_returns_rrl(customer_sk);
create index if not exists ix_fct_ret_disp     on returns_reverse_logistics_dim.fct_returns_rrl(disposition_sk);
create index if not exists ix_fct_ret_reason   on returns_reverse_logistics_dim.fct_returns_rrl(reason_code_sk);
create index if not exists ix_fct_refund_date  on returns_reverse_logistics_dim.fct_refunds_rrl(date_key);
create index if not exists ix_fct_refund_cust  on returns_reverse_logistics_dim.fct_refunds_rrl(customer_sk);
create index if not exists ix_fct_refurb_date  on returns_reverse_logistics_dim.fct_refurb_outcomes(date_key);
create index if not exists ix_fct_lot_date     on returns_reverse_logistics_dim.fct_liquidation_lots(date_key);
