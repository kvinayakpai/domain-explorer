{{ config(materialized='ephemeral') }}

with src as (
    select vehicle_id from {{ ref('stg_direct_store_delivery__vehicle') }}
    where vehicle_id is not null
)

select
    md5(vehicle_id)                     as h_vehicle_hk,
    vehicle_id                          as vehicle_bk,
    current_date                        as load_date,
    'direct_store_delivery.vehicle'     as record_source
from src
group by vehicle_id
