-- Staging: indemnity payments.
{{ config(materialized='view') }}

select
    cast(payment_id    as varchar)   as payment_id,
    cast(claim_line_id as varchar)   as claim_line_id,
    cast(amount        as double)    as amount,
    cast(method        as varchar)   as payment_method,
    cast(paid_at       as timestamp) as paid_at
from {{ source('p_and_c_claims', 'claim_payments') }}
