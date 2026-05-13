{{ config(materialized='view') }}

select
    cast(failure_mode_id                as varchar)    as failure_mode_id,
    cast(fault_code                     as varchar)    as fault_code,
    cast(description                    as varchar)    as description,
    cast(applicable_asset_class         as varchar)    as applicable_asset_class,
    cast(characteristic_frequency_hz    as double)     as characteristic_frequency_hz,
    cast(typical_p_f_interval_hours     as integer)    as typical_p_f_interval_hours,
    cast(severity_tier                  as varchar)    as severity_tier
from {{ source('predictive_maintenance', 'failure_mode') }}
