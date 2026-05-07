-- Staging: demand-affecting promotions.
{{ config(materialized='view') }}

select
    cast(promo_id      as varchar) as promo_id,
    cast(item_id       as varchar) as item_id,
    cast(promo_type    as varchar) as promo_type,
    cast(lift_pct      as double)  as lift_pct,
    cast(start_date    as date)    as start_date,
    cast(duration_days as integer) as duration_days,
    cast(start_date as date) + (cast(duration_days as integer) * interval 1 day) as end_date
from {{ source('demand_planning', 'promotions') }}
