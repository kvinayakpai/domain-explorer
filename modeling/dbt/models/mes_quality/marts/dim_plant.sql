-- Plant dimension.
{{ config(materialized='table') }}

with hub as (select * from {{ ref('int_mes_quality__hub_plant') }}),
     stg as (select * from {{ ref('stg_mes_quality__plants') }})

select
    h.h_plant_hk           as plant_key,
    h.plant_bk             as plant_id,
    s.plant_name,
    s.country_iso2,
    s.region,
    s.size_sqm,
    s.active,
    h.load_date            as dim_loaded_at,
    true                   as is_current
from hub h
left join stg s on s.plant_id = h.plant_bk
