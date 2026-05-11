-- Grain: one row per VAST video tracking event (start/firstQuartile/midpoint/thirdQuartile/complete).
{{ config(materialized='table') }}

with v as (select * from {{ ref('stg_programmatic_advertising__video_event') }})

select
    md5(v.video_event_id)                            as video_event_key,
    v.video_event_id,
    v.impression_event_id,
    md5(v.impression_event_id)                       as impression_key,
    v.event_type,
    cast({{ format_date('v.event_ts', '%Y%m%d') }} as integer)   as event_date_key,
    v.event_ts,
    case when v.event_type = 'start'         then true else false end as is_start,
    case when v.event_type = 'complete'      then true else false end as is_complete,
    case when v.event_type = 'firstQuartile' then true else false end as is_q1,
    case when v.event_type = 'midpoint'      then true else false end as is_q2,
    case when v.event_type = 'thirdQuartile' then true else false end as is_q3
from v
