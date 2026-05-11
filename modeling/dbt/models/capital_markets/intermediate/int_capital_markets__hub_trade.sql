-- Vault hub for the Trade business key.
{{ config(materialized='ephemeral') }}

with src as (
    select trade_id, trade_date
    from {{ ref('stg_capital_markets__trade') }}
    where trade_id is not null
)

select
    md5(trade_id)                  as h_trade_hk,
    trade_id                       as trade_bk,
    min(cast(trade_date as timestamp)) as load_ts,
    'capital_markets.trade'        as record_source
from src
group by trade_id
