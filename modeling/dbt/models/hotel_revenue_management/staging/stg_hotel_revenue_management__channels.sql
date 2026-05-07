-- Staging: distribution channels.
{{ config(materialized='view') }}

select
    cast(channel_id    as varchar) as channel_id,
    cast(name          as varchar) as channel_name,
    cast(category      as varchar) as channel_category,
    cast(commission_pct as double) as commission_pct,
    cast(active        as boolean) as is_active
from {{ source('hotel_revenue_management', 'channels') }}
