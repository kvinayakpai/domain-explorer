-- Vault hub for BidRequest.
{{ config(materialized='ephemeral') }}

with src as (
    select request_id, received_at from {{ ref('stg_programmatic_advertising__bid_request') }}
    where request_id is not null
)

select
    md5(request_id)                                as h_bid_request_hk,
    request_id                                     as request_bk,
    min(received_at)                               as load_ts,
    'programmatic_advertising.bid_request'         as record_source
from src
group by request_id
