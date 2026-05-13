{{ config(materialized='table') }}

with hub as (select * from {{ ref('int_direct_store_delivery__hub_vehicle') }}),
     stg as (select * from {{ ref('stg_direct_store_delivery__vehicle') }})

select
    h.h_vehicle_hk     as vehicle_sk,
    h.vehicle_bk       as vehicle_id,
    s.branch_id,
    s.asset_tag,
    s.vin,
    s.make,
    s.model,
    s.year,
    s.vehicle_class,
    s.gvwr_lbs,
    s.payload_lbs,
    s.bay_count,
    s.refrigerated,
    s.telematics_provider,
    s.ifta_jurisdictions,
    s.status
from hub h
left join stg s on s.vehicle_id = h.vehicle_bk
