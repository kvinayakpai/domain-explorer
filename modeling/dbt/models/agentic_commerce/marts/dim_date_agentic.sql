{{ config(materialized='table') }}

with day_seq as (
    select cast('2025-06-01' as date) + interval (n) day as cal_date
    from range(0, 730) t(n)
)

select
    cast(strftime(cal_date, '%Y%m%d') as integer) as date_key,
    cal_date,
    extract('dow' from cal_date)                   as day_of_week,
    strftime(cal_date, '%A')                       as day_name,
    extract('month' from cal_date)                 as month,
    strftime(cal_date, '%B')                       as month_name,
    extract('quarter' from cal_date)               as quarter,
    extract('year' from cal_date)                  as year,
    case when extract('dow' from cal_date) in (0, 6) then true else false end as is_weekend
from day_seq
