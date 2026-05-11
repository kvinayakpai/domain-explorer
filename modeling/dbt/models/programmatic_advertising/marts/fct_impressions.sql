-- Grain: one row per delivered impression.
{{ config(materialized='table') }}

with ie as (select * from {{ ref('stg_programmatic_advertising__impression_event') }}),
     b  as (select bid_id, advertiser_id, creative_id, bid_price_cpm
            from {{ ref('stg_programmatic_advertising__bid') }}),
     a  as (select * from {{ ref('dim_advertiser') }}),
     cr as (select * from {{ ref('dim_creative') }}),
     ca as (select * from {{ ref('dim_campaign') }})

select
    md5(ie.impression_event_id)                              as impression_key,
    ie.impression_event_id,
    ie.request_id,
    md5(ie.request_id)                                       as request_key,
    ie.bid_id,
    md5(ie.bid_id)                                           as bid_key,
    a.advertiser_key,
    cr.creative_key,
    ca.campaign_key,
    cast({{ format_date('ie.served_at', '%Y%m%d') }} as integer)         as served_date_key,
    ie.served_at,
    ie.served,
    ie.measurable,
    ie.viewable,
    ie.viewable_pixels_pct,
    ie.viewable_seconds,
    ie.ivt_flag,
    ie.ivt_classification,
    ie.render_ms,
    b.bid_price_cpm,
    b.bid_price_cpm / 1000.0                                  as paid_amount_usd
from ie
left join b  on b.bid_id        = ie.bid_id
left join a  on a.advertiser_id = b.advertiser_id
left join cr on cr.creative_id  = b.creative_id
left join ca on ca.campaign_id  = cr.campaign_id
