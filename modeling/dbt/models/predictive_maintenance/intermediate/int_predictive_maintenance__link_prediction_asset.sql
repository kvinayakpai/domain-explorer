-- Vault link: Prediction ↔ Asset ↔ Failure Mode (predicted class).
{{ config(materialized='ephemeral') }}

with p as (
    select prediction_id, asset_id, predicted_failure_mode_id
    from {{ ref('stg_predictive_maintenance__prediction') }}
    where prediction_id is not null
)

select
    md5(prediction_id || '|' || coalesce(asset_id, '') || '|' || coalesce(predicted_failure_mode_id, '')) as l_prediction_asset_hk,
    md5(prediction_id)                          as h_prediction_hk,
    md5(asset_id)                               as h_asset_hk,
    case when predicted_failure_mode_id is not null then md5(predicted_failure_mode_id) end as h_failure_mode_hk,
    current_date                                as load_date,
    'predictive_maintenance.prediction'         as record_source
from p
group by prediction_id, asset_id, predicted_failure_mode_id
