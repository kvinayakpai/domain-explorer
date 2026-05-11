-- Staging: market-data snapshots (top-of-book).
{{ config(materialized='view') }}

select
    cast(snapshot_id   as varchar)   as snapshot_id,
    cast(instrument_id as varchar)   as instrument_id,
    cast(snapshot_ts   as timestamp) as snapshot_ts,
    cast(bid_px        as double)    as bid_px,
    cast(ask_px        as double)    as ask_px,
    cast(bid_size      as double)    as bid_size,
    cast(ask_size      as double)    as ask_size,
    cast(last_px       as double)    as last_px,
    cast(volume_today  as double)    as volume_today,
    cast(venue_mic     as varchar)   as venue_mic
from {{ source('capital_markets', 'market_data_snapshot') }}
