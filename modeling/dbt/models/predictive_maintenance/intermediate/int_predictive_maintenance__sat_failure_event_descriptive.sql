-- Vault satellite carrying Failure Event details.
{{ config(materialized='ephemeral') }}

with src as (select * from {{ ref('stg_predictive_maintenance__failure_event') }})

select
    md5(failure_event_id)                                                              as h_failure_event_hk,
    failure_ts                                                                         as load_ts,
    md5(coalesce(detected_by,'') || '|' || cast(coalesce(downtime_minutes, 0) as varchar)
        || '|' || cast(coalesce(production_loss_units, 0) as varchar)
        || '|' || cast(coalesce(cost_usd, 0) as varchar))                              as hashdiff,
    failure_ts,
    detected_by,
    downtime_minutes,
    production_loss_units,
    root_cause,
    corrective_action,
    cost_usd,
    'predictive_maintenance.failure_event'                                              as record_source
from src
