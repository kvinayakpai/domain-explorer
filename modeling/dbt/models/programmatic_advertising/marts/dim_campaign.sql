-- Campaign dimension; FK to dim_advertiser.
{{ config(materialized='table') }}

with hub as (select * from {{ ref('int_programmatic_advertising__hub_campaign') }}),
     sat as (select * from {{ ref('int_programmatic_advertising__sat_campaign_state') }}),
     stg as (select * from {{ ref('stg_programmatic_advertising__campaign') }}),
     a   as (select * from {{ ref('dim_advertiser') }})

select
    h.h_campaign_hk         as campaign_key,
    h.campaign_bk           as campaign_id,
    a.advertiser_key,
    stg.advertiser_id,
    sat.campaign_name,
    sat.objective,
    sat.bid_strategy,
    sat.budget_total_usd,
    sat.budget_daily_usd,
    sat.start_date,
    sat.end_date,
    sat.status,
    h.load_date             as dim_loaded_at,
    true                    as is_current
from hub h
left join sat on sat.h_campaign_hk = h.h_campaign_hk
left join stg on stg.campaign_id   = h.campaign_bk
left join a   on a.advertiser_id   = stg.advertiser_id
