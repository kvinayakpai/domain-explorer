-- Staging: campaign master.
{{ config(materialized='view') }}

select
    cast(campaign_id      as varchar) as campaign_id,
    cast(advertiser_id    as varchar) as advertiser_id,
    cast(name             as varchar) as campaign_name,
    cast(objective        as varchar) as objective,
    cast(budget_total_usd as double)  as budget_total_usd,
    cast(budget_daily_usd as double)  as budget_daily_usd,
    cast(start_date       as date)    as start_date,
    cast(end_date         as date)    as end_date,
    cast(bid_strategy     as varchar) as bid_strategy,
    cast(status           as varchar) as status
from {{ source('programmatic_advertising', 'campaign') }}
