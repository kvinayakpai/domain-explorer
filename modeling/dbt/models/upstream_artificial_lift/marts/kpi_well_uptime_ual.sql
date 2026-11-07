-- ual.kpi.well_uptime per well and lift method: producing days / calendar days.
{{ config(materialized='table') }}

select
    d.well_key,
    w.lift_method,
    count(*)                                            as calendar_days,
    sum(case when d.producing then 1 else 0 end)        as producing_days,
    round(avg(case when d.producing then 1.0 else 0 end), 4) as uptime
from {{ ref('fct_well_day_ual') }} d
join {{ ref('dim_well_ual') }} w using (well_key)
group by 1, 2
