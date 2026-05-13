{{ config(materialized='ephemeral') }}

with s as (select * from {{ ref('stg_direct_store_delivery__settlement') }})

select
    md5(coalesce(settlement_id,'') || '|' || coalesce(route_id,'')) as h_link_hk,
    md5(settlement_id)                                              as h_settlement_hk,
    md5(route_id)                                                   as h_route_hk,
    md5(driver_id)                                                  as h_driver_hk,
    md5(vehicle_id)                                                 as h_vehicle_hk,
    settlement_date,
    current_date                                                    as load_date,
    'direct_store_delivery.settlement'                              as record_source
from s
where settlement_id is not null
