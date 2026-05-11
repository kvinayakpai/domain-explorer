-- Staging: FIX execution reports (fills).
{{ config(materialized='view') }}

select
    cast(execution_id        as varchar)   as execution_id,
    cast(order_id            as varchar)   as order_id,
    cast(exec_id             as varchar)   as exec_id,
    cast(exec_type           as varchar)   as exec_type,
    cast(ord_status          as varchar)   as ord_status,
    cast(instrument_id       as varchar)   as instrument_id,
    cast(side                as varchar)   as side,
    cast(last_qty            as double)    as last_qty,
    cast(last_px             as double)    as last_px,
    cast(exec_ts             as timestamp) as exec_ts,
    cast(venue_mic           as varchar)   as venue_mic,
    cast(liquidity_indicator as varchar)   as liquidity_indicator,
    cast(commission          as double)    as commission
from {{ source('capital_markets', 'execution') }}
