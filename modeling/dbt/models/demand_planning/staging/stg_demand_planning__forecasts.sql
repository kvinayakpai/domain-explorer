-- Staging: statistical / manual forecasts.
{{ config(materialized='view') }}

select
    cast(forecast_id    as varchar)   as forecast_id,
    cast(item_id        as varchar)   as item_id,
    cast(location_id    as varchar)   as location_id,
    cast(horizon_weeks  as integer)   as horizon_weeks,
    cast(model          as varchar)   as model,
    cast(forecast_qty   as double)    as forecast_qty,
    cast(lower_80       as double)    as lower_80,
    cast(upper_80       as double)    as upper_80,
    cast(generated_at   as timestamp) as generated_at,
    case
        when cast(forecast_qty as double) > 0
            then (cast(upper_80 as double) - cast(lower_80 as double))
                 / cast(forecast_qty as double)
    end                              as pi_relative_width
from {{ source('demand_planning', 'forecasts') }}
