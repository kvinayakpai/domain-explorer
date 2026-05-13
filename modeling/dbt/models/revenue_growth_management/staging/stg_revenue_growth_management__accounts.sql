{{ config(materialized='view') }}

select
    cast(account_id        as varchar)   as account_id,
    cast(account_name      as varchar)   as account_name,
    cast(parent_account_id as varchar)   as parent_account_id,
    cast(channel           as varchar)   as channel,
    cast(channel_tier      as varchar)   as channel_tier,
    cast(country_iso2      as varchar)   as country_iso2,
    cast(gln               as varchar)   as gln,
    cast(status            as varchar)   as status,
    cast(created_at        as timestamp) as created_at
from {{ source('revenue_growth_management', 'account') }}
