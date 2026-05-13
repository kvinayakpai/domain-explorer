{{ config(materialized='view') }}

select
    cast(prediction_id                  as varchar)    as prediction_id,
    cast(asset_id                       as varchar)    as asset_id,
    cast(model_id                       as varchar)    as model_id,
    cast(model_version                  as varchar)    as model_version,
    cast(prediction_ts                  as timestamp)  as prediction_ts,
    cast(prediction_type                as varchar)    as prediction_type,
    cast(anomaly_score                  as double)     as anomaly_score,
    cast(rul_hours                      as integer)    as rul_hours,
    cast(rul_confidence_lower           as integer)    as rul_confidence_lower,
    cast(rul_confidence_upper           as integer)    as rul_confidence_upper,
    cast(predicted_failure_mode_id      as varchar)    as predicted_failure_mode_id,
    cast(severity                       as varchar)    as severity,
    cast(feature_snapshot_hash          as varchar)    as feature_snapshot_hash,
    case when severity in ('alarm','critical') then true else false end as is_actionable_alert
from {{ source('predictive_maintenance', 'prediction') }}
