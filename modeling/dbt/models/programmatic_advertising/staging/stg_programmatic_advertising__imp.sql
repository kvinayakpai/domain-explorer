-- Staging: OpenRTB Imp object (one row per impression slot in a request).
{{ config(materialized='view') }}

select
    cast(imp_id              as varchar) as imp_id,
    cast(request_id          as varchar) as request_id,
    cast(imp_position        as integer) as imp_position,
    cast(ad_format           as varchar) as ad_format,
    cast(width               as integer) as width,
    cast(height              as integer) as height,
    cast(bidfloor_usd        as double)  as bidfloor_usd,
    cast(secure_required     as boolean) as secure_required,
    cast(video_min_duration  as integer) as video_min_duration,
    cast(video_max_duration  as integer) as video_max_duration,
    cast(instl               as boolean) as is_interstitial
from {{ source('programmatic_advertising', 'imp') }}
