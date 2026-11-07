{{ config(materialized='view') }}

-- SCADA tags at the well pads.
select
    cast(signal_id              as varchar ) as signal_id,
    cast(tag                    as varchar ) as tag,
    cast(functional_location_id as varchar ) as functional_location_id,
    cast(quantity               as varchar ) as quantity,
    cast(eng_unit               as varchar ) as eng_unit,
    cast(alarm_high             as double  ) as alarm_high,
    cast(source_system          as varchar ) as source_system,
    cast(sample_seconds         as integer ) as sample_seconds,
    cast(description            as varchar ) as description
from {{ source('upstream_artificial_lift', 'signal') }}
