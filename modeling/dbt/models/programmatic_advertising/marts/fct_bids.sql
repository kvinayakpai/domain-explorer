-- Grain: one row per bid (one bid response can carry many bids).
{{ config(materialized='table') }}

with b   as (select * from {{ ref('stg_programmatic_advertising__bid') }}),
     r   as (select request_id, received_at, country_iso from {{ ref('stg_programmatic_advertising__bid_request') }}),
     bre as (select response_id, dsp_id from {{ ref('stg_programmatic_advertising__bid_response') }}),
     d   as (select * from {{ ref('dim_dsp') }}),
     a   as (select * from {{ ref('dim_advertiser') }}),
     ca  as (select * from {{ ref('dim_campaign') }}),
     cr  as (select * from {{ ref('dim_creative') }})

select
    md5(b.bid_id)                                                              as bid_key,
    b.bid_id,
    b.response_id,
    b.request_id,
    md5(b.request_id)                                                          as request_key,
    b.imp_id,
    a.advertiser_key,
    b.advertiser_id,
    cr.creative_key,
    b.creative_id,
    ca.campaign_key,
    d.dsp_key,
    bre.dsp_id,
    b.bid_price_cpm,
    b.bid_price_cpm / 1000.0                                                   as bid_price_per_imp,
    b.currency,
    b.deal_id,
    b.iab_categories,
    b.status                                                                    as bid_status,
    case when b.status = 'won'    then true else false end                      as is_won,
    case when b.status = 'lost'   then true else false end                      as is_lost,
    cast({{ format_date('r.received_at', '%Y%m%d') }} as integer)                          as request_date_key,
    r.received_at                                                               as request_received_at,
    r.country_iso
from b
left join r   on r.request_id    = b.request_id
left join bre on bre.response_id = b.response_id
left join a   on a.advertiser_id = b.advertiser_id
left join cr  on cr.creative_id  = b.creative_id
left join ca  on ca.campaign_id  = cr.campaign_id
left join d   on d.dsp_id        = bre.dsp_id
