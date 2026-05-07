-- =============================================================================
-- Programmatic Advertising — dimensional mart
-- Star schema. Facts (in declining grain): bid, impression, video_event,
--   click, conversion, auction_summary_hourly, deal_performance_daily.
-- Conformed dims (SCD2): campaign, creative, dsp, publisher, deal, device,
--   geo, date, hour.
-- =============================================================================

create schema if not exists programmatic_advertising_dim;

-- ---------------------------------------------------------------------------
-- Conformed dimensions (SCD2)
-- ---------------------------------------------------------------------------
create table if not exists programmatic_advertising_dim.dim_date (
    date_key      integer primary key,
    date_actual   date not null,
    day_of_week   smallint not null,
    iso_week      smallint not null,
    fiscal_period varchar(8)
);

create table if not exists programmatic_advertising_dim.dim_hour (
    hour_key       integer primary key,         -- yyyymmddhh
    hour_actual    timestamp not null,
    date_key       integer not null references programmatic_advertising_dim.dim_date(date_key),
    hour_of_day    smallint not null
);

create table if not exists programmatic_advertising_dim.dim_dsp (
    dsp_key      bigint primary key,
    dsp_id       varchar(64) not null,
    name         varchar(255),
    qps_limit    integer,
    valid_from   timestamp not null,
    valid_to     timestamp,
    is_current   boolean not null
);

create table if not exists programmatic_advertising_dim.dim_publisher (
    publisher_key      bigint primary key,
    publisher_id       varchar(64) not null,
    name               varchar(255),
    domain             varchar(255),
    cat                text,
    ads_txt_status     varchar(16),
    valid_from         timestamp not null,
    valid_to           timestamp,
    is_current         boolean not null
);

create table if not exists programmatic_advertising_dim.dim_campaign (
    campaign_key       bigint primary key,
    campaign_id        varchar(64) not null,
    dsp_id             varchar(64),
    advertiser_domain  varchar(255),
    name               varchar(255),
    pacing_type        varchar(16),
    valid_from         timestamp not null,
    valid_to           timestamp,
    is_current         boolean not null
);

create table if not exists programmatic_advertising_dim.dim_creative (
    creative_key         bigint primary key,
    creative_id          varchar(64) not null,
    campaign_id          varchar(64),
    ad_format            varchar(16),
    width                smallint,
    height               smallint,
    duration_sec         smallint,
    vast_version         varchar(8),
    omid_partner         varchar(64),
    review_status        varchar(16),
    valid_from           timestamp not null,
    valid_to             timestamp,
    is_current           boolean not null
);

create table if not exists programmatic_advertising_dim.dim_deal (
    deal_key      bigint primary key,
    deal_id       varchar(64) not null,
    deal_type     varchar(16),
    publisher_id  varchar(64),
    dsp_id        varchar(64),
    bidfloor      numeric(12,4),
    bidfloorcur   varchar(3),
    valid_from    timestamp not null,
    valid_to      timestamp,
    is_current    boolean not null
);

create table if not exists programmatic_advertising_dim.dim_device (
    device_key     bigint primary key,
    devicetype     smallint,
    os             varchar(32),
    osv            varchar(32),
    make           varchar(64),
    model          varchar(64),
    valid_from     timestamp not null,
    valid_to       timestamp,
    is_current     boolean not null
);

create table if not exists programmatic_advertising_dim.dim_geo (
    geo_key      bigint primary key,
    country      varchar(3),
    region       varchar(8),
    city         varchar(64),
    valid_from   timestamp not null,
    valid_to     timestamp,
    is_current   boolean not null
);

create table if not exists programmatic_advertising_dim.dim_inventory_unit (
    inventory_unit_key  bigint primary key,
    publisher_key       bigint not null references programmatic_advertising_dim.dim_publisher(publisher_key),
    site_or_app_id      varchar(64),
    tagid               varchar(64),
    format_type         varchar(8),                -- Banner|Video|Native|Audio
    width               smallint,
    height              smallint,
    valid_from          timestamp not null,
    valid_to            timestamp,
    is_current          boolean not null
);

-- ---------------------------------------------------------------------------
-- Facts (declining grain)
-- ---------------------------------------------------------------------------

-- Grain: one row per bid (post-auction, includes wins and losses).
create table if not exists programmatic_advertising_dim.fact_bid (
    bid_id              varchar(64) primary key,
    request_id          varchar(64),
    imp_id              varchar(64),
    hour_key            integer references programmatic_advertising_dim.dim_hour(hour_key),
    date_key            integer references programmatic_advertising_dim.dim_date(date_key),
    dsp_key             bigint references programmatic_advertising_dim.dim_dsp(dsp_key),
    publisher_key       bigint references programmatic_advertising_dim.dim_publisher(publisher_key),
    campaign_key        bigint references programmatic_advertising_dim.dim_campaign(campaign_key),
    creative_key        bigint references programmatic_advertising_dim.dim_creative(creative_key),
    deal_key            bigint references programmatic_advertising_dim.dim_deal(deal_key),
    inventory_unit_key  bigint references programmatic_advertising_dim.dim_inventory_unit(inventory_unit_key),
    device_key          bigint references programmatic_advertising_dim.dim_device(device_key),
    geo_key             bigint references programmatic_advertising_dim.dim_geo(geo_key),
    bid_price           numeric(12,4),
    bidfloor            numeric(12,4),
    cur_currency        varchar(3),
    auction_type        smallint,
    won                 boolean not null,
    nbr_code            smallint,
    response_latency_ms integer
);

-- Grain: one row per served impression.
create table if not exists programmatic_advertising_dim.fact_impression (
    impression_event_id   varchar(64) primary key,
    bid_id                varchar(64) references programmatic_advertising_dim.fact_bid(bid_id),
    hour_key              integer references programmatic_advertising_dim.dim_hour(hour_key),
    date_key              integer references programmatic_advertising_dim.dim_date(date_key),
    publisher_key         bigint references programmatic_advertising_dim.dim_publisher(publisher_key),
    campaign_key          bigint references programmatic_advertising_dim.dim_campaign(campaign_key),
    creative_key          bigint references programmatic_advertising_dim.dim_creative(creative_key),
    dsp_key               bigint references programmatic_advertising_dim.dim_dsp(dsp_key),
    deal_key              bigint references programmatic_advertising_dim.dim_deal(deal_key),
    inventory_unit_key    bigint references programmatic_advertising_dim.dim_inventory_unit(inventory_unit_key),
    device_key            bigint references programmatic_advertising_dim.dim_device(device_key),
    geo_key               bigint references programmatic_advertising_dim.dim_geo(geo_key),
    served_at             timestamp,
    clearing_price        numeric(12,4),
    is_viewable           boolean,
    viewable_pixels_pct   numeric(5,2),
    viewable_seconds      numeric(5,2),
    is_ivt                boolean,
    ivt_category          varchar(16)
);

-- Grain: one row per VAST tracking event.
create table if not exists programmatic_advertising_dim.fact_video_event (
    video_event_id        varchar(64) primary key,
    impression_event_id   varchar(64) references programmatic_advertising_dim.fact_impression(impression_event_id),
    hour_key              integer references programmatic_advertising_dim.dim_hour(hour_key),
    creative_key          bigint references programmatic_advertising_dim.dim_creative(creative_key),
    event_type            varchar(24),
    event_ts              timestamp,
    position_sec          numeric(8,2)
);

-- Grain: one row per click event.
create table if not exists programmatic_advertising_dim.fact_click (
    click_event_id        varchar(64) primary key,
    impression_event_id   varchar(64) references programmatic_advertising_dim.fact_impression(impression_event_id),
    hour_key              integer references programmatic_advertising_dim.dim_hour(hour_key),
    date_key              integer references programmatic_advertising_dim.dim_date(date_key),
    publisher_key         bigint references programmatic_advertising_dim.dim_publisher(publisher_key),
    campaign_key          bigint references programmatic_advertising_dim.dim_campaign(campaign_key),
    creative_key          bigint references programmatic_advertising_dim.dim_creative(creative_key),
    clicked_at            timestamp,
    is_ivt                boolean
);

-- Grain: one row per conversion event.
create table if not exists programmatic_advertising_dim.fact_conversion (
    conversion_event_id        varchar(64) primary key,
    impression_event_id        varchar(64) references programmatic_advertising_dim.fact_impression(impression_event_id),
    click_event_id             varchar(64) references programmatic_advertising_dim.fact_click(click_event_id),
    campaign_key               bigint references programmatic_advertising_dim.dim_campaign(campaign_key),
    creative_key               bigint references programmatic_advertising_dim.dim_creative(creative_key),
    date_key                   integer references programmatic_advertising_dim.dim_date(date_key),
    conversion_type            varchar(32),
    conversion_value           numeric(12,4),
    currency                   varchar(3),
    attribution_window_hours   smallint,
    occurred_at                timestamp
);

-- Grain: one row per (publisher, dsp, hour) — pre-aggregated for dashboards.
create table if not exists programmatic_advertising_dim.fact_auction_summary_hourly (
    hour_key             integer not null references programmatic_advertising_dim.dim_hour(hour_key),
    publisher_key        bigint not null references programmatic_advertising_dim.dim_publisher(publisher_key),
    dsp_key              bigint not null references programmatic_advertising_dim.dim_dsp(dsp_key),
    inventory_unit_key   bigint references programmatic_advertising_dim.dim_inventory_unit(inventory_unit_key),
    requests             integer not null,
    bids                 integer not null,
    wins                 integer not null,
    served_impressions   integer not null,
    viewable_impressions integer not null,
    measurable_impressions integer not null,
    ivt_impressions      integer not null,
    revenue              numeric(15,4),
    revenue_currency     varchar(3),
    avg_response_latency_ms numeric(10,2),
    primary key (hour_key, publisher_key, dsp_key, inventory_unit_key)
);

-- Grain: one row per (deal, date) — PMP performance.
create table if not exists programmatic_advertising_dim.fact_deal_performance_daily (
    date_key            integer not null references programmatic_advertising_dim.dim_date(date_key),
    deal_key            bigint not null references programmatic_advertising_dim.dim_deal(deal_key),
    publisher_key       bigint not null references programmatic_advertising_dim.dim_publisher(publisher_key),
    dsp_key             bigint not null references programmatic_advertising_dim.dim_dsp(dsp_key),
    impressions         integer not null,
    revenue             numeric(15,4),
    revenue_currency    varchar(3),
    pmp_share_pct       numeric(7,4),
    deal_floor          numeric(12,4),
    avg_clearing_price  numeric(12,4),
    primary key (date_key, deal_key, publisher_key, dsp_key)
);
