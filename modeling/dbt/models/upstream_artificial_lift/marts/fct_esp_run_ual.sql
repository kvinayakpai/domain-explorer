-- One row per string run in a well. Running strings stay in, flagged as censored:
-- dropping them, or counting them as failures, would both bias run life.
{{ config(materialized='table') }}

select
    r.run_id,
    r.well_id                              as well_key,
    r.esp_string_id                        as esp_string_key,
    r.run_start,
    r.run_end,
    r.run_days,
    r.run_state = 'failed'                 as failed,
    r.censored,
    r.pull_reason,
    case when r.seal_built_since_aug_2025 then 'seal built since Aug 2025'
         else 'earlier builds' end         as cohort
from {{ ref('stg_upstream_artificial_lift__esp_run') }} r
