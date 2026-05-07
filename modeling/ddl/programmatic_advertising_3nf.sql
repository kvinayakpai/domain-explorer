-- =============================================================================
-- Programmatic Advertising — 3NF schema
-- Source standards (verbatim where the spec names a field):
--   IAB Tech Lab OpenRTB 2.6 — BidRequest, Imp, Banner, Video, Native, Audio,
--     Source, App, Site, User, Geo, Device, Regs, BidResponse, SeatBid, Bid.
--     https://github.com/InteractiveAdvertisingBureau/openrtb2.x
--   IAB AdCOM 1.0 — Placement, Display, Video Placement, Ad.
--     https://github.com/InteractiveAdvertisingBureau/AdCOM
--   IAB VAST 4.2 — Linear, Companion, MediaFile, TrackingEvents.
--   IAB ads.txt / app-ads.txt 1.1, IAB GPP / TCF 2.2.
-- =============================================================================

create schema if not exists programmatic_advertising_3nf;

-- OpenRTB 2.6 Publisher object — owns the inventory.
create table if not exists programmatic_advertising_3nf.publisher (
    publisher_id      varchar(64) primary key,
    name              varchar(255),
    cat               text,                       -- IAB Content Taxonomy
    domain            varchar(255),
    ads_txt_status    varchar(16)                 -- ads.txt 1.1 validation outcome
);

-- OpenRTB 2.6 Site object — web inventory descriptor.
create table if not exists programmatic_advertising_3nf.site (
    site_id           varchar(64) primary key,
    name              varchar(255),
    domain            varchar(255),
    cat               text,
    page_url          text,
    ref_url           text,
    publisher_id      varchar(64) references programmatic_advertising_3nf.publisher(publisher_id),
    privacypolicy     smallint,
    mobile            smallint
);

-- OpenRTB 2.6 App object — app inventory descriptor.
create table if not exists programmatic_advertising_3nf.app (
    app_id            varchar(64) primary key,
    bundle            varchar(128),               -- App.bundle
    name              varchar(255),
    domain            varchar(255),
    storeurl          text,
    cat               text,
    ver               varchar(32),
    paid              smallint,
    publisher_id      varchar(64) references programmatic_advertising_3nf.publisher(publisher_id)
);

-- OpenRTB 2.6 Geo object.
create table if not exists programmatic_advertising_3nf.geo (
    geo_id        varchar(64) primary key,
    lat           numeric(9,6),
    lon           numeric(9,6),
    country       varchar(3),                     -- ISO 3166-1 alpha-3
    region        varchar(8),
    city          varchar(64),
    zip           varchar(16),
    type          smallint,                       -- 1=GPS, 2=IP, 3=user-provided
    utcoffset     smallint
);

-- OpenRTB 2.6 Device object.
create table if not exists programmatic_advertising_3nf.device (
    device_id        varchar(64) primary key,
    ua               text,
    ip               varchar(45),
    devicetype       smallint,
    make             varchar(64),
    model            varchar(64),
    os               varchar(32),
    osv              varchar(32),
    language         varchar(8),
    ifa              varchar(64),                 -- IDFA / GAID
    dnt              smallint,
    lmt              smallint,
    connectiontype   smallint,
    geo_id           varchar(64) references programmatic_advertising_3nf.geo(geo_id)
);

-- OpenRTB 2.6 User object — pseudonymous identifier and segments.
create table if not exists programmatic_advertising_3nf.rtb_user (
    user_id          varchar(64) primary key,
    buyeruid         varchar(64),                 -- DSP-side id mapping
    yob              smallint,
    gender           varchar(1),
    keywords         text,
    geo_id           varchar(64) references programmatic_advertising_3nf.geo(geo_id),
    consent_string   text,                        -- TCF 2.2 / GPP
    eids_count       smallint                     -- |User.eids[]|
);

-- OpenRTB 2.6 Source object + IAB SupplyChain (sellers.json/SCS).
create table if not exists programmatic_advertising_3nf.source (
    source_id           varchar(64) primary key,
    tid                 varchar(64),
    pchain              text,
    schain_complete     smallint,
    schain_nodes_count  smallint,
    fd                  smallint
);

-- OpenRTB 2.6 Regs object — TCF/GPP, COPPA, US Privacy.
create table if not exists programmatic_advertising_3nf.regs (
    regs_id          varchar(64) primary key,
    coppa            smallint,
    gpp_string       text,
    gpp_sid          text,
    us_privacy       varchar(8),
    gdpr_applies     smallint
);

-- OpenRTB 2.6 BidRequest envelope.
create table if not exists programmatic_advertising_3nf.ad_request (
    request_id      varchar(64) primary key,    -- BidRequest.id
    received_at     timestamp,
    auction_type    smallint,                    -- BidRequest.at
    tmax_ms         integer,                     -- BidRequest.tmax
    cur_currency    varchar(12),                 -- BidRequest.cur
    bcat            text,                        -- BidRequest.bcat (blocked categories)
    badv            text,                        -- BidRequest.badv
    app_or_site     varchar(8),
    site_id         varchar(64) references programmatic_advertising_3nf.site(site_id),
    app_id          varchar(64) references programmatic_advertising_3nf.app(app_id),
    user_id         varchar(64) references programmatic_advertising_3nf.rtb_user(user_id),
    device_id       varchar(64) references programmatic_advertising_3nf.device(device_id),
    source_id       varchar(64) references programmatic_advertising_3nf.source(source_id),
    regs_id         varchar(64) references programmatic_advertising_3nf.regs(regs_id),
    test_flag       boolean
);

-- OpenRTB 2.6 Imp — one impression opportunity per BidRequest.
create table if not exists programmatic_advertising_3nf.imp (
    imp_id          varchar(64) not null,        -- Imp.id (unique within request)
    request_id      varchar(64) not null references programmatic_advertising_3nf.ad_request(request_id),
    tagid           varchar(64),
    bidfloor        numeric(12,4),               -- Imp.bidfloor (CPM)
    bidfloorcur     varchar(3),
    secure          smallint,
    format_type     varchar(8),                  -- Banner|Video|Native|Audio
    pmp_dealcount   smallint,
    instl           smallint,
    rwdd            smallint,                    -- Rewarded inventory (OpenRTB 2.6)
    primary key (imp_id, request_id)
);

-- AdCOM/OpenRTB Banner placement.
create table if not exists programmatic_advertising_3nf.banner (
    imp_id      varchar(64) not null,
    request_id  varchar(64) not null,
    w           smallint,
    h           smallint,
    btype       text,                            -- Banner.btype (blocked creative types)
    pos         smallint,                        -- Banner.pos
    api         text,                            -- MRAID/OMID frameworks
    primary key (imp_id, request_id),
    foreign key (imp_id, request_id) references programmatic_advertising_3nf.imp(imp_id, request_id)
);

-- AdCOM/OpenRTB Video placement.
create table if not exists programmatic_advertising_3nf.video (
    imp_id        varchar(64) not null,
    request_id    varchar(64) not null,
    mimes         text,
    minduration   smallint,
    maxduration   smallint,
    protocols     text,                          -- VAST/VPAID protocol versions
    linearity     smallint,
    skip          smallint,
    skipafter     smallint,
    placement     smallint,                      -- AdCOM placement subtype
    pos           smallint,
    primary key (imp_id, request_id),
    foreign key (imp_id, request_id) references programmatic_advertising_3nf.imp(imp_id, request_id)
);

-- OpenRTB Native 1.2 placement.
create table if not exists programmatic_advertising_3nf.native (
    imp_id                 varchar(64) not null,
    request_id             varchar(64) not null,
    ver                    varchar(8),
    api                    text,
    assets_required_count  smallint,
    plcmttype              smallint,
    primary key (imp_id, request_id),
    foreign key (imp_id, request_id) references programmatic_advertising_3nf.imp(imp_id, request_id)
);

-- DSP / bidder seat directory.
create table if not exists programmatic_advertising_3nf.dsp (
    dsp_id        varchar(64) primary key,
    name          varchar(255),
    endpoint_url  text,
    status        varchar(16),
    qps_limit     integer
);

-- OpenRTB 2.6 BidResponse — DSP reply (within Imp.bidfloor and tmax constraints).
create table if not exists programmatic_advertising_3nf.bid_response (
    response_id           varchar(64) primary key,    -- BidResponse.id
    request_id            varchar(64) references programmatic_advertising_3nf.ad_request(request_id),
    dsp_id                varchar(64) references programmatic_advertising_3nf.dsp(dsp_id),
    bidid                 varchar(64),
    cur_currency          varchar(3),
    nbr_code              smallint,                   -- BidResponse.nbr (no-bid reason)
    response_received_at  timestamp,
    response_latency_ms   integer
);

-- OpenRTB SeatBid — bids grouped by buyer seat.
create table if not exists programmatic_advertising_3nf.seatbid (
    seatbid_id    varchar(64) primary key,
    response_id   varchar(64) references programmatic_advertising_3nf.bid_response(response_id),
    seat          varchar(64),
    group_flag    smallint
);

-- Buy-side campaign object.
create table if not exists programmatic_advertising_3nf.campaign (
    campaign_id        varchar(64) primary key,
    dsp_id             varchar(64) references programmatic_advertising_3nf.dsp(dsp_id),
    advertiser_domain  varchar(255),
    name               varchar(255),
    start_at           date,
    end_at             date,
    budget             numeric(15,4),
    budget_currency    varchar(3),
    pacing_type        varchar(16),
    status             varchar(16)
);

-- AdCOM Ad / VAST creative.
create table if not exists programmatic_advertising_3nf.creative (
    creative_id          varchar(64) primary key,
    campaign_id          varchar(64) references programmatic_advertising_3nf.campaign(campaign_id),
    ad_format            varchar(16),                 -- Banner|Video|Native|Audio|DOOH
    width                smallint,
    height               smallint,
    duration_sec         smallint,
    vast_version         varchar(8),
    media_url            text,
    clickthrough_url     text,
    omid_partner         varchar(64),                 -- Open Measurement (OMID)
    review_status        varchar(16),
    brand_safety_score   numeric(5,2)
);

-- OpenRTB PMP Deal — private marketplace fixed/auction terms.
create table if not exists programmatic_advertising_3nf.deal (
    deal_id         varchar(64) primary key,
    publisher_id    varchar(64) references programmatic_advertising_3nf.publisher(publisher_id),
    dsp_id          varchar(64) references programmatic_advertising_3nf.dsp(dsp_id),
    bidfloor        numeric(12,4),
    bidfloorcur     varchar(3),
    at              smallint,
    wseat           text,
    wadomain        text,
    priority        smallint,
    deal_type       varchar(16),                     -- PMP|PG|PreferredDeal
    start_at        date,
    end_at          date,
    status          varchar(16)
);

-- OpenRTB 2.6 Bid — individual bid for a particular Imp.
create table if not exists programmatic_advertising_3nf.bid (
    bid_id        varchar(64) primary key,
    seatbid_id    varchar(64) references programmatic_advertising_3nf.seatbid(seatbid_id),
    imp_id        varchar(64),
    request_id    varchar(64),
    campaign_id   varchar(64) references programmatic_advertising_3nf.campaign(campaign_id),
    creative_id   varchar(64) references programmatic_advertising_3nf.creative(creative_id),
    price         numeric(12,4),                     -- Bid.price (CPM)
    dealid        varchar(64) references programmatic_advertising_3nf.deal(deal_id),
    adomain       text,                              -- Bid.adomain
    cat           text,
    cattax        smallint,                          -- Bid.cattax
    w             smallint,
    h             smallint,
    nurl          text,                              -- Bid.nurl (win notice)
    lurl          text,                              -- Bid.lurl (loss notice)
    burl          text,                              -- Bid.burl (billing notice)
    api           smallint,
    status        varchar(16),                      -- submitted|won|lost|filtered|rejected
    foreign key (imp_id, request_id) references programmatic_advertising_3nf.imp(imp_id, request_id)
);

-- Auction-clearing outcome per Imp (Prebid auctionEnd or SSP server-side).
create table if not exists programmatic_advertising_3nf.auction_event (
    auction_event_id   varchar(64) primary key,
    request_id         varchar(64),
    imp_id             varchar(64),
    winning_bid_id     varchar(64) references programmatic_advertising_3nf.bid(bid_id),
    clearing_price     numeric(12,4),
    cleared_currency   varchar(3),
    bid_count          smallint,
    filtered_count     smallint,
    auction_type       smallint,
    cleared_at         timestamp,
    foreign key (imp_id, request_id) references programmatic_advertising_3nf.imp(imp_id, request_id)
);

-- Served impression — Bid.burl/billing pixel + IAS/DV/MRC viewability.
create table if not exists programmatic_advertising_3nf.impression_event (
    impression_event_id   varchar(64) primary key,
    bid_id                varchar(64) references programmatic_advertising_3nf.bid(bid_id),
    served_at             timestamp,
    viewable              boolean,                    -- MRC viewability standard
    viewable_pixels_pct   numeric(5,2),
    viewable_seconds      numeric(5,2),
    ivt_flag              boolean,                    -- MRC IVT
    ivt_category          varchar(16),                -- GIVT|SIVT|None
    omid_session_id       varchar(64)
);

-- VAST 4.x TrackingEvents — start/quartile/complete/skip/click.
create table if not exists programmatic_advertising_3nf.video_event (
    video_event_id        varchar(64) primary key,
    impression_event_id   varchar(64) references programmatic_advertising_3nf.impression_event(impression_event_id),
    event_type            varchar(24),                -- impression|start|firstQuartile|midpoint|thirdQuartile|complete|skip|mute|click
    event_ts              timestamp,
    position_sec          numeric(8,2)
);

-- Click event — VAST ClickThrough or banner click pixel.
create table if not exists programmatic_advertising_3nf.click_event (
    click_event_id        varchar(64) primary key,
    impression_event_id   varchar(64) references programmatic_advertising_3nf.impression_event(impression_event_id),
    clicked_at            timestamp,
    click_url             text,
    ivt_flag              boolean
);

-- Conversion (post-click/post-view) signal back from advertiser tag.
create table if not exists programmatic_advertising_3nf.conversion_event (
    conversion_event_id        varchar(64) primary key,
    impression_event_id        varchar(64) references programmatic_advertising_3nf.impression_event(impression_event_id),
    click_event_id             varchar(64) references programmatic_advertising_3nf.click_event(click_event_id),
    campaign_id                varchar(64) references programmatic_advertising_3nf.campaign(campaign_id),
    conversion_type            varchar(32),
    conversion_value           numeric(12,4),
    currency                   varchar(3),
    attribution_window_hours   smallint,
    occurred_at                timestamp
);
