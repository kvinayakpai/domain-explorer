-- Vault-style hub for Room Type.
{{ config(materialized='ephemeral') }}

with src as (
    select room_type_id from {{ ref('stg_hotel_revenue_management__room_types') }}
    where room_type_id is not null
    union
    select distinct room_type_id from {{ ref('stg_hotel_revenue_management__reservations') }}
    where room_type_id is not null
)

select
    md5(room_type_id)                         as h_room_type_hk,
    room_type_id                              as room_type_bk,
    current_date                              as load_date,
    'hotel_revenue_management.room_types'     as record_source
from src
group by room_type_id
