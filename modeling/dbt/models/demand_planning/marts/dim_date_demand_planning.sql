-- Conformed daily date dimension. Reuses the planning calendar where present
-- and falls back to a generated daily range for any gaps.
-- Cross-DB portable (DuckDB + Postgres).
{{ config(materialized='table') }}

with days as (
    {{ dbt_utils.date_spine(
        datepart="day",
        start_date="cast('2018-01-01' as date)",
        end_date="cast('2031-01-01' as date)"
    ) }}
),
cal as (select * from {{ ref('stg_demand_planning__calendar_periods') }})

select
    cast({{ format_date('cast(d.date_day as date)', '%Y%m%d') }} as integer) as date_key,
    cast(d.date_day as date)                          as date_day,
    extract(year    from d.date_day)                  as year,
    extract(quarter from d.date_day)                  as quarter,
    extract(month   from d.date_day)                  as month,
    extract(week    from d.date_day)                  as iso_week,
    extract(day     from d.date_day)                  as day_of_month,
    extract(dow     from d.date_day)                  as day_of_week,
    coalesce(c.is_weekend,
             case when extract(dow from d.date_day) in (0, 6)
                  then true else false end)            as is_weekend,
    coalesce(c.is_holiday, false)                      as is_holiday,
    c.fiscal_quarter
from days d
left join cal c on c.period_date = cast(d.date_day as date)
