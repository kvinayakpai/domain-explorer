-- =============================================================================
-- Customer Loyalty & CDP — Data Vault 2.0 schema
-- Hubs (business keys) + Links (relationships) + Satellites (descriptive,
-- insert-only, time-stamped). Identity-graph edges captured as Links.
-- =============================================================================

create schema if not exists customer_loyalty_cdp_vault;

-- ---------- HUBS ----------
create table if not exists customer_loyalty_cdp_vault.h_customer (
    hk_customer    varchar(32) primary key,    -- MD5(customer_id)
    customer_id    varchar(32) unique,
    load_dts       timestamp,
    record_source  varchar(64)
);

create table if not exists customer_loyalty_cdp_vault.h_identity (
    hk_identity              varchar(32) primary key,
    identity_id              varchar(64) unique,
    identifier_type          varchar(24),
    load_dts                 timestamp,
    record_source            varchar(64)
);

create table if not exists customer_loyalty_cdp_vault.h_segment (
    hk_segment     varchar(32) primary key,
    segment_id     varchar(32) unique,
    load_dts       timestamp,
    record_source  varchar(64)
);

create table if not exists customer_loyalty_cdp_vault.h_loyalty_account (
    hk_loyalty_account   varchar(32) primary key,
    loyalty_account_id   varchar(32) unique,
    program_code         varchar(32),
    load_dts             timestamp,
    record_source        varchar(64)
);

create table if not exists customer_loyalty_cdp_vault.h_reward (
    hk_reward      varchar(32) primary key,
    reward_id      varchar(32) unique,
    load_dts       timestamp,
    record_source  varchar(64)
);

create table if not exists customer_loyalty_cdp_vault.h_event (
    hk_event       varchar(32) primary key,
    event_id       varchar(64) unique,
    load_dts       timestamp,
    record_source  varchar(64)
);

-- ---------- LINKS ----------
create table if not exists customer_loyalty_cdp_vault.l_customer_identity (
    hk_link              varchar(32) primary key,
    hk_customer          varchar(32) references customer_loyalty_cdp_vault.h_customer(hk_customer),
    hk_identity          varchar(32) references customer_loyalty_cdp_vault.h_identity(hk_identity),
    match_method         varchar(16),
    match_confidence     numeric(5,4),
    load_dts             timestamp,
    record_source        varchar(64)
);

create table if not exists customer_loyalty_cdp_vault.l_customer_segment (
    hk_link              varchar(32) primary key,
    hk_customer          varchar(32) references customer_loyalty_cdp_vault.h_customer(hk_customer),
    hk_segment           varchar(32) references customer_loyalty_cdp_vault.h_segment(hk_segment),
    entered_at           timestamp,
    exited_at            timestamp,
    is_current           boolean,
    load_dts             timestamp,
    record_source        varchar(64)
);

create table if not exists customer_loyalty_cdp_vault.l_customer_loyalty (
    hk_link              varchar(32) primary key,
    hk_customer          varchar(32) references customer_loyalty_cdp_vault.h_customer(hk_customer),
    hk_loyalty_account   varchar(32) references customer_loyalty_cdp_vault.h_loyalty_account(hk_loyalty_account),
    load_dts             timestamp,
    record_source        varchar(64)
);

create table if not exists customer_loyalty_cdp_vault.l_loyalty_event (
    hk_link              varchar(32) primary key,
    hk_loyalty_account   varchar(32) references customer_loyalty_cdp_vault.h_loyalty_account(hk_loyalty_account),
    hk_event             varchar(32) references customer_loyalty_cdp_vault.h_event(hk_event),
    points_delta         bigint,
    txn_type             varchar(16),
    load_dts             timestamp,
    record_source        varchar(64)
);

create table if not exists customer_loyalty_cdp_vault.l_redemption (
    hk_link              varchar(32) primary key,
    hk_loyalty_account   varchar(32) references customer_loyalty_cdp_vault.h_loyalty_account(hk_loyalty_account),
    hk_reward            varchar(32) references customer_loyalty_cdp_vault.h_reward(hk_reward),
    redemption_id        varchar(32),
    load_dts             timestamp,
    record_source        varchar(64)
);

create table if not exists customer_loyalty_cdp_vault.l_customer_event (
    hk_link              varchar(32) primary key,
    hk_customer          varchar(32) references customer_loyalty_cdp_vault.h_customer(hk_customer),
    hk_event             varchar(32) references customer_loyalty_cdp_vault.h_event(hk_event),
    load_dts             timestamp,
    record_source        varchar(64)
);

-- ---------- SATELLITES ----------
create table if not exists customer_loyalty_cdp_vault.s_customer_descriptive (
    hk_customer              varchar(32) references customer_loyalty_cdp_vault.h_customer(hk_customer),
    load_dts                 timestamp,
    email_sha256             varchar(64),
    phone_sha256             varchar(64),
    country_iso2             varchar(2),
    postal_code              varchar(16),
    lifecycle_stage          varchar(16),
    golden_record_source     varchar(32),
    confidence_score         numeric(5,4),
    resolution_method        varchar(16),
    status                   varchar(16),
    record_source            varchar(64),
    primary key (hk_customer, load_dts)
);

create table if not exists customer_loyalty_cdp_vault.s_customer_rfm (
    hk_customer              varchar(32) references customer_loyalty_cdp_vault.h_customer(hk_customer),
    load_dts                 timestamp,
    rfm_recency              smallint,
    rfm_frequency            smallint,
    rfm_monetary             smallint,
    predicted_clv            numeric(12,2),
    predicted_churn_prob     numeric(5,4),
    record_source            varchar(64),
    primary key (hk_customer, load_dts)
);

create table if not exists customer_loyalty_cdp_vault.s_loyalty_state (
    hk_loyalty_account       varchar(32) references customer_loyalty_cdp_vault.h_loyalty_account(hk_loyalty_account),
    load_dts                 timestamp,
    tier_code                varchar(16),
    tier_progress_points     integer,
    current_points_balance   bigint,
    lifetime_points_earned   bigint,
    lifetime_points_redeemed bigint,
    status                   varchar(16),
    opt_in_marketing         boolean,
    last_engagement_at       timestamp,
    record_source            varchar(64),
    primary key (hk_loyalty_account, load_dts)
);

create table if not exists customer_loyalty_cdp_vault.s_segment_descriptive (
    hk_segment               varchar(32) references customer_loyalty_cdp_vault.h_segment(hk_segment),
    load_dts                 timestamp,
    segment_name             varchar(128),
    segment_kind             varchar(24),
    refresh_cadence          varchar(16),
    owning_team              varchar(64),
    activated_destinations   text,
    status                   varchar(16),
    record_source            varchar(64),
    primary key (hk_segment, load_dts)
);

create table if not exists customer_loyalty_cdp_vault.s_reward_descriptive (
    hk_reward                varchar(32) references customer_loyalty_cdp_vault.h_reward(hk_reward),
    load_dts                 timestamp,
    reward_name              varchar(255),
    reward_type              varchar(24),
    points_cost              integer,
    cash_equivalent_minor    bigint,
    stock_remaining          integer,
    vendor                   varchar(64),
    valid_from               timestamp,
    valid_to                 timestamp,
    status                   varchar(16),
    record_source            varchar(64),
    primary key (hk_reward, load_dts)
);

create table if not exists customer_loyalty_cdp_vault.s_event_descriptive (
    hk_event                 varchar(32) references customer_loyalty_cdp_vault.h_event(hk_event),
    load_dts                 timestamp,
    event_type               varchar(32),
    channel                  varchar(16),
    source_system            varchar(32),
    campaign_id              varchar(32),
    journey_id               varchar(32),
    product_id               varchar(32),
    order_id                 varchar(32),
    amount_minor             bigint,
    currency                 varchar(3),
    event_ts                 timestamp,
    record_source            varchar(64),
    primary key (hk_event, load_dts)
);

create table if not exists customer_loyalty_cdp_vault.s_consent_state (
    hk_customer              varchar(32) references customer_loyalty_cdp_vault.h_customer(hk_customer),
    load_dts                 timestamp,
    jurisdiction             varchar(16),
    consent_basis            varchar(24),
    consent_string           text,
    purpose_codes            text,
    action                   varchar(24),
    source_system            varchar(32),
    record_source            varchar(64),
    primary key (hk_customer, load_dts, jurisdiction)
);

create table if not exists customer_loyalty_cdp_vault.s_preference (
    hk_customer              varchar(32) references customer_loyalty_cdp_vault.h_customer(hk_customer),
    load_dts                 timestamp,
    channel                  varchar(16),
    topic                    varchar(32),
    state                    varchar(16),
    effective_until          timestamp,
    record_source            varchar(64),
    primary key (hk_customer, load_dts, channel, topic)
);
