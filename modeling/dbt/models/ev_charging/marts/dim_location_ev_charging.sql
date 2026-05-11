-- Location dimension. Suffixed `_ev_charging` to avoid collision with
-- demand_planning.dim_location.
{{ config(materialized='table') }}

with stg as (select * from {{ ref('stg_ev_charging__location') }}),
     cpo as (select * from {{ ref('stg_ev_charging__cpo') }})

select
    md5(s.location_id)        as location_key,
    s.location_id,
    s.location_name,
    s.address_line,
    s.city,
    s.postal_code,
    s.country_code,
    s.latitude,
    s.longitude,
    s.parking_type,
    s.operational_status,
    s.cpo_id,
    c.cpo_name,
    md5(s.cpo_id)             as cpo_key,
    current_date              as dim_loaded_at
from stg s
left join cpo c on c.cpo_id = s.cpo_id
