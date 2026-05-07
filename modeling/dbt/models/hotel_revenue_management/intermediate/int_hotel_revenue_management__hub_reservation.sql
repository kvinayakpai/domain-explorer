-- Vault-style hub for Reservation.
{{ config(materialized='ephemeral') }}

with src as (
    select reservation_id, booked_at
    from {{ ref('stg_hotel_revenue_management__reservations') }}
    where reservation_id is not null
)

select
    md5(reservation_id)                       as h_reservation_hk,
    reservation_id                            as reservation_bk,
    min(booked_at)                            as load_ts,
    'hotel_revenue_management.reservations'   as record_source
from src
group by reservation_id
