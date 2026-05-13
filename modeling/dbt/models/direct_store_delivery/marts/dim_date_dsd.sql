-- Date dimension scoped to the direct_store_delivery window.
-- Suffix `_dsd` avoids collision with payments / merchandising / TPM dim_date.
{{ config(materialized='table') }}

with bounds as (
    select date '2025-06-01' as start_date, date '2026-12-31' as end_date
),
date_spine as (
    select cast(d as date) as cal_date
    from bounds, generate_series(bounds.start_date, bounds.end_date, interval 1 day) g(d)
)

select
    cast(strftime(cal_date, '%Y%m%d') as integer)            as date_key,
    cal_date,
    cast(extract(year    from cal_date) as smallint)         as year,
    cast(((extract(month from cal_date) - 1) / 3) + 1 as smallint) as quarter,
    cast(extract(month   from cal_date) as smallint)         as month,
    strftime(cal_date, '%B')                                  as month_name,
    cast(extract(week    from cal_date) as smallint)         as iso_week,
    cast(extract(dow     from cal_date) as smallint)         as day_of_week,
    strftime(cal_date, '%A')                                  as day_name,
    case when extract(dow from cal_date) in (0, 6)        then true  else false end as is_weekend,
    case when extract(dow from cal_date) = 0              then false else true  end as is_dsd_service_day
from date_spine
