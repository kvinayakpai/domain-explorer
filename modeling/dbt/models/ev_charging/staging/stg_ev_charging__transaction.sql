{{ config(materialized='view') }}

select
    cast(transaction_id   as varchar)   as transaction_id,
    cast(connector_id     as varchar)   as connector_id,
    cast(id_token         as varchar)   as id_token,
    cast(authorization_id as varchar)   as authorization_id,
    cast(started_at       as timestamp) as started_at,
    cast(stopped_at       as timestamp) as stopped_at,
    cast(duration_minutes as integer)   as duration_minutes,
    cast(energy_kwh       as double)    as energy_kwh,
    cast(soc_start_pct    as integer)   as soc_start_pct,
    cast(soc_end_pct      as integer)   as soc_end_pct,
    cast(stop_reason      as varchar)   as stop_reason,
    cast(total_cost       as double)    as total_cost,
    upper(currency)                     as currency,
    cast(tariff_id        as varchar)   as tariff_id,
    cast(status           as varchar)   as status,
    cast({{ format_date('started_at', '%Y%m%d') }} as integer) as started_date_key
from {{ source('ev_charging', 'transaction') }}
