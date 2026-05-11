-- Staging: impression delivery event with viewability + IVT classification.
{{ config(materialized='view') }}

select
    cast(impression_event_id as varchar)   as impression_event_id,
    cast(request_id          as varchar)   as request_id,
    cast(bid_id              as varchar)   as bid_id,
    cast(served              as boolean)   as served,
    cast(served_at           as timestamp) as served_at,
    cast(measurable          as boolean)   as measurable,
    cast(viewable            as boolean)   as viewable,
    cast(viewable_pixels_pct as double)    as viewable_pixels_pct,
    cast(viewable_seconds    as double)    as viewable_seconds,
    cast(ivt_flag            as boolean)   as ivt_flag,
    cast(ivt_classification  as varchar)   as ivt_classification,
    cast(render_ms           as integer)   as render_ms
from {{ source('programmatic_advertising', 'impression_event') }}
