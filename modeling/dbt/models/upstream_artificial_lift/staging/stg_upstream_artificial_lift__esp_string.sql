{{ config(materialized='view') }}

-- ESP strings by serial.
select
    cast(esp_string_id as varchar ) as esp_string_id,
    cast(model         as varchar ) as model,
    cast(maker_id      as varchar ) as maker_id,
    cast(built_on      as date    ) as built_on,
    cast(shipped_on    as date    ) as shipped_on
from {{ source('upstream_artificial_lift', 'esp_string') }}
