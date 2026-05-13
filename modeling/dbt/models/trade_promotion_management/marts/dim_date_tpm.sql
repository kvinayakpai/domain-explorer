-- Date dimension scoped to the trade_promotion_management window.
-- Suffix `_tpm` avoids collision with payments / merchandising dim_date.
{{ config(materialized='table') }}

with bounds as (
    select date '2024-01-01' as start_date, date '2026-12-31' as end_date
),
date_spine as (
    select cast(d as date) as cal_date
    from bounds, generate_series(bounds.start_date, bounds.end_date, interval 1 day) g(d)
)

select
    cast(strftime(cal_date, '%Y%m%d') as integer) as date_key,
    cal_date,
    cast(extract(year from cal_date)    as smallint) as fiscal_year,
    cast(((extract(month from cal_date) - 1) / 3) + 1 as smallint) as fiscal_quarter,
    cast(extract(month from cal_date)   as smallint) as fiscal_period,
    cast(extract(week from cal_date)    as smallint) as week_of_year,
    cast(extract(dow from cal_date)     as smallint) as day_of_week,
    strftime(cal_date, '%A')                          as day_name,
    case when extract(dow from cal_date) in (0, 6) then true else false end as is_weekend,
    case when extract(dow from cal_date) in (0, 6) then false else true end as is_promo_eligible
from date_spine
