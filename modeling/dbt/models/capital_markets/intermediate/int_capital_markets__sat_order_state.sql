-- Vault satellite carrying mutable Order attributes.
{{ config(materialized='ephemeral') }}

with src as (select * from {{ ref('stg_capital_markets__order') }})

select
    md5(order_id)                                                              as h_order_hk,
    placed_at                                                                  as load_ts,
    md5(coalesce(side,'') || '|' || coalesce(ord_type,'') || '|' || coalesce(time_in_force,'')
        || '|' || coalesce(status,'') || '|' || cast(coalesce(qty, 0) as varchar)
        || '|' || cast(coalesce(limit_price, 0) as varchar))                    as hashdiff,
    side,
    ord_type,
    time_in_force,
    qty,
    limit_price,
    status,
    'capital_markets.order'                                                     as record_source
from src
