-- =============================================================================
-- Programmatic Advertising — Data Vault 2.0
-- Hubs: ad_request, imp, bid, dsp, publisher, creative, campaign, deal, user.
-- Links carry the auction graph (request -> imp -> bid -> impression event).
-- Sat hash_diff lets us replay every status hop emitted by Prebid auctionEnd
-- and SSP server-side equivalents without overwriting prior states.
-- =============================================================================

create schema if not exists programmatic_advertising_vault;

-- ---------------------------------------------------------------------------
-- Hubs
-- ---------------------------------------------------------------------------
create table if not exists programmatic_advertising_vault.hub_ad_request (
    ad_request_hk   bytea primary key,
    ad_request_bk   varchar not null,        -- BidRequest.id
    load_dts        timestamp not null,
    rec_src         varchar not null
);

create table if not exists programmatic_advertising_vault.hub_imp (
    imp_hk     bytea primary key,
    imp_bk     varchar not null,             -- request_id || ':' || imp_id
    load_dts   timestamp not null,
    rec_src    varchar not null
);

create table if not exists programmatic_advertising_vault.hub_bid (
    bid_hk     bytea primary key,
    bid_bk     varchar not null,
    load_dts   timestamp not null,
    rec_src    varchar not null
);

create table if not exists programmatic_advertising_vault.hub_dsp (
    dsp_hk     bytea primary key,
    dsp_bk     varchar not null,
    load_dts   timestamp not null,
    rec_src    varchar not null
);

create table if not exists programmatic_advertising_vault.hub_publisher (
    publisher_hk   bytea primary key,
    publisher_bk   varchar not null,
    load_dts       timestamp not null,
    rec_src        varchar not null
);

create table if not exists programmatic_advertising_vault.hub_creative (
    creative_hk   bytea primary key,
    creative_bk   varchar not null,
    load_dts      timestamp not null,
    rec_src       varchar not null
);

create table if not exists programmatic_advertising_vault.hub_campaign (
    campaign_hk   bytea primary key,
    campaign_bk   varchar not null,
    load_dts      timestamp not null,
    rec_src       varchar not null
);

create table if not exists programmatic_advertising_vault.hub_deal (
    deal_hk    bytea primary key,
    deal_bk    varchar not null,
    load_dts   timestamp not null,
    rec_src    varchar not null
);

create table if not exists programmatic_advertising_vault.hub_user (
    user_hk    bytea primary key,
    user_bk    varchar not null,             -- User.id (publisher namespace)
    load_dts   timestamp not null,
    rec_src    varchar not null
);

-- ---------------------------------------------------------------------------
-- Links
-- ---------------------------------------------------------------------------
create table if not exists programmatic_advertising_vault.link_request_imp (
    link_hk         bytea primary key,
    ad_request_hk   bytea not null references programmatic_advertising_vault.hub_ad_request(ad_request_hk),
    imp_hk          bytea not null references programmatic_advertising_vault.hub_imp(imp_hk),
    load_dts        timestamp not null,
    rec_src         varchar not null
);

create table if not exists programmatic_advertising_vault.link_request_publisher (
    link_hk         bytea primary key,
    ad_request_hk   bytea not null references programmatic_advertising_vault.hub_ad_request(ad_request_hk),
    publisher_hk    bytea not null references programmatic_advertising_vault.hub_publisher(publisher_hk),
    user_hk         bytea references programmatic_advertising_vault.hub_user(user_hk),
    load_dts        timestamp not null,
    rec_src         varchar not null
);

create table if not exists programmatic_advertising_vault.link_bid_imp (
    link_hk      bytea primary key,
    bid_hk       bytea not null references programmatic_advertising_vault.hub_bid(bid_hk),
    imp_hk       bytea not null references programmatic_advertising_vault.hub_imp(imp_hk),
    dsp_hk       bytea not null references programmatic_advertising_vault.hub_dsp(dsp_hk),
    creative_hk  bytea references programmatic_advertising_vault.hub_creative(creative_hk),
    campaign_hk  bytea references programmatic_advertising_vault.hub_campaign(campaign_hk),
    deal_hk      bytea references programmatic_advertising_vault.hub_deal(deal_hk),
    load_dts     timestamp not null,
    rec_src      varchar not null
);

create table if not exists programmatic_advertising_vault.link_campaign_creative (
    link_hk      bytea primary key,
    campaign_hk  bytea not null references programmatic_advertising_vault.hub_campaign(campaign_hk),
    creative_hk  bytea not null references programmatic_advertising_vault.hub_creative(creative_hk),
    load_dts     timestamp not null,
    rec_src      varchar not null
);

create table if not exists programmatic_advertising_vault.link_deal_dsp_pub (
    link_hk        bytea primary key,
    deal_hk        bytea not null references programmatic_advertising_vault.hub_deal(deal_hk),
    dsp_hk         bytea not null references programmatic_advertising_vault.hub_dsp(dsp_hk),
    publisher_hk   bytea not null references programmatic_advertising_vault.hub_publisher(publisher_hk),
    load_dts       timestamp not null,
    rec_src        varchar not null
);

-- ---------------------------------------------------------------------------
-- Satellites (descriptive context, change-tracked via hash_diff)
-- ---------------------------------------------------------------------------
create table if not exists programmatic_advertising_vault.sat_request_context (
    ad_request_hk   bytea not null references programmatic_advertising_vault.hub_ad_request(ad_request_hk),
    load_dts        timestamp not null,
    load_end_dts    timestamp,
    hash_diff       bytea not null,
    auction_type    smallint,
    tmax_ms         integer,
    cur_currency    varchar(12),
    bcat            text,
    badv            text,
    app_or_site     varchar(8),
    test_flag       boolean,
    received_at     timestamp,
    rec_src         varchar not null,
    primary key (ad_request_hk, load_dts)
);

create table if not exists programmatic_advertising_vault.sat_imp_placement (
    imp_hk          bytea not null references programmatic_advertising_vault.hub_imp(imp_hk),
    load_dts        timestamp not null,
    load_end_dts    timestamp,
    hash_diff       bytea not null,
    tagid           varchar(64),
    bidfloor        numeric(12,4),
    bidfloorcur     varchar(3),
    secure          smallint,
    format_type     varchar(8),
    pmp_dealcount   smallint,
    instl           smallint,
    rwdd            smallint,
    rec_src         varchar not null,
    primary key (imp_hk, load_dts)
);

create table if not exists programmatic_advertising_vault.sat_bid_state (
    bid_hk          bytea not null references programmatic_advertising_vault.hub_bid(bid_hk),
    load_dts        timestamp not null,
    load_end_dts    timestamp,
    hash_diff       bytea not null,
    price           numeric(12,4),
    cur_currency    varchar(3),
    status          varchar(16),                 -- submitted|won|lost|filtered|rejected
    nurl_fired      boolean,
    burl_fired      boolean,
    lurl_fired      boolean,
    adomain         text,
    cattax          smallint,
    rec_src         varchar not null,
    primary key (bid_hk, load_dts)
);

create table if not exists programmatic_advertising_vault.sat_bid_outcome (
    bid_hk            bytea not null references programmatic_advertising_vault.hub_bid(bid_hk),
    load_dts          timestamp not null,
    load_end_dts      timestamp,
    hash_diff         bytea not null,
    served            boolean,                   -- impression fired
    viewable          boolean,                   -- MRC viewable
    ivt_flag          boolean,                   -- MRC IVT
    ivt_category      varchar(16),
    served_at         timestamp,
    rec_src           varchar not null,
    primary key (bid_hk, load_dts)
);

create table if not exists programmatic_advertising_vault.sat_creative_state (
    creative_hk          bytea not null references programmatic_advertising_vault.hub_creative(creative_hk),
    load_dts             timestamp not null,
    load_end_dts         timestamp,
    hash_diff            bytea not null,
    ad_format            varchar(16),
    width                smallint,
    height               smallint,
    duration_sec         smallint,
    vast_version         varchar(8),
    omid_partner         varchar(64),
    review_status        varchar(16),
    brand_safety_score   numeric(5,2),
    rec_src              varchar not null,
    primary key (creative_hk, load_dts)
);

create table if not exists programmatic_advertising_vault.sat_campaign_state (
    campaign_hk        bytea not null references programmatic_advertising_vault.hub_campaign(campaign_hk),
    load_dts           timestamp not null,
    load_end_dts       timestamp,
    hash_diff          bytea not null,
    advertiser_domain  varchar(255),
    name               varchar(255),
    start_at           date,
    end_at             date,
    budget             numeric(15,4),
    budget_currency    varchar(3),
    pacing_type        varchar(16),
    status             varchar(16),
    rec_src            varchar not null,
    primary key (campaign_hk, load_dts)
);

create table if not exists programmatic_advertising_vault.sat_deal_state (
    deal_hk         bytea not null references programmatic_advertising_vault.hub_deal(deal_hk),
    load_dts        timestamp not null,
    load_end_dts    timestamp,
    hash_diff       bytea not null,
    bidfloor        numeric(12,4),
    bidfloorcur     varchar(3),
    deal_type       varchar(16),
    priority        smallint,
    start_at        date,
    end_at          date,
    status          varchar(16),
    rec_src         varchar not null,
    primary key (deal_hk, load_dts)
);

create table if not exists programmatic_advertising_vault.sat_user_consent (
    user_hk          bytea not null references programmatic_advertising_vault.hub_user(user_hk),
    load_dts         timestamp not null,
    load_end_dts     timestamp,
    hash_diff        bytea not null,
    consent_string   text,
    gpp_string       text,
    gpp_sid          text,
    us_privacy       varchar(8),
    coppa            smallint,
    eids_count       smallint,
    rec_src          varchar not null,
    primary key (user_hk, load_dts)
);
