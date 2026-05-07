-- Property dimension.
{{ config(materialized='table') }}

with hub as (select * from {{ ref('int_hotel_revenue_management__hub_property') }}),
     stg as (select * from {{ ref('stg_hotel_revenue_management__properties') }})

select
    h.h_property_hk    as property_key,
    h.property_bk      as property_id,
    s.property_name,
    s.city,
    s.country_code,
    s.brand,
    s.stars,
    case
        when s.stars is null then 'unknown'
        when s.stars <= 2 then 'economy'
        when s.stars =  3 then 'midscale'
        when s.stars =  4 then 'upscale'
        else 'luxury'
    end                  as property_tier,
    s.room_count,
    s.is_active,
    h.load_date          as dim_loaded_at
from hub h
left join stg s on s.property_id = h.property_bk
