-- Staging: FIX-style orders.
{{ config(materialized='view') }}

select
    cast(order_id              as varchar)   as order_id,
    cast(cl_ord_id             as varchar)   as cl_ord_id,
    cast(instrument_id         as varchar)   as instrument_id,
    cast(account_id            as varchar)   as account_id,
    cast(submitting_party_id   as varchar)   as submitting_party_id,
    cast(side                  as varchar)   as side,
    cast(ord_type              as varchar)   as ord_type,
    cast(time_in_force         as varchar)   as time_in_force,
    cast(qty                   as double)    as qty,
    cast(limit_price           as double)    as limit_price,
    cast(placed_at             as timestamp) as placed_at,
    cast(status                as varchar)   as status
from {{ source('capital_markets', 'order') }}
