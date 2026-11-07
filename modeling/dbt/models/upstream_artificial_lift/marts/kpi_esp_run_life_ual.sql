-- ual.kpi.esp_run_life_median: Kaplan-Meier median run life per cohort.
-- S(t) steps down by (n - d) / n at each failure time t, n = runs still at risk
-- (censored runs count as at risk up to their last day). The median is the first t
-- with S(t) <= 0.5; when S lands exactly on 0.5 the midpoint to the next failure
-- time is used, as in factory_to_field/analytics.py and R's survfit.
{{ config(materialized='table') }}

with runs as (
        select cohort, run_days as t, failed from {{ ref('fct_esp_run_ual') }}
     ),
     times as (
        select cohort, t, sum(case when failed then 1 else 0 end) as d, count(*) as c
        from runs group by 1, 2
     ),
     at_risk as (
        select cohort, t, d,
               sum(c) over (partition by cohort order by t desc
                            rows between unbounded preceding and current row) as n
        from times
     ),
     steps as (
        select cohort, t, d, n,
               exp(sum(case when d < n then ln(1 - d * 1.0 / n) else -1e9 end)
                   over (partition by cohort order by t
                         rows between unbounded preceding and current row)) as s
        from at_risk
        where d > 0
     ),
     ordered as (
        select *, lead(t) over (partition by cohort order by t) as next_t from steps
     ),
     median as (
        select cohort,
               min(case when abs(s - 0.5) < 1e-9 then (t + coalesce(next_t, t)) / 2.0
                        when s < 0.5 then t end) as km_median_run_days
        from ordered
        group by 1
     ),
     counts as (
        select cohort,
               count(*)                                       as runs,
               sum(case when failed then 1 else 0 end)        as failed,
               sum(case when not failed then 1 else 0 end)    as running
        from runs group by 1
     )

select c.cohort, c.runs, c.failed, c.running, m.km_median_run_days
from counts c
left join median m using (cohort)
