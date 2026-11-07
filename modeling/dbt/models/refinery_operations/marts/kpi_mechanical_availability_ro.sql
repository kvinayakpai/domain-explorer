-- ref.kpi.mechanical_availability per refinery: 1 - repair days / position days
-- over the historian period (from the first history day to the as-of date).
{{ config(materialized='table') }}

with period as (
        select min(day) as first_day, cast('{{ var("ftf_as_of") }}' as date) as last_day
        from {{ ref('stg_refinery_operations__signal_daily') }}
     ),
     pos as (
        select site_id, count(*) as positions
        from {{ ref('stg_refinery_operations__functional_location') }}
        group by 1
     ),
     rep as (
        select fl.site_id, sum(f.repair_days) as repair_days
        from {{ ref('stg_refinery_operations__failure_event') }} f
        join {{ ref('stg_refinery_operations__functional_location') }} fl using (functional_location_id)
        cross join period
        where f.failed_on between period.first_day and period.last_day
        group by 1
     )

select
    pos.site_id,
    pos.positions,
    pos.positions * (date_diff('day', period.first_day, period.last_day) + 1) as position_days,
    coalesce(rep.repair_days, 0)                                             as repair_days,
    round(1 - coalesce(rep.repair_days, 0) * 1.0
          / (pos.positions * (date_diff('day', period.first_day, period.last_day) + 1)), 4) as mechanical_availability
from pos
cross join period
left join rep using (site_id)
