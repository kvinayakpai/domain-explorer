-- Staging: OpenRTB BidResponse.
{{ config(materialized='view') }}

select
    cast(response_id           as varchar)   as response_id,
    cast(request_id            as varchar)   as request_id,
    cast(dsp_id                as varchar)   as dsp_id,
    cast(response_received_at  as timestamp) as response_received_at,
    cast(response_latency_ms   as double)    as response_latency_ms,
    cast(no_bid_reason         as varchar)   as no_bid_reason,
    cast(bid_count             as integer)   as bid_count,
    upper(currency)                          as currency
from {{ source('programmatic_advertising', 'bid_response') }}
