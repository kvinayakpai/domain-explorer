-- Conformed daily date dimension for the tax_administration anchor (suffixed).
-- Cross-DB portable (DuckDB + Postgres).
{{ config(materialized='table') }}

with days as (
    {{ dbt_utils.date_spine(
        datepart="day",
        start_date="cast('2022-01-01' as date)",
        end_date="cast('2031-01-01' as date)"
    ) }}
)

select
    cast({{ format_date('cast(date_day as date)', '%Y%m%d') }} as integer) as date_key,
    cast(date_day as date)                          as date_day,
    extract(year    from date_day)                  as year,
    extract(quarter from date_day)                  as quarter,
    extract(month   from date_day)                  as month,
    extract(week    from date_day)                  as iso_week,
    extract(day     from date_day)                  as day_of_month,
    extract(dow     from date_day)                  as day_of_week,
    case when extract(dow from date_day) in (0, 6) then true else false end as is_weekend,
    -- Tax-year flag = the calendar year this date belongs to (most filings
    -- happen Jan–Apr of the year *after* the tax year).
    case when extract(month from date_day) in (1,2,3,4) then true else false end as is_filing_season
from days
