-- Advertiser dimension.
{{ config(materialized='table') }}

with hub as (select * from {{ ref('int_programmatic_advertising__hub_advertiser') }}),
     stg as (select * from {{ ref('stg_programmatic_advertising__advertiser') }})

select
    h.h_advertiser_hk      as advertiser_key,
    h.advertiser_bk        as advertiser_id,
    s.advertiser_name,
    s.iab_categories,
    s.country_iso,
    s.tier,
    h.load_date            as dim_loaded_at,
    true                   as is_current
from hub h
left join stg s on s.advertiser_id = h.advertiser_bk
