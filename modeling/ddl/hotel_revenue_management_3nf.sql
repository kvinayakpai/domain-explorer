-- =============================================================================
-- Hotel Revenue Management — 3NF schema (excerpt)
-- PMS + RMS + channel manager view of inventory, rates, reservations, demand.
-- =============================================================================

create schema if not exists hotel_revenue_management_3nf;

create table if not exists hotel_revenue_management_3nf.brand (
    brand_id             varchar primary key,
    brand_name           varchar not null,
    parent_company       varchar
);

create table if not exists hotel_revenue_management_3nf.property (
    property_id          varchar primary key,
    property_name        varchar not null,
    brand_id             varchar not null references hotel_revenue_management_3nf.brand(brand_id),
    chain_code           varchar(8),
    city                 varchar not null,
    country_iso2         varchar(2) not null,
    timezone             varchar(64) not null,
    total_rooms          integer not null
);

create table if not exists hotel_revenue_management_3nf.room (
    room_id              varchar primary key,
    property_id          varchar not null references hotel_revenue_management_3nf.property(property_id),
    room_number          varchar(16) not null,
    room_type_code       varchar(16) not null,
    floor                smallint
);

create table if not exists hotel_revenue_management_3nf.room_type (
    room_type_code       varchar(16) primary key,
    description          varchar not null,
    max_occupancy        smallint not null
);

create table if not exists hotel_revenue_management_3nf.rate_plan (
    rate_plan_id         varchar primary key,
    property_id          varchar not null references hotel_revenue_management_3nf.property(property_id),
    rate_plan_code       varchar(16) not null,
    rate_plan_name       varchar not null,
    market_segment       varchar(32) not null,
    is_packageable       boolean not null default false
);

create table if not exists hotel_revenue_management_3nf.bar_rate (
    property_id          varchar not null references hotel_revenue_management_3nf.property(property_id),
    room_type_code       varchar(16) not null references hotel_revenue_management_3nf.room_type(room_type_code),
    stay_date            date not null,
    bar_amount           numeric(10, 2) not null,
    currency             varchar(3) not null,
    set_at               timestamp not null,
    set_by               varchar not null,
    primary key (property_id, room_type_code, stay_date)
);

create table if not exists hotel_revenue_management_3nf.rate_restriction (
    property_id          varchar not null references hotel_revenue_management_3nf.property(property_id),
    rate_plan_id         varchar not null references hotel_revenue_management_3nf.rate_plan(rate_plan_id),
    room_type_code       varchar(16) not null references hotel_revenue_management_3nf.room_type(room_type_code),
    stay_date            date not null,
    min_los              smallint,
    max_los              smallint,
    closed_to_arrival    boolean not null default false,
    closed_to_departure  boolean not null default false,
    primary key (property_id, rate_plan_id, room_type_code, stay_date)
);

create table if not exists hotel_revenue_management_3nf.channel (
    channel_id           varchar primary key,
    channel_name         varchar not null,
    channel_type         varchar(16) not null
);

create table if not exists hotel_revenue_management_3nf.guest (
    guest_id             varchar primary key,
    given_name           varchar not null,
    family_name          varchar not null,
    loyalty_id           varchar,
    country_iso2         varchar(2)
);

create table if not exists hotel_revenue_management_3nf.reservation (
    reservation_id       varchar primary key,
    property_id          varchar not null references hotel_revenue_management_3nf.property(property_id),
    rate_plan_id         varchar not null references hotel_revenue_management_3nf.rate_plan(rate_plan_id),
    room_type_code       varchar(16) not null references hotel_revenue_management_3nf.room_type(room_type_code),
    guest_id             varchar references hotel_revenue_management_3nf.guest(guest_id),
    channel_id           varchar not null references hotel_revenue_management_3nf.channel(channel_id),
    arrival_date         date not null,
    departure_date       date not null,
    booking_ts           timestamp not null,
    cancelled_ts         timestamp,
    booking_status       varchar(16) not null,
    total_amount         numeric(12, 2) not null,
    currency             varchar(3) not null
);

create table if not exists hotel_revenue_management_3nf.room_night (
    property_id          varchar not null references hotel_revenue_management_3nf.property(property_id),
    room_id              varchar not null references hotel_revenue_management_3nf.room(room_id),
    stay_date            date not null,
    reservation_id       varchar references hotel_revenue_management_3nf.reservation(reservation_id),
    rate_amount          numeric(10, 2),
    primary key (property_id, room_id, stay_date)
);

create table if not exists hotel_revenue_management_3nf.inventory_balance (
    property_id          varchar not null references hotel_revenue_management_3nf.property(property_id),
    room_type_code       varchar(16) not null references hotel_revenue_management_3nf.room_type(room_type_code),
    stay_date            date not null,
    rooms_available      integer not null,
    rooms_held           integer not null,
    rooms_sold           integer not null,
    overbooking_limit    smallint not null default 0,
    primary key (property_id, room_type_code, stay_date)
);

create table if not exists hotel_revenue_management_3nf.cancellation (
    cancellation_id      varchar primary key,
    reservation_id       varchar not null references hotel_revenue_management_3nf.reservation(reservation_id),
    cancelled_ts         timestamp not null,
    cancellation_fee     numeric(12, 2),
    reason_code          varchar(16)
);

create table if not exists hotel_revenue_management_3nf.no_show (
    no_show_id           varchar primary key,
    reservation_id       varchar not null references hotel_revenue_management_3nf.reservation(reservation_id),
    arrival_date         date not null,
    fee_charged          numeric(12, 2)
);

create table if not exists hotel_revenue_management_3nf.compset_benchmark (
    property_id          varchar not null references hotel_revenue_management_3nf.property(property_id),
    benchmark_week_start date not null,
    compset_revpar       numeric(10, 2) not null,
    compset_adr          numeric(10, 2) not null,
    compset_occupancy    numeric(5, 4) not null,
    primary key (property_id, benchmark_week_start)
);

create table if not exists hotel_revenue_management_3nf.demand_forecast (
    property_id          varchar not null references hotel_revenue_management_3nf.property(property_id),
    room_type_code       varchar(16) not null references hotel_revenue_management_3nf.room_type(room_type_code),
    stay_date            date not null,
    forecast_run_ts      timestamp not null,
    forecasted_rooms     integer not null,
    forecasted_revenue   numeric(12, 2) not null,
    primary key (property_id, room_type_code, stay_date, forecast_run_ts)
);

create table if not exists hotel_revenue_management_3nf.event_calendar (
    event_id             varchar primary key,
    property_id          varchar not null references hotel_revenue_management_3nf.property(property_id),
    event_name           varchar not null,
    event_start          date not null,
    event_end            date not null,
    impact_score         smallint
);
