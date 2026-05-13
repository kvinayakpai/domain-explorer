-- Vault satellite carrying Prediction payload (anomaly score / RUL / severity).
{{ config(materialized='ephemeral') }}

with src as (select * from {{ ref('stg_predictive_maintenance__prediction') }})

select
    md5(prediction_id)                                                              as h_prediction_hk,
    prediction_ts                                                                   as load_ts,
    md5(coalesce(prediction_type,'') || '|' || cast(coalesce(anomaly_score, 0) as varchar)
        || '|' || cast(coalesce(rul_hours, 0) as varchar)
        || '|' || coalesce(severity,''))                                            as hashdiff,
    prediction_ts,
    prediction_type,
    anomaly_score,
    rul_hours,
    rul_confidence_lower,
    rul_confidence_upper,
    severity,
    feature_snapshot_hash,
    'predictive_maintenance.prediction'                                              as record_source
from src
