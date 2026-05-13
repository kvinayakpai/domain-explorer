-- Suffix `_pm` to avoid collision with any future model_version dim in other anchors.
{{ config(materialized='table') }}

select
    row_number() over (order by model_version_id) as model_version_sk,
    model_version_id,
    model_id,
    algorithm,
    trained_on_from_ts,
    trained_on_to_ts,
    holdout_precision,
    holdout_recall,
    holdout_rul_mape,
    deployed_at,
    deprecated_at,
    champion
from {{ ref('stg_predictive_maintenance__model_version') }}
