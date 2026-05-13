-- Vault link: Stop ↔ Route ↔ route_day.
{{ config(materialized='ephemeral') }}

with stops as (select * from {{ ref('stg_direct_store_delivery__stop') }})

select
    md5(coalesce(stop_id,'') || '|' || coalesce(route_id,'') || '|' || cast(coalesce(route_day, date '1900-01-01') as varchar)) as h_link_hk,
    md5(stop_id)                                  as h_stop_hk,
    md5(route_id)                                 as h_route_hk,
    route_day,
    current_date                                  as load_date,
    'direct_store_delivery.stop'                  as record_source
from stops
where stop_id is not null and route_id is not null
