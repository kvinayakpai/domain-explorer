-- Staging: settlement events tying payments to clearing batches.
{{ config(materialized='view') }}

select
    cast(settlement_id as varchar)   as settlement_id,
    cast(payment_id    as varchar)   as payment_id,
    cast(amount        as double)    as amount,
    upper(currency)                  as currency,
    cast(settled_at    as timestamp) as settled_at,
    cast(batch_id      as varchar)   as batch_id,
    cast(fee_amount    as double)    as fee_amount,
    cast(network       as varchar)   as network
from {{ source('payments', 'settlements') }}
