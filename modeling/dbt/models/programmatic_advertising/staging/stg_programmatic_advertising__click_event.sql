-- Staging: click events.
{{ config(materialized='view') }}

select
    cast(click_event_id      as varchar)   as click_event_id,
    cast(impression_event_id as varchar)   as impression_event_id,
    cast(clicked_at          as timestamp) as clicked_at,
    cast(click_x             as integer)   as click_x,
    cast(click_y             as integer)   as click_y,
    cast(click_url           as varchar)   as click_url
from {{ source('programmatic_advertising', 'click_event') }}
