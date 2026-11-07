{{ config(materialized='view') }}

-- One string's time in one well; running runs are censored.
select
    cast(run_id                    as varchar ) as run_id,
    cast(well_id                   as varchar ) as well_id,
    cast(esp_string_id             as varchar ) as esp_string_id,
    cast(run_start                 as date    ) as run_start,
    cast(run_end                   as date    ) as run_end,
    cast(run_days                  as integer ) as run_days,
    cast(run_state                 as varchar ) as run_state,
    cast(censored                  as boolean ) as censored,
    cast(pull_reason               as varchar ) as pull_reason,
    cast(seal_built_since_aug_2025 as boolean ) as seal_built_since_aug_2025
from {{ source('upstream_artificial_lift', 'esp_run') }}
