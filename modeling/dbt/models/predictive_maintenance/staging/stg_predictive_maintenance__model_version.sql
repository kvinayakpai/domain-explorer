{{ config(materialized='view') }}

select
    cast(model_version_id       as varchar)    as model_version_id,
    cast(model_id               as varchar)    as model_id,
    cast(algorithm              as varchar)    as algorithm,
    cast(trained_on_from_ts     as timestamp)  as trained_on_from_ts,
    cast(trained_on_to_ts       as timestamp)  as trained_on_to_ts,
    cast(holdout_precision      as double)     as holdout_precision,
    cast(holdout_recall         as double)     as holdout_recall,
    cast(holdout_rul_mape       as double)     as holdout_rul_mape,
    cast(deployed_at            as timestamp)  as deployed_at,
    cast(deprecated_at          as timestamp)  as deprecated_at,
    cast(champion               as boolean)    as champion
from {{ source('predictive_maintenance', 'model_version') }}
