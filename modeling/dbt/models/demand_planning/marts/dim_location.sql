-- Location dimension.
{{ config(materialized='table') }}

with hub as (select * from {{ ref('int_demand_planning__hub_location') }}),
     stg as (select * from {{ ref('stg_demand_planning__locations') }})

select
    h.h_location_hk        as location_key,
    h.location_bk          as location_id,
    s.location_name,
    s.location_type,
    s.country_code,
    s.capacity_units,
    h.load_date            as dim_loaded_at
from hub h
left join stg s on s.location_id = h.location_bk
