{{ config(materialized='view') }}

-- Daily aggregates per SCADA tag.
select
    cast(signal_id    as varchar ) as signal_id,
    cast(day          as date    ) as day,
    cast(mean_value   as double  ) as mean_value,
    cast(min_value    as double  ) as min_value,
    cast(max_value    as double  ) as max_value,
    cast(sample_count as integer ) as sample_count
from {{ source('upstream_artificial_lift', 'signal_daily') }}
