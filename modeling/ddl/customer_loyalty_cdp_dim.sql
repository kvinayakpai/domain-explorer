-- =============================================================================
-- Customer Loyalty & CDP — Kimball dimensional schema
-- Star: fct_events_cdp, fct_segment_memberships, fct_loyalty_points_ledger,
--       fct_redemptions
-- Conformed dims: dim_customer_cdp, dim_date_cdp, dim_segment,
--                 dim_loyalty_tier, dim_reward, dim_channel
-- Suffix `_cdp` avoids collisions with merchandising / loyalty / customer_analytics dims.
-- =============================================================================

create schema if not exists customer_loyalty_cdp_dim;

-- ---------- DIMS ----------
create table if not exists customer_loyalty_cdp_dim.dim_date_cdp (
    date_key       integer primary key,    -- yyyymmdd
    cal_date       date,
    day_of_week    smallint,
    day_name       varchar(12),
    month          smallint,
    month_name     varchar(12),
    quarter        smallint,
    year           smallint,
    is_weekend     boolean
);

create table if not exists customer_loyalty_cdp_dim.dim_customer_cdp (
    customer_sk              bigint primary key,
    customer_id              varchar(32) unique,
    email_sha256             varchar(64),
    phone_sha256             varchar(64),
    country_iso2             varchar(2),
    postal_code              varchar(16),
    lifecycle_stage          varchar(16),
    rfm_recency              smallint,
    rfm_frequency            smallint,
    rfm_monetary             smallint,
    predicted_clv            numeric(12,2),
    predicted_churn_prob     numeric(5,4),
    golden_record_source     varchar(32),
    confidence_score         numeric(5,4),
    resolution_method        varchar(16),
    status                   varchar(16),
    valid_from               timestamp,
    valid_to                 timestamp,
    is_current               boolean
);

create table if not exists customer_loyalty_cdp_dim.dim_segment (
    segment_sk               bigint primary key,
    segment_id               varchar(32) unique,
    segment_name             varchar(128),
    segment_kind             varchar(24),
    refresh_cadence          varchar(16),
    owning_team              varchar(64),
    status                   varchar(16)
);

create table if not exists customer_loyalty_cdp_dim.dim_loyalty_tier (
    tier_sk          smallint primary key,
    tier_code        varchar(16) unique,
    tier_rank        smallint,
    min_spend_minor  bigint,
    earn_multiplier  numeric(4,2)
);

create table if not exists customer_loyalty_cdp_dim.dim_reward (
    reward_sk                bigint primary key,
    reward_id                varchar(32) unique,
    reward_name              varchar(255),
    reward_type              varchar(24),
    points_cost              integer,
    cash_equivalent_minor    bigint,
    vendor                   varchar(64),
    status                   varchar(16)
);

create table if not exists customer_loyalty_cdp_dim.dim_channel (
    channel_sk    smallint primary key,
    channel_code  varchar(16) unique,         -- web|app|email|push|sms|in_store|call_center|chat
    is_owned      boolean,
    is_paid       boolean
);

-- ---------- FACTS ----------
create table if not exists customer_loyalty_cdp_dim.fct_events_cdp (
    event_id                 varchar(64) primary key,
    date_key                 integer references customer_loyalty_cdp_dim.dim_date_cdp(date_key),
    customer_sk              bigint  references customer_loyalty_cdp_dim.dim_customer_cdp(customer_sk),
    channel_sk               smallint references customer_loyalty_cdp_dim.dim_channel(channel_sk),
    event_type               varchar(32),
    source_system            varchar(32),
    campaign_id              varchar(32),
    journey_id               varchar(32),
    product_id               varchar(32),
    order_id                 varchar(32),
    amount_minor             bigint,
    currency                 varchar(3),
    amount_usd               numeric(15,4),
    is_purchase              boolean,
    is_engagement            boolean,
    is_marketing_send        boolean,
    event_ts                 timestamp,
    ingest_lag_seconds       integer
);

create table if not exists customer_loyalty_cdp_dim.fct_segment_memberships (
    membership_id            varchar(64) primary key,
    date_key                 integer references customer_loyalty_cdp_dim.dim_date_cdp(date_key),
    customer_sk              bigint  references customer_loyalty_cdp_dim.dim_customer_cdp(customer_sk),
    segment_sk               bigint  references customer_loyalty_cdp_dim.dim_segment(segment_sk),
    entered_at               timestamp,
    exited_at                timestamp,
    duration_seconds         bigint,
    entry_reason             varchar(64),
    is_current               boolean
);

create table if not exists customer_loyalty_cdp_dim.fct_loyalty_points_ledger (
    ledger_id                varchar(64) primary key,
    date_key                 integer references customer_loyalty_cdp_dim.dim_date_cdp(date_key),
    customer_sk              bigint  references customer_loyalty_cdp_dim.dim_customer_cdp(customer_sk),
    tier_sk                  smallint references customer_loyalty_cdp_dim.dim_loyalty_tier(tier_sk),
    loyalty_account_id       varchar(32),
    txn_type                 varchar(16),
    points_delta             bigint,
    cash_equivalent_minor    bigint,
    campaign_code            varchar(32),
    is_earn                  boolean,
    is_redeem                boolean,
    is_expire                boolean,
    is_adjust                boolean,
    txn_ts                   timestamp,
    posted_ts                timestamp
);

create table if not exists customer_loyalty_cdp_dim.fct_redemptions (
    redemption_id            varchar(32) primary key,
    date_key                 integer references customer_loyalty_cdp_dim.dim_date_cdp(date_key),
    customer_sk              bigint  references customer_loyalty_cdp_dim.dim_customer_cdp(customer_sk),
    reward_sk                bigint  references customer_loyalty_cdp_dim.dim_reward(reward_sk),
    channel_sk               smallint references customer_loyalty_cdp_dim.dim_channel(channel_sk),
    tier_sk                  smallint references customer_loyalty_cdp_dim.dim_loyalty_tier(tier_sk),
    loyalty_account_id       varchar(32),
    points_spent             integer,
    cash_equivalent_minor    bigint,
    is_fulfilled             boolean,
    is_reversed              boolean,
    requested_at             timestamp,
    fulfilled_at             timestamp,
    fulfilment_lag_seconds   integer
);

-- Helpful indexes
create index if not exists ix_fct_events_date     on customer_loyalty_cdp_dim.fct_events_cdp(date_key);
create index if not exists ix_fct_events_cust     on customer_loyalty_cdp_dim.fct_events_cdp(customer_sk);
create index if not exists ix_fct_segmem_cust     on customer_loyalty_cdp_dim.fct_segment_memberships(customer_sk);
create index if not exists ix_fct_segmem_seg      on customer_loyalty_cdp_dim.fct_segment_memberships(segment_sk);
create index if not exists ix_fct_ledger_cust     on customer_loyalty_cdp_dim.fct_loyalty_points_ledger(customer_sk);
create index if not exists ix_fct_ledger_date     on customer_loyalty_cdp_dim.fct_loyalty_points_ledger(date_key);
create index if not exists ix_fct_redemp_cust     on customer_loyalty_cdp_dim.fct_redemptions(customer_sk);
