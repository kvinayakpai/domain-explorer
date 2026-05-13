-- Satellite carrying Route descriptive attributes (insert-only, time-stamped).
{{ config(materialized='ephemeral') }}

with src as (select * from {{ ref('stg_direct_store_delivery__route') }})

select
    md5(route_id)                                                                          as h_route_hk,
    current_timestamp                                                                       as load_ts,
    md5(coalesce(route_type,'') || '|' || coalesce(service_days,'') || '|' || coalesce(vehicle_class,'') || '|' || coalesce(status,'')) as hashdiff,
    branch_id,
    route_code,
    route_type,
    service_days,
    planned_stops,
    planned_miles,
    planned_duration_min,
    vehicle_class,
    status,
    effective_from,
    effective_to,
    'direct_store_delivery.route'                                                           as record_source
from src
