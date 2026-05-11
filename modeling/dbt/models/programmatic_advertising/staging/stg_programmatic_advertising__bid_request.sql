-- Staging: OpenRTB BidRequest.
{{ config(materialized='view') }}

select
    cast(request_id           as varchar)   as request_id,
    cast(received_at          as timestamp) as received_at,
    cast(tmax_ms              as integer)   as tmax_ms,
    cast(publisher_id         as varchar)   as publisher_id,
    cast(site_id              as varchar)   as site_id,
    cast(site_domain          as varchar)   as site_domain,
    cast(iab_content_category as varchar)   as iab_content_category,
    cast(device_type          as varchar)   as device_type,
    cast(os                   as varchar)   as os,
    cast(user_agent           as varchar)   as user_agent,
    cast(ip_class_c           as varchar)   as ip_class_c,
    upper(country)                          as country_iso,
    cast(user_id_hash         as varchar)   as user_id_hash,
    cast(consent_string       as varchar)   as consent_string,
    cast(auction_type         as integer)   as auction_type
from {{ source('programmatic_advertising', 'bid_request') }}
