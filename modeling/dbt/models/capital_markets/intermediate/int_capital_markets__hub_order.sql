-- Vault hub for the Order business key.
{{ config(materialized='ephemeral') }}

with src as (
    select order_id, placed_at
    from {{ ref('stg_capital_markets__order') }}
    where order_id is not null
)

select
    md5(order_id)                  as h_order_hk,
    order_id                       as order_bk,
    min(placed_at)                 as load_ts,
    'capital_markets.order'        as record_source
from src
group by order_id
