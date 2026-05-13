-- Vault hub for the Prediction business key.
{{ config(materialized='ephemeral') }}

with src as (
    select prediction_id
    from {{ ref('stg_predictive_maintenance__prediction') }}
    where prediction_id is not null
)

select
    md5(prediction_id)                          as h_prediction_hk,
    prediction_id                               as prediction_bk,
    current_date                                as load_date,
    'predictive_maintenance.prediction'         as record_source
from src
group by prediction_id
