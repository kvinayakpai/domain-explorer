{{ config(materialized='table') }}

select
    row_number() over (order by failure_mode_id) as failure_mode_sk,
    failure_mode_id,
    fault_code,
    description,
    applicable_asset_class,
    characteristic_frequency_hz,
    typical_p_f_interval_hours,
    severity_tier
from {{ ref('stg_predictive_maintenance__failure_mode') }}
