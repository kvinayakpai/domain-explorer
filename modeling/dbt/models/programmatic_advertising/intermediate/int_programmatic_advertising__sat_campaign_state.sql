-- Vault satellite: Campaign mutable state.
{{ config(materialized='ephemeral') }}

with src as (select * from {{ ref('stg_programmatic_advertising__campaign') }})

select
    md5(campaign_id)                                                          as h_campaign_hk,
    cast(start_date as timestamp)                                             as load_ts,
    md5(coalesce(status,'') || '|' || coalesce(objective,'') || '|'
        || coalesce(bid_strategy,'') || '|'
        || cast(coalesce(budget_total_usd, 0) as varchar))                     as hashdiff,
    campaign_name,
    objective,
    bid_strategy,
    budget_total_usd,
    budget_daily_usd,
    start_date,
    end_date,
    status,
    'programmatic_advertising.campaign'                                        as record_source
from src
