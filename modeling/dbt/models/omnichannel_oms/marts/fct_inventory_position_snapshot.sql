{{ config(materialized='table') }}

with i as (select * from {{ ref('stg_omnichannel_oms__inventory_positions') }}),
     l as (select * from {{ ref('dim_location') }}),
     p as (select * from {{ ref('dim_product_oms') }})

select
    cast({{ format_date('i.as_of_ts', '%Y%m%d') }} as varchar) || '-' || i.position_id as snapshot_id,
    cast({{ format_date('i.as_of_ts', '%Y%m%d') }} as integer) as date_key,
    l.location_sk,
    p.product_sk,
    i.on_hand_units,
    i.allocated_units,
    i.reserved_safety_units,
    i.atp_units,
    i.refresh_lag_seconds,
    i.as_of_ts
from i
left join l on l.location_id = i.location_id
left join p on p.product_id  = i.product_id
