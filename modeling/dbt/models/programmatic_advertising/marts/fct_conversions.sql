-- Grain: one row per conversion event.
{{ config(materialized='table') }}

with c  as (select * from {{ ref('stg_programmatic_advertising__conversion_event') }}),
     ck as (select click_event_id, impression_event_id, clicked_at from {{ ref('stg_programmatic_advertising__click_event') }}),
     ie as (select impression_event_id, bid_id from {{ ref('stg_programmatic_advertising__impression_event') }}),
     b  as (select bid_id, advertiser_id, creative_id from {{ ref('stg_programmatic_advertising__bid') }}),
     a  as (select * from {{ ref('dim_advertiser') }}),
     cr as (select * from {{ ref('dim_creative') }})

select
    md5(c.conversion_event_id)                                as conversion_key,
    c.conversion_event_id,
    c.click_event_id,
    md5(c.click_event_id)                                     as click_key,
    ck.impression_event_id,
    a.advertiser_key,
    cr.creative_key,
    cast({{ format_date('c.converted_at', '%Y%m%d') }} as integer)        as converted_date_key,
    c.converted_at,
    c.conversion_type,
    c.value_usd,
    c.attribution_model,
    case when c.converted_at is not null and ck.clicked_at is not null
         then {{ dbt_utils.datediff('ck.clicked_at', 'c.converted_at', 'second') }}
         end                                                   as time_to_convert_seconds
from c
left join ck on ck.click_event_id      = c.click_event_id
left join ie on ie.impression_event_id = ck.impression_event_id
left join b  on b.bid_id               = ie.bid_id
left join a  on a.advertiser_id        = b.advertiser_id
left join cr on cr.creative_id         = b.creative_id
