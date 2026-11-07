{{ config(materialized='view') }}

-- Pump positions (SAP PM functional locations).
select
    cast(functional_location_id as varchar ) as functional_location_id,
    cast(floc_code              as varchar ) as floc_code,
    cast(tag                    as varchar ) as tag,
    cast(site_id                as varchar ) as site_id,
    cast(area                   as varchar ) as area,
    cast(process_unit           as varchar ) as process_unit,
    cast(service                as varchar ) as service,
    cast(api_610_type           as varchar ) as api_610_type,
    cast(model_required         as varchar ) as model_required,
    cast(rated_flow_m3h         as double  ) as rated_flow_m3h,
    cast(train_letter           as varchar ) as train_letter,
    cast(spare_of               as varchar ) as spare_of,
    cast(pid_drawing            as varchar ) as pid_drawing,
    cast(pid_revision           as varchar ) as pid_revision
from {{ source('refinery_operations', 'functional_location') }}
