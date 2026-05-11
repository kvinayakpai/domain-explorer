-- Staging: post-click conversion events.
{{ config(materialized='view') }}

select
    cast(conversion_event_id as varchar)   as conversion_event_id,
    cast(click_event_id      as varchar)   as click_event_id,
    cast(converted_at        as timestamp) as converted_at,
    cast(conversion_type     as varchar)   as conversion_type,
    cast(value_usd           as double)    as value_usd,
    cast(attribution_model   as varchar)   as attribution_model
from {{ source('programmatic_advertising', 'conversion_event') }}
