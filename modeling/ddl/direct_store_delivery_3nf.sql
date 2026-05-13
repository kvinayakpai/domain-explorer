-- =============================================================================
-- Direct Store Delivery — 3NF schema
-- Source standards (verbatim where the spec names a field):
--   SAP DSD (S/4HANA Direct Store Delivery) — Tour Plan, Visit, Settlement, EPOD.
--   Aldata Apollo — Route, Daily Route, Settlement, Returns Allowance.
--   Trimble Roadnet Anywhere + PeopleNet — Master Route, sequencing, ELD/HOS.
--   Epicor DSD + Epicor Eagle — Mobile Sales Force, presell vs deliver.
--   Salient CMx + AFS DSD — Driver / Route P&L; Perfect Store metrics.
--   ASC X12 EDI — 894 Delivery/Return Base, 895 Acknowledgement, 940 WSO, 945 WSA.
--   GS1 — GTIN-14 (case), GLN (store/route depot), SSCC (pallet).
--   FMCSA 49 CFR Part 395 — Hours of Service / ELD identifier.
--   IFTA — International Fuel Tax Agreement jurisdictions.
-- =============================================================================

create schema if not exists direct_store_delivery;

-- Master route — recurring sequence of stops; SAP DSD "Tour Plan", Roadnet "Master Route".
create table if not exists direct_store_delivery.route (
    route_id              varchar(32) primary key,
    branch_id             varchar(32),
    route_code            varchar(16),
    route_type            varchar(16),                 -- deliver|presell|merchandiser|combination|service
    service_days          varchar(16),                 -- MTWHFSU pattern (e.g., MWF)
    planned_stops         smallint,
    planned_miles         numeric(8,2),
    planned_duration_min  integer,
    vehicle_class         varchar(16),                 -- bobtail|side-bay|tractor-trailer|step-van|sprinter
    status                varchar(16),
    created_at            timestamp,
    effective_from        date,
    effective_to          date
);

-- Driver / driver-sales rep. ELD identifier per FMCSA 49 CFR §395.
create table if not exists direct_store_delivery.driver (
    driver_id        varchar(32) primary key,
    branch_id        varchar(32),
    employee_number  varchar(32),
    full_name        varchar(255),
    cdl_class        varchar(4),                       -- A|B|C
    cdl_expiry       date,
    hire_date        date,
    tenure_years     numeric(5,2),
    eld_device_id    varchar(64),                      -- FMCSA-registered ELD ID
    home_terminal    varchar(32),
    pay_class        varchar(16),                      -- hourly|commission|hybrid
    status           varchar(16)
);

-- Vehicle / truck. PeopleNet ELD + telematics live here.
create table if not exists direct_store_delivery.vehicle (
    vehicle_id           varchar(32) primary key,
    branch_id            varchar(32),
    asset_tag            varchar(32),
    vin                  varchar(17),                  -- ISO 3779
    make                 varchar(32),
    model                varchar(32),
    year                 smallint,
    vehicle_class        varchar(16),                  -- bobtail|side-bay|tractor-trailer|step-van|sprinter
    gvwr_lbs             integer,
    payload_lbs          integer,
    bay_count            smallint,
    refrigerated         boolean,
    telematics_provider  varchar(32),                  -- trimble_peoplenet|samsara|geotab|verizon_connect
    ifta_jurisdictions   text,                          -- JSON list of state/province codes
    status               varchar(16)
);

-- A scheduled stop on a route-day. Grain = (route_id, route_day, sequence).
create table if not exists direct_store_delivery.stop (
    stop_id            varchar(40) primary key,
    route_id           varchar(32) references direct_store_delivery.route(route_id),
    route_day          date,
    outlet_id          varchar(32),
    gln                varchar(13),                    -- GS1 GLN of the store
    planned_sequence   smallint,
    actual_sequence    smallint,
    planned_arrival    timestamp,
    actual_arrival     timestamp,
    planned_departure  timestamp,
    actual_departure   timestamp,
    dwell_minutes      integer,
    status             varchar(16),                    -- scheduled|in_route|on_site|completed|skipped|reattempt
    skip_reason        varchar(64),
    lat                numeric(9,6),
    lng                numeric(9,6),
    presell_flag       boolean
);

-- An order written or delivered at a stop.
create table if not exists direct_store_delivery.dsd_order (
    order_id                 varchar(40) primary key,
    stop_id                  varchar(40) references direct_store_delivery.stop(stop_id),
    outlet_id                varchar(32),
    order_type               varchar(16),              -- presell|deliver|return|swap|service
    order_date               date,
    requested_delivery_date  date,
    account_id               varchar(32),
    salesman_id              varchar(32),
    total_cases              integer,
    total_units              integer,
    gross_amount_cents       bigint,
    discount_amount_cents    bigint,
    net_amount_cents         bigint,
    tax_amount_cents         bigint,
    payment_terms            varchar(16),              -- cod|net7|net14|net30|charge_account
    status                   varchar(16),              -- draft|approved|in_transit|delivered|invoiced|cancelled
    created_at               timestamp
);

-- One SKU line on a DSD order.
create table if not exists direct_store_delivery.dsd_order_line (
    order_line_id        varchar(40) primary key,
    order_id             varchar(40) references direct_store_delivery.dsd_order(order_id),
    sku_id               varchar(32),
    gtin                 varchar(14),                  -- GS1 GTIN-14 (case)
    ordered_units        integer,
    ordered_cases        integer,
    delivered_units      integer,
    delivered_cases      integer,
    returned_units       integer,
    short_units          integer,
    unit_price_cents     bigint,
    extended_amount_cents bigint,
    promo_tactic_id      varchar(32),                  -- joins to trade_promotion_management.promo_tactic
    lot_number           varchar(32),
    expiry_date          date,
    route_load_position  varchar(16)                   -- bay+slot reference for FleetLoader/MobileCast
);

-- Daily settlement — cash + check + EFT + returns reconciliation.
create table if not exists direct_store_delivery.settlement (
    settlement_id              varchar(40) primary key,
    route_id                   varchar(32) references direct_store_delivery.route(route_id),
    driver_id                  varchar(32) references direct_store_delivery.driver(driver_id),
    vehicle_id                 varchar(32) references direct_store_delivery.vehicle(vehicle_id),
    settlement_date            date,
    total_invoiced_cents       bigint,
    total_collected_cash_cents bigint,
    total_collected_check_cents bigint,
    total_collected_eft_cents  bigint,
    total_charge_account_cents bigint,
    returns_credit_cents       bigint,
    spoilage_credit_cents      bigint,
    variance_cents             bigint,
    variance_reason            varchar(64),
    status                     varchar(16),            -- open|reconciled|disputed|adjusted|closed
    closed_at                  timestamp,
    approved_by                varchar(64)
);

-- EPOD: signature + photo + geo at the store door. EDI 895 reference.
create table if not exists direct_store_delivery.epod_event (
    epod_id              varchar(40) primary key,
    stop_id              varchar(40) references direct_store_delivery.stop(stop_id),
    order_id             varchar(40) references direct_store_delivery.dsd_order(order_id),
    signed_at            timestamp,
    signed_by            varchar(255),
    signature_image_uri  text,
    photo_uri            text,
    geo_lat              numeric(9,6),
    geo_lng              numeric(9,6),
    device_id            varchar(64),                  -- Honeywell CN80 / Zebra TC78
    edi_895_doc_id       varchar(64)
);

-- Perfect Store audit — distribution, share-of-cooler, planogram, freshness.
create table if not exists direct_store_delivery.perfect_store_audit (
    audit_id                  varchar(40) primary key,
    stop_id                   varchar(40) references direct_store_delivery.stop(stop_id),
    outlet_id                 varchar(32),
    audit_date                date,
    auditor_id                varchar(32),
    distribution_score        numeric(5,2),
    share_of_cooler_pct       numeric(5,2),
    planogram_compliance_pct  numeric(5,2),
    price_compliance_pct      numeric(5,2),
    promo_compliance_pct      numeric(5,2),
    freshness_score           numeric(5,2),
    oos_count                 smallint,
    perfect_store_score       numeric(5,2),
    photo_uri                 text,
    notes                     text
);

-- Per-minute telemetry from PeopleNet/Samsara/Geotab — GPS, HOS, harsh events.
create table if not exists direct_store_delivery.route_telemetry (
    telemetry_id      varchar(48) primary key,
    vehicle_id        varchar(32) references direct_store_delivery.vehicle(vehicle_id),
    driver_id         varchar(32) references direct_store_delivery.driver(driver_id),
    observed_at       timestamp,
    lat               numeric(9,6),
    lng               numeric(9,6),
    speed_mph         numeric(5,2),
    heading_deg       smallint,
    odometer_miles    numeric(9,2),
    fuel_pct          numeric(5,2),
    ignition_on       boolean,
    hos_status        varchar(8),                       -- off_duty|sleeper|on_duty|driving
    harsh_event_type  varchar(16)                       -- harsh_brake|harsh_accel|hard_corner|over_speed
);

-- Retailer-issued chargeback against a DSD invoice.
create table if not exists direct_store_delivery.deduction (
    deduction_id        varchar(40) primary key,
    account_id          varchar(32),
    order_id            varchar(40),                    -- joins to dsd_order.order_id
    stop_id             varchar(40),
    claim_number        varchar(64),
    deduction_type      varchar(32),                    -- shortage|damages|expired|pricing|stale|promo|swell|other
    amount_cents        bigint,
    open_amount_cents   bigint,
    opened_date         date,
    aging_days          integer,
    status              varchar(16),                    -- open|matched|disputed|paid|written_off|chargeback_lost
    dispute_reason      varchar(64),
    epod_evidence_uri   text,
    resolution_date     date
);

-- Helpful indexes on time and cardinality.
create index if not exists ix_dsd_stop_route       on direct_store_delivery.stop(route_id, route_day);
create index if not exists ix_dsd_order_stop       on direct_store_delivery.dsd_order(stop_id);
create index if not exists ix_dsd_orderline_order  on direct_store_delivery.dsd_order_line(order_id);
create index if not exists ix_dsd_settlement_route on direct_store_delivery.settlement(route_id, settlement_date);
create index if not exists ix_dsd_epod_stop        on direct_store_delivery.epod_event(stop_id);
create index if not exists ix_dsd_psaudit_stop     on direct_store_delivery.perfect_store_audit(stop_id);
create index if not exists ix_dsd_telemetry_veh    on direct_store_delivery.route_telemetry(vehicle_id, observed_at);
create index if not exists ix_dsd_deduction_order  on direct_store_delivery.deduction(order_id);
