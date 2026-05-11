-- Grain: one row per OpenRTB BidRequest.
{{ config(materialized='table') }}

with r  as (select * from {{ ref('stg_programmatic_advertising__bid_request') }}),
     pb as (select * from {{ ref('dim_publisher') }}),
     resp as (
        select request_id, count(*) as response_count, sum(bid_count) as bid_count
        from {{ ref('stg_programmatic_advertising__bid_response') }}
        group by request_id
     )

select
    md5(r.request_id)                                  as request_key,
    r.request_id,
    cast({{ format_date('r.received_at', '%Y%m%d') }} as integer)  as received_date_key,
    r.received_at,
    r.tmax_ms,
    pb.publisher_key,
    r.publisher_id,
    r.site_id,
    r.site_domain,
    r.iab_content_category,
    r.device_type,
    r.os,
    r.country_iso,
    r.auction_type,
    coalesce(resp.response_count, 0)                    as response_count,
    coalesce(resp.bid_count, 0)                         as bid_count
from r
left join pb   on pb.publisher_id = r.publisher_id
left join resp on resp.request_id = r.request_id
