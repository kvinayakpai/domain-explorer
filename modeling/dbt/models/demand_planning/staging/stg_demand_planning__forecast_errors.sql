-- Staging: per-forecast accuracy measurements.
{{ config(materialized='view') }}

select
    cast(error_id    as varchar)   as error_id,
    cast(forecast_id as varchar)   as forecast_id,
    cast(actual_qty  as double)    as actual_qty,
    cast(error       as double)    as forecast_error,
    cast(ape         as double)    as ape,
    cast(computed_at as timestamp) as computed_at
from {{ source('demand_planning', 'forecast_errors') }}
