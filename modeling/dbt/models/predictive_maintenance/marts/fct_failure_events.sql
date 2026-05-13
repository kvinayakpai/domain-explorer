-- Fact — one row per observed failure event.
-- Joins to dim_asset_pm, dim_failure_mode, dim_date_pm. Includes the
-- lead-time-to-failure measure used by pm.kpi.lead_time_to_failure.
{{ config(materialized='table') }}

with f as (select * from {{ ref('stg_predictive_maintenance__failure_event') }}),
     p as (select * from {{ ref('stg_predictive_maintenance__prediction') }}),
     a as (select * from {{ ref('dim_asset_pm') }}),
     fm as (select * from {{ ref('dim_failure_mode') }}),
     last_pred as (
        select
            asset_id,
            predicted_failure_mode_id,
            max(prediction_ts) as last_prediction_ts
        from p
        where severity in ('alarm','critical')
        group by 1, 2
     )

select
    f.failure_event_id,
    cast({{ format_date('f.failure_ts', '%Y%m%d') }} as integer) as date_key,
    a.asset_sk,
    fm.failure_mode_sk,
    f.failure_ts,
    f.detected_by,
    f.was_predicted,
    -- lead time = failure_ts - last alarm-level prediction for the same asset+mode (hours).
    case
        when lp.last_prediction_ts is not null
            then ({{ dbt_utils.datediff('lp.last_prediction_ts', 'f.failure_ts', 'minute') }} / 60.0)
    end                                                          as lead_time_hours,
    f.downtime_minutes,
    f.production_loss_units,
    f.cost_usd
from f
left join a  on a.asset_id        = f.asset_id
left join fm on fm.failure_mode_id = f.failure_mode_id
left join last_pred lp
       on lp.asset_id                  = f.asset_id
      and lp.predicted_failure_mode_id = f.failure_mode_id
      and lp.last_prediction_ts        <= f.failure_ts
