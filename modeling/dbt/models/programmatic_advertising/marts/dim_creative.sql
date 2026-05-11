-- Creative dimension; FK to dim_campaign + dim_advertiser.
{{ config(materialized='table') }}

with hub as (select * from {{ ref('int_programmatic_advertising__hub_creative') }}),
     sat as (select * from {{ ref('int_programmatic_advertising__sat_creative_descriptive') }}),
     stg as (select * from {{ ref('stg_programmatic_advertising__creative') }}),
     c   as (select * from {{ ref('dim_campaign') }}),
     a   as (select * from {{ ref('dim_advertiser') }})

select
    h.h_creative_hk         as creative_key,
    h.creative_bk           as creative_id,
    c.campaign_key,
    a.advertiser_key,
    stg.campaign_id,
    stg.advertiser_id,
    sat.ad_format,
    sat.width,
    sat.height,
    sat.duration_sec,
    sat.iab_categories,
    sat.vast_version,
    sat.approval_status,
    h.load_date             as dim_loaded_at,
    true                    as is_current
from hub h
left join sat on sat.h_creative_hk = h.h_creative_hk
left join stg on stg.creative_id   = h.creative_bk
left join c   on c.campaign_id     = stg.campaign_id
left join a   on a.advertiser_id   = stg.advertiser_id
