-- =============================================================================
-- Hotel Revenue Management — dimensional mart (excerpt)
-- Star schema for occupancy, ADR, RevPAR, MPI/ARI/RGI analytics.
-- =============================================================================

create schema if not exists hotel_revenue_management_dim;

create table if not exists hotel_revenue_management_dim.dim_date (
    date_key             integer primary key,
    date_actual          date not null,
    day_of_week          smallint not null,
    is_weekend           boolean not null,
    holiday_name         varchar(64),
    fiscal_period        varchar(8)
);

create table if not exists hotel_revenue_management_dim.dim_property (
    property_key         bigint primary key,
    property_id          varchar not null,
    property_name        varchar not null,
    brand_name           varchar not null,
    chain_code           varchar(8),
    city                 varchar not null,
    country_iso2         varchar(2) not null,
    total_rooms          integer not null,
    valid_from           timestamp not null,
    valid_to             timestamp,
    is_current           boolean not null
);

create table if not exists hotel_revenue_management_dim.dim_room_type (
    room_type_key        smallint primary key,
    room_type_code       varchar(16) not null,
    description          varchar not null,
    max_occupancy        smallint not null
);

create table if not exists hotel_revenue_management_dim.dim_rate_plan (
    rate_plan_key        bigint primary key,
    rate_plan_id         varchar not null,
    rate_plan_code       varchar(16) not null,
    rate_plan_name       varchar not null,
    market_segment       varchar(32) not null
);

create table if not exists hotel_revenue_management_dim.dim_channel (
    channel_key          smallint primary key,
    channel_id           varchar not null,
    channel_name         varchar not null,
    channel_type         varchar(16) not null
);

create table if not exists hotel_revenue_management_dim.dim_guest (
    guest_key            bigint primary key,
    guest_id             varchar not null,
    loyalty_tier         varchar(16),
    country_iso2         varchar(2),
    valid_from           timestamp not null,
    valid_to             timestamp,
    is_current           boolean not null
);

create table if not exists hotel_revenue_management_dim.fact_room_night (
    stay_date_key        integer not null references hotel_revenue_management_dim.dim_date(date_key),
    property_key         bigint not null references hotel_revenue_management_dim.dim_property(property_key),
    room_type_key        smallint not null references hotel_revenue_management_dim.dim_room_type(room_type_key),
    rate_plan_key        bigint references hotel_revenue_management_dim.dim_rate_plan(rate_plan_key),
    channel_key          smallint references hotel_revenue_management_dim.dim_channel(channel_key),
    guest_key            bigint references hotel_revenue_management_dim.dim_guest(guest_key),
    rooms_sold           integer not null,
    rooms_available      integer not null,
    room_revenue         numeric(14, 2) not null,
    other_revenue        numeric(14, 2) not null default 0,
    primary key (stay_date_key, property_key, room_type_key, rate_plan_key, channel_key)
);

create table if not exists hotel_revenue_management_dim.fact_booking_curve (
    stay_date_key        integer not null references hotel_revenue_management_dim.dim_date(date_key),
    booking_date_key     integer not null references hotel_revenue_management_dim.dim_date(date_key),
    property_key         bigint not null references hotel_revenue_management_dim.dim_property(property_key),
    room_type_key        smallint not null references hotel_revenue_management_dim.dim_room_type(room_type_key),
    pickup_rooms         integer not null,
    cancellations        integer not null,
    primary key (stay_date_key, booking_date_key, property_key, room_type_key)
);

create table if not exists hotel_revenue_management_dim.fact_compset (
    week_start_key       integer not null references hotel_revenue_management_dim.dim_date(date_key),
    property_key         bigint not null references hotel_revenue_management_dim.dim_property(property_key),
    compset_revpar       numeric(10, 2) not null,
    compset_adr          numeric(10, 2) not null,
    compset_occupancy    numeric(5, 4) not null,
    property_revpar      numeric(10, 2) not null,
    property_adr         numeric(10, 2) not null,
    property_occupancy   numeric(5, 4) not null,
    mpi                  numeric(8, 4),
    ari                  numeric(8, 4),
    rgi                  numeric(8, 4),
    primary key (week_start_key, property_key)
);

create table if not exists hotel_revenue_management_dim.fact_bar_history (
    stay_date_key        integer not null references hotel_revenue_management_dim.dim_date(date_key),
    set_date_key         integer not null references hotel_revenue_management_dim.dim_date(date_key),
    property_key         bigint not null references hotel_revenue_management_dim.dim_property(property_key),
    room_type_key        smallint not null references hotel_revenue_management_dim.dim_room_type(room_type_key),
    bar_amount           numeric(10, 2) not null,
    primary key (stay_date_key, set_date_key, property_key, room_type_key)
);
