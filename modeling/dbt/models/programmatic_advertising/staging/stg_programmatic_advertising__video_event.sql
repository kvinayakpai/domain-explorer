-- Staging: VAST 4.x video tracking events.
{{ config(materialized='view') }}

select
    cast(video_event_id      as varchar)   as video_event_id,
    cast(impression_event_id as varchar)   as impression_event_id,
    cast(event_type          as varchar)   as event_type,
    cast(event_ts            as timestamp) as event_ts
from {{ source('programmatic_advertising', 'video_event') }}
