-- Vault satellite carrying booked Trade attributes.
{{ config(materialized='ephemeral') }}

with src as (select * from {{ ref('stg_capital_markets__trade') }})

select
    md5(trade_id)                                                       as h_trade_hk,
    cast(trade_date as timestamp)                                       as load_ts,
    md5(coalesce(side,'') || '|' || cast(coalesce(quantity, 0) as varchar)
        || '|' || cast(coalesce(price, 0) as varchar)
        || '|' || coalesce(currency,''))                                 as hashdiff,
    side,
    quantity,
    price,
    gross_amount,
    currency,
    venue_mic,
    settlement_date,
    'capital_markets.trade'                                              as record_source
from src
