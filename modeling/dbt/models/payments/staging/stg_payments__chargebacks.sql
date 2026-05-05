-- Staging: chargeback notifications inbound from issuers.
{{ config(materialized='view') }}

select
    cast(chargeback_id as varchar)   as chargeback_id,
    cast(payment_id    as varchar)   as payment_id,
    cast(reason_code   as varchar)   as reason_code,
    cast(amount        as double)    as amount,
    cast(filed_at      as timestamp) as filed_at,
    cast(status        as varchar)   as status
from {{ source('payments', 'chargebacks') }}
