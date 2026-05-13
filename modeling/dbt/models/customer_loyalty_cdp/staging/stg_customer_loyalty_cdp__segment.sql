{{ config(materialized='view') }}

select
    cast(segment_id              as varchar)    as segment_id,
    cast(segment_name            as varchar)    as segment_name,
    cast(segment_kind            as varchar)    as segment_kind,
    cast(definition_dsl          as varchar)    as definition_dsl,
    cast(refresh_cadence         as varchar)    as refresh_cadence,
    cast(owning_team             as varchar)    as owning_team,
    cast(activated_destinations  as varchar)    as activated_destinations,
    cast(created_at              as timestamp)  as created_at,
    cast(updated_at              as timestamp)  as updated_at,
    cast(status                  as varchar)    as status
from {{ source('customer_loyalty_cdp', 'segment') }}
