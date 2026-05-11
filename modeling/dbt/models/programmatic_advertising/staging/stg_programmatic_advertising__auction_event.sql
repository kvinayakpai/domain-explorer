-- Staging: auction outcome (winning bid).
{{ config(materialized='view') }}

select
    cast(auction_event_id as varchar)   as auction_event_id,
    cast(request_id       as varchar)   as request_id,
    cast(winning_bid_id   as varchar)   as winning_bid_id,
    cast(clearing_price   as double)    as clearing_price,
    cast(auction_type     as integer)   as auction_type,
    cast(decided_at       as timestamp) as decided_at,
    cast(ssp_id           as varchar)   as ssp_id
from {{ source('programmatic_advertising', 'auction_event') }}
