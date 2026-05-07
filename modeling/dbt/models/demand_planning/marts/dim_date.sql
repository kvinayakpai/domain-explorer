-- Conformed daily date dimension. Reuses the planning calendar where present
-- and falls back to a generated daily range for any gaps.
{{ config(materialized='table') }}

with cal as (select * from {{ ref('stg_demand_planning__calendar_periods') }}),
     bounds as (
         select
             coalesce(min(period_date), cast('2018-01-01' as date)) as start_dt,
             coalesce(max(period_date), cast('2030-12-31' as date)) as end_dt
         from cal
     ),
     days as (
         select cast(d as date) as date_day
         from bounds, unnest(range(start_dt, end_dt + interval 1 day, interval 1 day)) as t(d)
     )

select
    cast(strftime(d.date_day, '%Y%m%d') as integer) as date_key,
    d.date_day,
    extract('year'    from d.date_day)              as year,
    extract('quarter' from d.date_day)              as quarter,
    extract('month'   from d.date_day)              as month,
    extract('week'    from d.date_day)              as iso_week,
    extract('day'     from d.date_day)              as day_of_month,
    extract('dow'     from d.date_day)              as day_of_week,
    coalesce(c.is_weekend,
             extract('dow' from d.date_day) in (0, 6))  as is_weekend,
    coalesce(c.is_holiday, false)                    as is_holiday,
    c.fiscal_quarter
from days d
left join cal c on c.period_date = d.date_day
