-- Conformed daily date dimension for the revenue_growth_management anchor.
-- Suffixed `_rgm` to avoid collision with other anchors' dim_date.
{{ config(materialized='table') }}

with day_seq as (
    {{ dbt_utils.date_spine(
        datepart="day",
        start_date="cast('2024-01-01' as date)",
        end_date="cast('2027-01-01' as date)"
    ) }}
)

select
    cast({{ format_date('cast(date_day as date)', '%Y%m%d') }} as integer) as date_key,
    cast(date_day as date)                                                  as cal_date,
    extract(dow     from date_day)                                          as day_of_week,
    {{ format_date('cast(date_day as date)', '%A') }}                       as day_name,
    extract(month   from date_day)                                          as month,
    {{ format_date('cast(date_day as date)', '%B') }}                       as month_name,
    extract(quarter from date_day)                                          as quarter,
    extract(year    from date_day)                                          as year,
    extract(year    from date_day)                                          as fiscal_year,
    extract(quarter from date_day)                                          as fiscal_quarter,
    case when extract(dow from date_day) in (0, 6) then true else false end as is_weekend
from day_seq
