-- Vault-style link tying Reservation -> Property + Room Type.
{{ config(materialized='ephemeral') }}

with src as (
    select reservation_id, property_id, room_type_id
    from {{ ref('stg_hotel_revenue_management__reservations') }}
    where reservation_id is not null
      and property_id  is not null
      and room_type_id is not null
)

select
    md5(reservation_id || '|' || property_id || '|' || room_type_id)
                                              as l_reservation_property_room_hk,
    md5(reservation_id)                       as h_reservation_hk,
    md5(property_id)                          as h_property_hk,
    md5(room_type_id)                         as h_room_type_hk,
    current_date                              as load_date,
    'hotel_revenue_management.reservations'   as record_source
from src
group by reservation_id, property_id, room_type_id
