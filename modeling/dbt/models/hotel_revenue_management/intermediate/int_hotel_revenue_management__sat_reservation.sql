-- Vault-style satellite carrying descriptive Reservation attributes.
{{ config(materialized='ephemeral') }}

with src as (
    select * from {{ ref('stg_hotel_revenue_management__reservations') }}
)

select
    md5(reservation_id)                                      as h_reservation_hk,
    booked_at                                                as load_ts,
    md5(coalesce(reservation_status,'') || '|' || cast(adr as varchar)
        || '|' || cast(nights as varchar) || '|'
        || coalesce(rate_plan_id,'') || '|' || coalesce(channel_id,''))
                                                             as hashdiff,
    rate_plan_id,
    channel_id,
    guest_id,
    reservation_status,
    arrival_date,
    departure_date,
    nights,
    adr,
    total_amount,
    lead_time_days,
    'hotel_revenue_management.reservations'                  as record_source
from src
