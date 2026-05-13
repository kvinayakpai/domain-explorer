-- Conformed daily date dimension for the sop_supply_chain_planning anchor.
-- Suffix `_sop` avoids collision with the conformed dim_date used by other anchors.
-- Cross-DB portable (DuckDB + Postgres).
{{ config(materialized='table') }}

with day_seq as (
    {{ dbt_utils.date_spine(
        datepart="day",
        start_date="cast('2025-01-01' as date)",
        end_date="cast('2027-12-31' as date)"
    ) }}
)

select
    cast({{ format_date('cast(date_day as date)', '%Y%m%d') }} as integer) as date_key,
    cast(date_day as date)                                                  as cal_date,
    extract(dow     from date_day)                                          as day_of_week,
    {{ format_date('cast(date_day as date)', '%A') }}                       as day_name,
    extract(week    from date_day)                                          as iso_week,
    extract(month   from date_day)                                          as month,
    {{ format_date('cast(date_day as date)', '%B') }}                       as month_name,
    extract(quarter from date_day)                                          as quarter,
    extract(year    from date_day)                                          as year,
    cast(concat(cast(extract(year from date_day) as varchar),
                '-Q', cast(extract(quarter from date_day) as varchar)) as varchar) as fiscal_period,
    case when extract(dow from date_day) in (0, 6) then true else false end as is_weekend
from day_seq
