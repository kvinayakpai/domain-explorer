-- =============================================================================
-- Direct Store Delivery — Data Vault 2.0 schema
-- Hubs (business keys) + Links (relationships) + Satellites (descriptive,
-- insert-only, time-stamped). Mirrors the SAP DSD / Roadnet / EPOD source
-- contract and supports late-binding settlement adjustments.
-- =============================================================================

create schema if not exists direct_store_delivery_vault;

-- ---------- HUBS ----------
create table if not exists direct_store_delivery_vault.h_route (
    hk_route       varchar(32) primary key,         -- MD5(route_id)
    route_id       varchar(32) unique,
    load_dts       timestamp,
    record_source  varchar(64)
);

create table if not exists direct_store_delivery_vault.h_driver (
    hk_driver      varchar(32) primary key,
    driver_id      varchar(32) unique,
    load_dts       timestamp,
    record_source  varchar(64)
);

create table if not exists direct_store_delivery_vault.h_vehicle (
    hk_vehicle     varchar(32) primary key,
    vehicle_id     varchar(32) unique,
    load_dts       timestamp,
    record_source  varchar(64)
);

create table if not exists direct_store_delivery_vault.h_stop (
    hk_stop        varchar(32) primary key,
    stop_id        varchar(40) unique,
    load_dts       timestamp,
    record_source  varchar(64)
);

create table if not exists direct_store_delivery_vault.h_order (
    hk_order       varchar(32) primary key,
    order_id       varchar(40) unique,
    load_dts       timestamp,
    record_source  varchar(64)
);

create table if not exists direct_store_delivery_vault.h_settlement (
    hk_settlement  varchar(32) primary key,
    settlement_id  varchar(40) unique,
    load_dts       timestamp,
    record_source  varchar(64)
);

create table if not exists direct_store_delivery_vault.h_audit (
    hk_audit       varchar(32) primary key,
    audit_id       varchar(40) unique,
    load_dts       timestamp,
    record_source  varchar(64)
);

create table if not exists direct_store_delivery_vault.h_outlet (
    hk_outlet      varchar(32) primary key,
    outlet_id      varchar(32) unique,
    load_dts       timestamp,
    record_source  varchar(64)
);

-- ---------- LINKS ----------
create table if not exists direct_store_delivery_vault.l_route_stop (
    hk_link        varchar(32) primary key,
    hk_route       varchar(32) references direct_store_delivery_vault.h_route(hk_route),
    hk_stop        varchar(32) references direct_store_delivery_vault.h_stop(hk_stop),
    route_day      date,
    load_dts       timestamp,
    record_source  varchar(64)
);

create table if not exists direct_store_delivery_vault.l_stop_outlet (
    hk_link        varchar(32) primary key,
    hk_stop        varchar(32) references direct_store_delivery_vault.h_stop(hk_stop),
    hk_outlet      varchar(32) references direct_store_delivery_vault.h_outlet(hk_outlet),
    load_dts       timestamp,
    record_source  varchar(64)
);

create table if not exists direct_store_delivery_vault.l_stop_order (
    hk_link        varchar(32) primary key,
    hk_stop        varchar(32) references direct_store_delivery_vault.h_stop(hk_stop),
    hk_order       varchar(32) references direct_store_delivery_vault.h_order(hk_order),
    load_dts       timestamp,
    record_source  varchar(64)
);

create table if not exists direct_store_delivery_vault.l_settlement_route (
    hk_link        varchar(32) primary key,
    hk_settlement  varchar(32) references direct_store_delivery_vault.h_settlement(hk_settlement),
    hk_route       varchar(32) references direct_store_delivery_vault.h_route(hk_route),
    hk_driver      varchar(32) references direct_store_delivery_vault.h_driver(hk_driver),
    hk_vehicle     varchar(32) references direct_store_delivery_vault.h_vehicle(hk_vehicle),
    settlement_date date,
    load_dts       timestamp,
    record_source  varchar(64)
);

create table if not exists direct_store_delivery_vault.l_audit_stop (
    hk_link        varchar(32) primary key,
    hk_audit       varchar(32) references direct_store_delivery_vault.h_audit(hk_audit),
    hk_stop        varchar(32) references direct_store_delivery_vault.h_stop(hk_stop),
    load_dts       timestamp,
    record_source  varchar(64)
);

create table if not exists direct_store_delivery_vault.l_driver_vehicle_day (
    hk_link        varchar(32) primary key,
    hk_driver      varchar(32) references direct_store_delivery_vault.h_driver(hk_driver),
    hk_vehicle     varchar(32) references direct_store_delivery_vault.h_vehicle(hk_vehicle),
    activity_date  date,
    load_dts       timestamp,
    record_source  varchar(64)
);

-- ---------- SATELLITES ----------
create table if not exists direct_store_delivery_vault.s_route_descriptive (
    hk_route             varchar(32) references direct_store_delivery_vault.h_route(hk_route),
    load_dts             timestamp,
    branch_id            varchar(32),
    route_code           varchar(16),
    route_type           varchar(16),
    service_days         varchar(16),
    planned_stops        smallint,
    planned_miles        numeric(8,2),
    planned_duration_min integer,
    vehicle_class        varchar(16),
    status               varchar(16),
    effective_from       date,
    effective_to         date,
    record_source        varchar(64),
    primary key (hk_route, load_dts)
);

create table if not exists direct_store_delivery_vault.s_driver_descriptive (
    hk_driver        varchar(32) references direct_store_delivery_vault.h_driver(hk_driver),
    load_dts         timestamp,
    branch_id        varchar(32),
    employee_number  varchar(32),
    cdl_class        varchar(4),
    cdl_expiry       date,
    tenure_years     numeric(5,2),
    eld_device_id    varchar(64),
    home_terminal    varchar(32),
    pay_class        varchar(16),
    status           varchar(16),
    record_source    varchar(64),
    primary key (hk_driver, load_dts)
);

create table if not exists direct_store_delivery_vault.s_vehicle_descriptive (
    hk_vehicle           varchar(32) references direct_store_delivery_vault.h_vehicle(hk_vehicle),
    load_dts             timestamp,
    branch_id            varchar(32),
    vin                  varchar(17),
    make                 varchar(32),
    model                varchar(32),
    year                 smallint,
    vehicle_class        varchar(16),
    payload_lbs          integer,
    refrigerated         boolean,
    telematics_provider  varchar(32),
    status               varchar(16),
    record_source        varchar(64),
    primary key (hk_vehicle, load_dts)
);

create table if not exists direct_store_delivery_vault.s_stop_status (
    hk_stop          varchar(32) references direct_store_delivery_vault.h_stop(hk_stop),
    load_dts         timestamp,
    planned_arrival  timestamp,
    actual_arrival   timestamp,
    planned_departure timestamp,
    actual_departure timestamp,
    dwell_minutes    integer,
    status           varchar(16),
    skip_reason      varchar(64),
    actual_sequence  smallint,
    record_source    varchar(64),
    primary key (hk_stop, load_dts)
);

create table if not exists direct_store_delivery_vault.s_order_state (
    hk_order             varchar(32) references direct_store_delivery_vault.h_order(hk_order),
    load_dts             timestamp,
    order_type           varchar(16),
    requested_delivery_date date,
    total_cases          integer,
    total_units          integer,
    net_amount_cents     bigint,
    payment_terms        varchar(16),
    status               varchar(16),
    record_source        varchar(64),
    primary key (hk_order, load_dts)
);

create table if not exists direct_store_delivery_vault.s_settlement_state (
    hk_settlement              varchar(32) references direct_store_delivery_vault.h_settlement(hk_settlement),
    load_dts                   timestamp,
    total_invoiced_cents       bigint,
    total_collected_cash_cents bigint,
    total_collected_check_cents bigint,
    total_collected_eft_cents  bigint,
    returns_credit_cents       bigint,
    spoilage_credit_cents      bigint,
    variance_cents             bigint,
    variance_reason            varchar(64),
    status                     varchar(16),
    closed_at                  timestamp,
    approved_by                varchar(64),
    record_source              varchar(64),
    primary key (hk_settlement, load_dts)
);

create table if not exists direct_store_delivery_vault.s_perfect_store_score (
    hk_audit                  varchar(32) references direct_store_delivery_vault.h_audit(hk_audit),
    load_dts                  timestamp,
    distribution_score        numeric(5,2),
    share_of_cooler_pct       numeric(5,2),
    planogram_compliance_pct  numeric(5,2),
    price_compliance_pct      numeric(5,2),
    promo_compliance_pct      numeric(5,2),
    freshness_score           numeric(5,2),
    perfect_store_score       numeric(5,2),
    oos_count                 smallint,
    record_source             varchar(64),
    primary key (hk_audit, load_dts)
);

create table if not exists direct_store_delivery_vault.s_outlet_descriptive (
    hk_outlet        varchar(32) references direct_store_delivery_vault.h_outlet(hk_outlet),
    load_dts         timestamp,
    gln              varchar(13),
    account_id       varchar(32),
    state_region     varchar(8),
    format           varchar(32),
    record_source    varchar(64),
    primary key (hk_outlet, load_dts)
);
