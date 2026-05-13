{{ config(materialized='view') }}

select
    cast(failure_event_id       as varchar)    as failure_event_id,
    cast(asset_id               as varchar)    as asset_id,
    cast(failure_mode_id        as varchar)    as failure_mode_id,
    cast(failure_ts             as timestamp)  as failure_ts,
    cast(detected_by            as varchar)    as detected_by,
    cast(downtime_minutes       as integer)    as downtime_minutes,
    cast(production_loss_units  as bigint)     as production_loss_units,
    cast(root_cause             as varchar)    as root_cause,
    cast(corrective_action      as varchar)    as corrective_action,
    cast(cost_usd               as double)     as cost_usd,
    case when detected_by = 'model_alert' then true else false end as was_predicted
from {{ source('predictive_maintenance', 'failure_event') }}
