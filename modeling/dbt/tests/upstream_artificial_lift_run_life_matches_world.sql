-- Domain test: the Kaplan-Meier medians computed in SQL must equal the run lives the
-- Factory to Field world reports (answer key): 780 days for earlier seal builds and
-- 290 days for seals built since 1 Aug 2025 (12 strings, 7 failed, 5 still running).
-- Returns the rows that disagree; an empty result passes.
select *
from {{ ref('kpi_esp_run_life_ual') }}
where (cohort = 'earlier builds' and km_median_run_days <> 780)
   or (cohort = 'seal built since Aug 2025'
       and (km_median_run_days <> 290 or runs <> 12 or failed <> 7 or running <> 5))
