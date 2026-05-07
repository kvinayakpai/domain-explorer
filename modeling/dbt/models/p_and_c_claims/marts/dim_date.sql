-- Conformed daily date dimension scoped to the P&C claims data window.
{{ config(materialized='table') }}

with bounds as (
    select
        coalesce(date_trunc('day', min(fnol_ts)) - interval 30 day,
                 cast('2022-01-01' as date)) as start_dt,
        coalesce(date_trunc('day', max(fnol_ts)) + interval 30 day,
                 cast('2030-12-31' as date)) as end_dt
    from {{ ref('stg_p_and_c_claims__claims') }}
),
days as (
    select cast(d as date) as date_day
    from bounds, unnest(range(start_dt, end_dt + interval 1 day, interval 1 day)) as t(d)
)

select
    cast(strftime(date_day, '%Y%m%d') as integer) as date_key,
    date_day,
    extract('year'    from date_day)              as year,
    extract('quarter' from date_day)              as quarter,
    extract('month'   from date_day)              as month,
    extract('week'    from date_day)              as iso_week,
    extract('day'     from date_day)              as day_of_month,
    extract('dow'     from date_day)              as day_of_week,
    case when extract('dow' from date_day) in (0, 6)
         then true else false end                 as is_weekend
from days
