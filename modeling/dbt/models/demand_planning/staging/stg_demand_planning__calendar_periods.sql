-- Staging: planning calendar.
{{ config(materialized='view') }}

select
    cast(period_id      as varchar) as period_id,
    cast(date           as date)    as period_date,
    cast(iso_week       as integer) as iso_week,
    cast(fiscal_quarter as integer) as fiscal_quarter,
    cast(is_weekend     as boolean) as is_weekend,
    cast(is_holiday     as boolean) as is_holiday
from {{ source('demand_planning', 'calendar_periods') }}
