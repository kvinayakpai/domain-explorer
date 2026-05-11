-- Staging: creative master.
{{ config(materialized='view') }}

select
    cast(creative_id     as varchar) as creative_id,
    cast(advertiser_id   as varchar) as advertiser_id,
    cast(campaign_id     as varchar) as campaign_id,
    cast(format          as varchar) as ad_format,
    cast(width           as integer) as width,
    cast(height          as integer) as height,
    cast(duration_sec    as integer) as duration_sec,
    cast(iab_categories  as varchar) as iab_categories,
    cast(vast_version    as varchar) as vast_version,
    cast(approval_status as varchar) as approval_status
from {{ source('programmatic_advertising', 'creative') }}
