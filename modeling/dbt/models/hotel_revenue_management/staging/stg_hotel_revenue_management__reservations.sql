-- Staging: reservation header.
{{ config(materialized='view') }}

select
    cast(reservation_id as varchar)   as reservation_id,
    cast(property_id    as varchar)   as property_id,
    cast(room_type_id   as varchar)   as room_type_id,
    cast(rate_plan_id   as varchar)   as rate_plan_id,
    cast(channel_id     as varchar)   as channel_id,
    cast(guest_id       as varchar)   as guest_id,
    cast(booked_at      as timestamp) as booked_at,
    cast(arrival_date   as date)      as arrival_date,
    cast(departure_date as date)      as departure_date,
    cast(nights         as integer)   as nights,
    cast(adr            as double)    as adr,
    cast(total_amount   as double)    as total_amount,
    cast(status         as varchar)   as reservation_status,
    case
        when cast(arrival_date as date) is not null and cast(booked_at as timestamp) is not null
            then date_diff('day', cast(booked_at as timestamp)::date, cast(arrival_date as date))
    end                               as lead_time_days
from {{ source('hotel_revenue_management', 'reservations') }}
