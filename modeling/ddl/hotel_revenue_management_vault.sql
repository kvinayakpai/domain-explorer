-- =============================================================================
-- Hotel Revenue Management — Data Vault 2.0 (excerpt)
-- Hubs / Links / Satellites for property, reservation, rate plan, channel.
-- =============================================================================

create schema if not exists hotel_revenue_management_vault;

-- Hubs
create table if not exists hotel_revenue_management_vault.hub_property (
    property_hk          bytea primary key,
    property_bk          varchar not null,
    load_dts             timestamp not null,
    rec_src              varchar not null
);

create table if not exists hotel_revenue_management_vault.hub_reservation (
    reservation_hk       bytea primary key,
    reservation_bk       varchar not null,
    load_dts             timestamp not null,
    rec_src              varchar not null
);

create table if not exists hotel_revenue_management_vault.hub_rate_plan (
    rate_plan_hk         bytea primary key,
    rate_plan_bk         varchar not null,
    load_dts             timestamp not null,
    rec_src              varchar not null
);

create table if not exists hotel_revenue_management_vault.hub_channel (
    channel_hk           bytea primary key,
    channel_bk           varchar not null,
    load_dts             timestamp not null,
    rec_src              varchar not null
);

create table if not exists hotel_revenue_management_vault.hub_guest (
    guest_hk             bytea primary key,
    guest_bk             varchar not null,
    load_dts             timestamp not null,
    rec_src              varchar not null
);

create table if not exists hotel_revenue_management_vault.hub_room (
    room_hk              bytea primary key,
    room_bk              varchar not null,
    load_dts             timestamp not null,
    rec_src              varchar not null
);

-- Links
create table if not exists hotel_revenue_management_vault.link_reservation_property (
    link_hk              bytea primary key,
    reservation_hk       bytea not null references hotel_revenue_management_vault.hub_reservation(reservation_hk),
    property_hk          bytea not null references hotel_revenue_management_vault.hub_property(property_hk),
    rate_plan_hk         bytea not null references hotel_revenue_management_vault.hub_rate_plan(rate_plan_hk),
    channel_hk           bytea not null references hotel_revenue_management_vault.hub_channel(channel_hk),
    guest_hk             bytea references hotel_revenue_management_vault.hub_guest(guest_hk),
    load_dts             timestamp not null,
    rec_src              varchar not null
);

create table if not exists hotel_revenue_management_vault.link_room_night (
    link_hk              bytea primary key,
    property_hk          bytea not null references hotel_revenue_management_vault.hub_property(property_hk),
    room_hk              bytea not null references hotel_revenue_management_vault.hub_room(room_hk),
    reservation_hk       bytea references hotel_revenue_management_vault.hub_reservation(reservation_hk),
    stay_date            date not null,
    load_dts             timestamp not null,
    rec_src              varchar not null
);

create table if not exists hotel_revenue_management_vault.link_bar_rate (
    link_hk              bytea primary key,
    property_hk          bytea not null references hotel_revenue_management_vault.hub_property(property_hk),
    room_type_code       varchar(16) not null,
    stay_date            date not null,
    load_dts             timestamp not null,
    rec_src              varchar not null
);

-- Satellites
create table if not exists hotel_revenue_management_vault.sat_property_descriptive (
    property_hk          bytea not null references hotel_revenue_management_vault.hub_property(property_hk),
    load_dts             timestamp not null,
    load_end_dts         timestamp,
    hash_diff            bytea not null,
    property_name        varchar not null,
    brand_id             varchar not null,
    chain_code           varchar(8),
    city                 varchar not null,
    country_iso2         varchar(2) not null,
    total_rooms          integer not null,
    rec_src              varchar not null,
    primary key (property_hk, load_dts)
);

create table if not exists hotel_revenue_management_vault.sat_reservation_state (
    reservation_hk       bytea not null references hotel_revenue_management_vault.hub_reservation(reservation_hk),
    load_dts             timestamp not null,
    load_end_dts         timestamp,
    hash_diff            bytea not null,
    arrival_date         date not null,
    departure_date       date not null,
    booking_status       varchar(16) not null,
    total_amount         numeric(12, 2) not null,
    currency             varchar(3) not null,
    rec_src              varchar not null,
    primary key (reservation_hk, load_dts)
);

create table if not exists hotel_revenue_management_vault.sat_rate_plan_descriptive (
    rate_plan_hk         bytea not null references hotel_revenue_management_vault.hub_rate_plan(rate_plan_hk),
    load_dts             timestamp not null,
    load_end_dts         timestamp,
    hash_diff            bytea not null,
    rate_plan_code       varchar(16) not null,
    rate_plan_name       varchar not null,
    market_segment       varchar(32) not null,
    is_packageable       boolean not null,
    rec_src              varchar not null,
    primary key (rate_plan_hk, load_dts)
);

create table if not exists hotel_revenue_management_vault.sat_bar_rate (
    link_hk              bytea not null,
    load_dts             timestamp not null,
    load_end_dts         timestamp,
    hash_diff            bytea not null,
    bar_amount           numeric(10, 2) not null,
    currency             varchar(3) not null,
    set_by               varchar not null,
    rec_src              varchar not null,
    primary key (link_hk, load_dts)
);

create table if not exists hotel_revenue_management_vault.sat_room_night_state (
    link_hk              bytea not null,
    load_dts             timestamp not null,
    load_end_dts         timestamp,
    hash_diff            bytea not null,
    rate_amount          numeric(10, 2),
    is_occupied          boolean not null,
    rec_src              varchar not null,
    primary key (link_hk, load_dts)
);
