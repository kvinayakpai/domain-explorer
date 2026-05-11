-- Staging: trade allocations to client accounts.
{{ config(materialized='view') }}

select
    cast(allocation_id      as varchar) as allocation_id,
    cast(trade_id           as varchar) as trade_id,
    cast(client_account_id  as varchar) as client_account_id,
    cast(allocated_qty      as double)  as allocated_qty,
    cast(allocated_amount   as double)  as allocated_amount,
    cast(average_price      as double)  as average_price,
    cast(status             as varchar) as status
from {{ source('capital_markets', 'allocation') }}
