-- Staging: light typing on payments.payment_instructions.
{{ config(materialized='view') }}

select
    cast(instruction_id    as varchar)   as instruction_id,
    cast(source_account_id as varchar)   as source_account_id,
    cast(dest_account_id   as varchar)   as dest_account_id,
    cast(rail              as varchar)   as rail,
    cast(amount            as double)    as amount,
    upper(currency)                      as currency,
    cast(created_at        as timestamp) as created_at,
    cast(status            as varchar)   as status
from {{ source('payments', 'payment_instructions') }}
