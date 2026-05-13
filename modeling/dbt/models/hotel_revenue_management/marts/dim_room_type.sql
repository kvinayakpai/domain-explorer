-- Room type dimension joined to its property.
{{ config(materialized='table') }}

with hub as (select * from {{ ref('int_hotel_revenue_management__hub_room_type') }}),
     stg as (select * from {{ ref('stg_hotel_revenue_management__room_types') }}),
     hub_p as (select * from {{ ref('int_hotel_revenue_management__hub_property') }})

select
    h.h_room_type_hk    as room_type_key,
    h.room_type_bk      as room_type_id,
    s.property_id,
    p.h_property_hk     as property_key,
    s.room_type_name,
    s.max_occupancy,
    s.room_view,
    s.size_sqm,
    h.load_date         as dim_loaded_at
from hub h
left join stg s   on s.room_type_id = h.room_type_bk
left join hub_p p on p.property_bk  = s.property_id
