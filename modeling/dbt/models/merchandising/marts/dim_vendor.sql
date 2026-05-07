-- Vendor dimension.
{{ config(materialized='table') }}

with hub as (select * from {{ ref('int_merchandising__hub_vendor') }}),
     stg as (select * from {{ ref('stg_merchandising__vendors') }})

select
    h.h_vendor_hk      as vendor_key,
    h.vendor_bk        as vendor_id,
    s.vendor_name,
    s.country_code,
    s.tier,
    s.lead_time_days,
    s.is_active,
    h.load_date        as dim_loaded_at
from hub h
left join stg s on s.vendor_id = h.vendor_bk
