-- Grain: one row per click event.
{{ config(materialized='table') }}

with c as (select * from {{ ref('stg_programmatic_advertising__click_event') }}),
     i as (select impression_event_id, bid_id, request_id, served_at from {{ ref('stg_programmatic_advertising__impression_event') }}),
     b as (select bid_id, advertiser_id, creative_id from {{ ref('stg_programmatic_advertising__bid') }}),
     a as (select * from {{ ref('dim_advertiser') }}),
     cr as (select * from {{ ref('dim_creative') }})

select
    md5(c.click_event_id)                                  as click_key,
    c.click_event_id,
    c.impression_event_id,
    md5(c.impression_event_id)                             as impression_key,
    i.bid_id,
    a.advertiser_key,
    cr.creative_key,
    cast({{ format_date('c.clicked_at', '%Y%m%d') }} as integer)       as clicked_date_key,
    c.clicked_at,
    c.click_x,
    c.click_y,
    c.click_url,
    case when c.clicked_at is not null and i.served_at is not null
         then {{ dbt_utils.datediff('i.served_at', 'c.clicked_at', 'millisecond') }}
         end                                                as time_to_click_ms
from c
left join i  on i.impression_event_id = c.impression_event_id
left join b  on b.bid_id              = i.bid_id
left join a  on a.advertiser_id       = b.advertiser_id
left join cr on cr.creative_id        = b.creative_id
