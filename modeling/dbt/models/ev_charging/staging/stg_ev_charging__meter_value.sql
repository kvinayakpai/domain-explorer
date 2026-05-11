{{ config(materialized='view') }}

select
    cast(meter_value_id                    as varchar)   as meter_value_id,
    cast(transaction_id                    as varchar)   as transaction_id,
    cast(sample_ts                         as timestamp) as sample_ts,
    cast(context                           as varchar)   as ocpp_context,
    cast(energy_active_import_register_kwh as double)    as energy_register_kwh,
    cast(power_active_import_kw            as double)    as power_kw,
    cast(current_import_a                  as double)    as current_a,
    cast(voltage_v                         as double)    as voltage_v,
    cast(soc_pct                           as double)    as soc_pct,
    cast(temperature_celsius               as double)    as temperature_c,
    cast({{ format_date('sample_ts', '%Y%m%d') }} as integer)       as sample_date_key
from {{ source('ev_charging', 'meter_value') }}
