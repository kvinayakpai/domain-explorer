-- Conformed daily date dimension for the pricing_and_promotions anchor.
-- Suffix `_pricing` avoids collision with merchandising / agentic dim_date.
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
    cast(date_day as date)                                                  as cal_date,
    extract(dow     from date_day)                                          as day_of_week,
    {{ format_date('cast(date_day as date)', '%A') }}                       as day_name,
    extract(month   from date_day)                                          as month,
    {{ format_date('cast(date_day as date)', '%B') }}                       as month_name,
    extract(quarter from date_day)                                          as quarter,
    extract(year    from date_day)                                          as year,
    cast({{ format_date('cast(date_day as date)', '%V') }} as integer)       as iso_week,
    case when extract(dow from date_day) in (0, 6) then true else false end as is_weekend,
    -- Retail promo weeks roll Sun-Sat; approximated by ISO week parity for the demo.
    case when cast({{ format_date('cast(date_day as date)', '%V') }} as integer) % 2 = 0
         then true else false end                                           as is_promo_week
from day_seq
