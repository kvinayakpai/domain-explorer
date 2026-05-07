-- Staging: SKU-level promotions.
{{ config(materialized='view') }}

select
    cast(promo_id      as varchar) as promo_id,
    cast(name          as varchar) as promo_name,
    cast(sku           as varchar) as sku,
    cast(discount_pct  as double)  as discount_pct,
    cast(start_date    as date)    as start_date,
    cast(duration_days as integer) as duration_days,
    cast(channel       as varchar) as channel,
    cast(start_date as date) + (cast(duration_days as integer) * interval 1 day) as end_date
from {{ source('merchandising', 'promotions') }}
