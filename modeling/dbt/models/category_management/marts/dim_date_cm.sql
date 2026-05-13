-- Conformed daily date dimension for the category_management anchor.
-- Suffix _cm avoids collision with other anchors' dim_date.
{{ config(materialized='table') }}

with day_seq as (
    {{ dbt_utils.date_spine(
        datepart="day",
        start_date="cast('2025-06-01' as date)",
        end_date="cast('2027-06-01' as date)"
    ) }}
)

select
    cast({{ format_date('cast(date_day as date)', '%Y%m%d') }} as integer) as date_key,
    cast(date_day as date)                                                   as cal_date,
    extract(dow     from date_day)                                           as day_of_week,
    {{ format_date('cast(date_day as date)', '%A') }}                        as day_name,
    cast(date_trunc('week', cast(date_day as date)) as date)                  as week_start_date,
    extract(week    from date_day)                                            as week_of_year,
    extract(month   from date_day)                                            as month,
    {{ format_date('cast(date_day as date)', '%B') }}                         as month_name,
    extract(quarter from date_day)                                            as quarter,
    extract(year    from date_day)                                            as year,
    extract(year    from date_day)                                            as fiscal_year,
    extract(quarter from date_day)                                            as fiscal_quarter,
    case when extract(dow from date_day) in (0, 6) then true else false end   as is_weekend
from day_seq
