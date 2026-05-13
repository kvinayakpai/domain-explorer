-- =============================================================================
-- Customer Loyalty & CDP — 3NF schema
-- Source standards (verbatim where the spec names a field):
--   Adobe XDM Profile / ExperienceEvent (https://github.com/adobe/xdm)
--   Segment spec: track / identify / group (https://segment.com/docs/connections/spec)
--   IAB TCF v2.2 + GPP consent strings (https://iabtechlab.com/gpp/)
--   GDPR (Reg. 2016/679); CCPA / CPRA (Cal. Civ. Code §1798.100)
--   FASB ASC 606 for points liability deferred-revenue accounting
--   RFC 5322 (email); ITU E.164 (phone); JWE (RFC 7516) for PII encryption
-- =============================================================================

create schema if not exists customer_loyalty_cdp;

-- Golden customer record — output of identity resolution.
create table if not exists customer_loyalty_cdp.customer_master (
    customer_id              varchar(32) primary key,
    first_name_token         varchar(64),
    last_name_token          varchar(64),
    email_sha256             varchar(64),                    -- lower-cased + trimmed + sha256
    phone_sha256             varchar(64),                    -- sha256 of E.164 phone
    country_iso2             varchar(2),
    postal_code              varchar(16),
    golden_record_source     varchar(32),                    -- amperity|salesforce_dc|adobe_rtcdp|treasure_data|in_house
    confidence_score         numeric(5,4),                   -- 0..1
    resolution_method        varchar(16),                    -- deterministic|probabilistic|hybrid|manual_merge
    lifecycle_stage          varchar(16),                    -- prospect|new|active|lapsed|churned|reactivated|vip
    rfm_recency              smallint,                       -- 1..5
    rfm_frequency            smallint,
    rfm_monetary             smallint,
    predicted_clv            numeric(12,2),
    predicted_churn_prob     numeric(5,4),
    first_seen_at            timestamp,
    last_seen_at             timestamp,
    created_at               timestamp,
    updated_at               timestamp,
    status                   varchar(16)                     -- active|deleted|suppressed|right_to_be_forgotten
);

-- Identity graph edge — many identifiers per customer_master.
create table if not exists customer_loyalty_cdp.identity_link (
    identity_id              varchar(64) primary key,
    customer_id              varchar(32) references customer_loyalty_cdp.customer_master(customer_id),
    identifier_type          varchar(24),                    -- email_sha256|phone_sha256|loyalty_id|device_id|maid|fbp|ga_client_id|cookie_id|postal_addr|wallet_pass
    identifier_value_hash    varchar(64),                    -- sha256; raw never persisted in analytical zone
    match_method             varchar(16),                    -- deterministic|probabilistic|merged|manual
    match_confidence         numeric(5,4),
    source_system            varchar(32),                    -- salesforce_dc|adobe_rtcdp|amperity|segment|mparticle|tealium|treasure_data|klaviyo|braze|iterable|epsilon
    first_observed_at        timestamp,
    last_observed_at         timestamp,
    is_active                boolean
);

-- Behavioral / engagement event — Adobe XDM ExperienceEvent / Segment track grain.
create table if not exists customer_loyalty_cdp.event (
    event_id                 varchar(64) primary key,
    customer_id              varchar(32) references customer_loyalty_cdp.customer_master(customer_id),
    anonymous_id             varchar(64),                    -- Segment anonymousId / Adobe ECID
    event_type               varchar(32),                    -- page_view|product_view|...|store_visit
    channel                  varchar(16),
    source_system            varchar(32),
    campaign_id              varchar(32),
    journey_id               varchar(32),
    product_id               varchar(32),
    order_id                 varchar(32),
    amount_minor             bigint,
    currency                 varchar(3),
    event_ts                 timestamp,
    ingest_ts                timestamp,
    properties_json          text
);

-- Segment / audience definition.
create table if not exists customer_loyalty_cdp.segment (
    segment_id               varchar(32) primary key,
    segment_name             varchar(128),
    segment_kind             varchar(24),                    -- rfm|behavioural|predictive|rules|lookalike|suppression
    definition_dsl           text,                           -- json DSL or SQL
    refresh_cadence          varchar(16),                    -- realtime|hourly|daily|weekly
    owning_team              varchar(64),
    activated_destinations   text,                           -- JSON list of destinations
    created_at               timestamp,
    updated_at               timestamp,
    status                   varchar(16)                     -- draft|active|paused|deprecated
);

-- Append-only segment-membership episodes.
create table if not exists customer_loyalty_cdp.segment_membership (
    membership_id            varchar(64) primary key,
    customer_id              varchar(32) references customer_loyalty_cdp.customer_master(customer_id),
    segment_id               varchar(32) references customer_loyalty_cdp.segment(segment_id),
    entered_at               timestamp,
    exited_at                timestamp,
    entry_reason             varchar(64),
    source_system            varchar(32),
    is_current               boolean
);

-- Loyalty account — one per customer per program.
create table if not exists customer_loyalty_cdp.loyalty_account (
    loyalty_account_id       varchar(32) primary key,
    customer_id              varchar(32) references customer_loyalty_cdp.customer_master(customer_id),
    program_code             varchar(32),
    tier_code                varchar(16),                    -- bronze|silver|gold|platinum|black|founder
    tier_progress_points     integer,
    tier_anchor_date         date,
    enrolled_at              timestamp,
    enrollment_channel       varchar(16),
    lifetime_points_earned   bigint,
    lifetime_points_redeemed bigint,
    current_points_balance   bigint,
    status                   varchar(16),                    -- active|paused|expired|closed|fraud_hold
    opt_in_marketing         boolean,
    last_engagement_at       timestamp
);

-- Points ledger — ASC 606 book of record for points liability.
create table if not exists customer_loyalty_cdp.points_ledger (
    ledger_id                varchar(64) primary key,
    loyalty_account_id       varchar(32) references customer_loyalty_cdp.loyalty_account(loyalty_account_id),
    txn_type                 varchar(16),                    -- earn|redeem|expire|adjust|transfer_in|transfer_out|bonus|reversal
    source_event_id          varchar(64),                    -- event.event_id or redemption.redemption_id
    order_id                 varchar(32),
    points_delta             bigint,                         -- signed integer
    cash_equivalent_minor    bigint,
    campaign_code            varchar(32),
    txn_ts                   timestamp,
    posted_ts                timestamp,
    expiry_ts                timestamp,
    status                   varchar(16)                     -- posted|pending|reversed|expired
);

-- Reward catalog.
create table if not exists customer_loyalty_cdp.reward (
    reward_id                varchar(32) primary key,
    reward_name              varchar(255),
    reward_type              varchar(24),                    -- gift_card|product_voucher|discount_percent|discount_amount|partner_experience|charitable_donation|sweepstakes_entry
    points_cost              integer,
    cash_equivalent_minor    bigint,
    stock_remaining          integer,
    vendor                   varchar(64),
    valid_from               timestamp,
    valid_to                 timestamp,
    status                   varchar(16)                     -- active|paused|sold_out|retired
);

-- Reward redemption — drives the redemption KPI.
create table if not exists customer_loyalty_cdp.redemption (
    redemption_id            varchar(32) primary key,
    loyalty_account_id       varchar(32) references customer_loyalty_cdp.loyalty_account(loyalty_account_id),
    reward_id                varchar(32) references customer_loyalty_cdp.reward(reward_id),
    points_spent             integer,
    cash_equivalent_minor    bigint,
    channel                  varchar(16),
    order_id                 varchar(32),
    requested_at             timestamp,
    fulfilled_at             timestamp,
    status                   varchar(16)                     -- pending|fulfilled|cancelled|reversed|fraud_review
);

-- Channel / topic preferences — authoritative for send-eligibility checks.
create table if not exists customer_loyalty_cdp.preference_center (
    preference_id            varchar(64) primary key,
    customer_id              varchar(32) references customer_loyalty_cdp.customer_master(customer_id),
    channel                  varchar(16),                    -- email|sms|push|direct_mail|in_app|paid_media
    topic                    varchar(32),
    state                    varchar(16),                    -- opted_in|opted_out|paused|never_set
    source_system            varchar(32),
    changed_at               timestamp,
    effective_until          timestamp
);

-- Legal book of record for consent — GDPR Art. 6/7, CCPA/CPRA, IAB TCF v2.2 / GPP.
create table if not exists customer_loyalty_cdp.consent_record (
    consent_id               varchar(64) primary key,
    customer_id              varchar(32) references customer_loyalty_cdp.customer_master(customer_id),
    jurisdiction             varchar(16),                    -- EU_GDPR|UK_GDPR|US_CCPA|US_CPRA|CA_PIPEDA|BR_LGPD|other
    consent_basis            varchar(24),                    -- consent|contract|legitimate_interest|legal_obligation|vital_interest|public_task
    consent_string           text,                           -- IAB TCF v2.2 / GPP encoded
    purpose_codes            text,                           -- JSON array
    action                   varchar(24),                    -- granted|withdrawn|updated|right_to_delete|right_to_portability|complaint
    source_system            varchar(32),
    event_ts                 timestamp,
    ip_token                 varchar(64),
    user_agent_token         varchar(64)
);

-- Indexes for hot query paths.
create index if not exists ix_idlink_customer       on customer_loyalty_cdp.identity_link(customer_id);
create index if not exists ix_event_customer        on customer_loyalty_cdp.event(customer_id);
create index if not exists ix_event_ts              on customer_loyalty_cdp.event(event_ts);
create index if not exists ix_segmem_customer       on customer_loyalty_cdp.segment_membership(customer_id);
create index if not exists ix_segmem_segment        on customer_loyalty_cdp.segment_membership(segment_id);
create index if not exists ix_loyacc_customer       on customer_loyalty_cdp.loyalty_account(customer_id);
create index if not exists ix_ledger_account        on customer_loyalty_cdp.points_ledger(loyalty_account_id);
create index if not exists ix_redemp_account        on customer_loyalty_cdp.redemption(loyalty_account_id);
create index if not exists ix_pref_customer         on customer_loyalty_cdp.preference_center(customer_id);
create index if not exists ix_consent_customer      on customer_loyalty_cdp.consent_record(customer_id);
