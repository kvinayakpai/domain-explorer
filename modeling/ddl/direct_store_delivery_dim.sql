-- =============================================================================
-- Direct Store Delivery — Kimball dimensional schema
-- Star: fct_orders_dsd, fct_stops_dsd, fct_settlements_dsd,
--       fct_perfect_store_audits, fct_route_telemetry_summary
-- Conformed dims: dim_date_dsd, dim_product_dsd, dim_route, dim_driver,
--                 dim_vehicle, dim_stop, dim_outlet_dsd, dim_account_dsd
-- The `_dsd` suffix avoids collision with other anchors' dim_date / dim_product /
-- dim_account that already exist in trade_promotion_management and merchandising.
-- =============================================================================

create schema if not exists direct_store_delivery_dim;

-- ---------- DIMS ----------
create table if not exists direct_store_delivery_dim.dim_date_dsd (
    date_key      integer primary key,           -- yyyymmdd
    cal_date      date,
    day_of_week   smallint,
    day_name      varchar(12),
    iso_week      smallint,
    month         smallint,
    month_name    varchar(12),
    quarter       smallint,
    year          smallint,
    is_weekend    boolean,
    is_dsd_service_day boolean                    -- DSD branches typically run Mon-Sat
);

create table if not exists direct_store_delivery_dim.dim_product_dsd (
    product_sk         bigint primary key,
    sku_id             varchar(32) unique,
    gtin               varchar(14),
    brand              varchar(64),
    category           varchar(64),
    subcategory        varchar(64),
    pack_size          varchar(32),
    case_pack_qty      smallint,
    list_price_cents   bigint,
    srp_cents          bigint,
    cost_of_goods_cents bigint,
    refrigerated       boolean,
    perishable         boolean,
    status             varchar(16)
);

create table if not exists direct_store_delivery_dim.dim_route (
    route_sk             bigint primary key,
    route_id             varchar(32) unique,
    branch_id            varchar(32),
    route_code           varchar(16),
    route_type           varchar(16),
    service_days         varchar(16),
    vehicle_class        varchar(16),
    planned_stops        smallint,
    planned_miles        numeric(8,2),
    planned_duration_min integer,
    status               varchar(16),
    valid_from           timestamp,
    valid_to             timestamp,
    is_current           boolean
);

create table if not exists direct_store_delivery_dim.dim_driver (
    driver_sk     bigint primary key,
    driver_id     varchar(32) unique,
    branch_id     varchar(32),
    employee_number varchar(32),
    full_name     varchar(255),
    cdl_class     varchar(4),
    tenure_years  numeric(5,2),
    pay_class     varchar(16),
    home_terminal varchar(32),
    status        varchar(16),
    valid_from    timestamp,
    valid_to      timestamp,
    is_current    boolean
);

create table if not exists direct_store_delivery_dim.dim_vehicle (
    vehicle_sk          bigint primary key,
    vehicle_id          varchar(32) unique,
    branch_id           varchar(32),
    vin                 varchar(17),
    make                varchar(32),
    model               varchar(32),
    year                smallint,
    vehicle_class       varchar(16),
    payload_lbs         integer,
    bay_count           smallint,
    refrigerated        boolean,
    telematics_provider varchar(32),
    status              varchar(16)
);

create table if not exists direct_store_delivery_dim.dim_stop (
    stop_sk           bigint primary key,
    stop_id           varchar(40) unique,
    route_id          varchar(32),
    outlet_id         varchar(32),
    gln               varchar(13),
    route_day_key     integer,
    planned_sequence  smallint,
    presell_flag      boolean
);

create table if not exists direct_store_delivery_dim.dim_outlet_dsd (
    outlet_sk      bigint primary key,
    outlet_id      varchar(32) unique,
    account_id     varchar(32),
    gln            varchar(13),
    state_region   varchar(8),
    postal_code    varchar(16),
    format         varchar(32),
    lat            numeric(9,6),
    lng            numeric(9,6),
    status         varchar(16)
);

create table if not exists direct_store_delivery_dim.dim_account_dsd (
    account_sk      bigint primary key,
    account_id      varchar(32) unique,
    account_name    varchar(255),
    channel         varchar(32),
    country_iso2    varchar(2),
    trade_terms_code varchar(16),
    status          varchar(16)
);

-- ---------- FACTS ----------
create table if not exists direct_store_delivery_dim.fct_orders_dsd (
    order_line_id          varchar(40) primary key,
    date_key               integer references direct_store_delivery_dim.dim_date_dsd(date_key),
    product_sk             bigint  references direct_store_delivery_dim.dim_product_dsd(product_sk),
    route_sk               bigint  references direct_store_delivery_dim.dim_route(route_sk),
    driver_sk              bigint  references direct_store_delivery_dim.dim_driver(driver_sk),
    vehicle_sk             bigint  references direct_store_delivery_dim.dim_vehicle(vehicle_sk),
    stop_sk                bigint  references direct_store_delivery_dim.dim_stop(stop_sk),
    outlet_sk              bigint  references direct_store_delivery_dim.dim_outlet_dsd(outlet_sk),
    account_sk             bigint  references direct_store_delivery_dim.dim_account_dsd(account_sk),
    order_id               varchar(40),
    order_type             varchar(16),
    ordered_units          integer,
    ordered_cases          integer,
    delivered_units        integer,
    delivered_cases        integer,
    returned_units         integer,
    short_units            integer,
    unit_price_cents       bigint,
    extended_amount_cents  bigint,
    cogs_cents             bigint,
    gross_profit_cents     bigint,
    is_presell             boolean,
    is_swap                boolean,
    promo_tactic_id        varchar(32)
);

create table if not exists direct_store_delivery_dim.fct_stops_dsd (
    stop_id                 varchar(40) primary key,
    date_key                integer references direct_store_delivery_dim.dim_date_dsd(date_key),
    route_sk                bigint  references direct_store_delivery_dim.dim_route(route_sk),
    driver_sk               bigint  references direct_store_delivery_dim.dim_driver(driver_sk),
    vehicle_sk              bigint  references direct_store_delivery_dim.dim_vehicle(vehicle_sk),
    outlet_sk               bigint  references direct_store_delivery_dim.dim_outlet_dsd(outlet_sk),
    planned_sequence        smallint,
    actual_sequence         smallint,
    sequence_drift          smallint,
    planned_arrival         timestamp,
    actual_arrival          timestamp,
    on_time_window_minutes  integer,
    is_on_time              boolean,
    dwell_minutes           integer,
    is_skipped              boolean,
    is_completed            boolean,
    cases_delivered         integer,
    units_delivered         integer,
    net_sales_cents         bigint
);

create table if not exists direct_store_delivery_dim.fct_settlements_dsd (
    settlement_id              varchar(40) primary key,
    date_key                   integer references direct_store_delivery_dim.dim_date_dsd(date_key),
    route_sk                   bigint  references direct_store_delivery_dim.dim_route(route_sk),
    driver_sk                  bigint  references direct_store_delivery_dim.dim_driver(driver_sk),
    vehicle_sk                 bigint  references direct_store_delivery_dim.dim_vehicle(vehicle_sk),
    total_invoiced_cents       bigint,
    total_collected_cash_cents bigint,
    total_collected_check_cents bigint,
    total_collected_eft_cents  bigint,
    total_charge_account_cents bigint,
    returns_credit_cents       bigint,
    spoilage_credit_cents      bigint,
    variance_cents             bigint,
    abs_variance_cents         bigint,
    is_balanced                boolean,
    is_disputed                boolean,
    closed_at                  timestamp
);

create table if not exists direct_store_delivery_dim.fct_perfect_store_audits (
    audit_id                 varchar(40) primary key,
    date_key                 integer references direct_store_delivery_dim.dim_date_dsd(date_key),
    outlet_sk                bigint  references direct_store_delivery_dim.dim_outlet_dsd(outlet_sk),
    route_sk                 bigint  references direct_store_delivery_dim.dim_route(route_sk),
    driver_sk                bigint  references direct_store_delivery_dim.dim_driver(driver_sk),
    distribution_score       numeric(5,2),
    share_of_cooler_pct      numeric(5,2),
    planogram_compliance_pct numeric(5,2),
    price_compliance_pct     numeric(5,2),
    promo_compliance_pct     numeric(5,2),
    freshness_score          numeric(5,2),
    perfect_store_score      numeric(5,2),
    oos_count                smallint,
    is_above_threshold       boolean
);

create table if not exists direct_store_delivery_dim.fct_route_telemetry_daily (
    vehicle_sk          bigint references direct_store_delivery_dim.dim_vehicle(vehicle_sk),
    driver_sk           bigint references direct_store_delivery_dim.dim_driver(driver_sk),
    date_key            integer references direct_store_delivery_dim.dim_date_dsd(date_key),
    miles_driven        numeric(8,2),
    drive_minutes       integer,
    on_duty_minutes     integer,
    fuel_used_gal       numeric(8,2),
    harsh_brake_count   integer,
    harsh_accel_count   integer,
    over_speed_count    integer,
    hos_violation_flag  boolean,
    primary key (vehicle_sk, driver_sk, date_key)
);

-- Helpful indexes
create index if not exists ix_fct_orders_dsd_route   on direct_store_delivery_dim.fct_orders_dsd(route_sk, date_key);
create index if not exists ix_fct_orders_dsd_outlet  on direct_store_delivery_dim.fct_orders_dsd(outlet_sk, date_key);
create index if not exists ix_fct_stops_dsd_date     on direct_store_delivery_dim.fct_stops_dsd(date_key);
create index if not exists ix_fct_stops_dsd_route    on direct_store_delivery_dim.fct_stops_dsd(route_sk, date_key);
create index if not exists ix_fct_settlements_route  on direct_store_delivery_dim.fct_settlements_dsd(route_sk, date_key);
create index if not exists ix_fct_psaudit_outlet    on direct_store_delivery_dim.fct_perfect_store_audits(outlet_sk, date_key);
