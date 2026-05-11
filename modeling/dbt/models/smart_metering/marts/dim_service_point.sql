-- Service Point dimension fed from the Vault hub + staging attributes.
{{ config(materialized='table') }}

with hub as (select * from {{ ref('int_smart_metering__hub_service_point') }}),
     stg as (select * from {{ ref('stg_smart_metering__service_point') }})

select
    h.h_service_point_hk     as service_point_key,
    h.service_point_bk       as service_point_id,
    s.premise_id,
    s.address_line,
    s.address_city,
    s.address_state,
    s.service_class,
    s.rate_schedule,
    s.feeder_id,
    s.transformer_id,
    s.latitude,
    s.longitude,
    s.active_since,
    cast({{ dbt_utils.datediff('s.active_since', 'current_date', 'day') }} / 365.25 as integer)
                             as years_in_service,
    h.load_date              as dim_loaded_at
from hub h
left join stg s on s.service_point_id = h.service_point_bk
