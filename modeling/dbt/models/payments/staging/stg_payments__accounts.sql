-- Staging: light typing on payments.accounts.
{{ config(materialized='view') }}

select
    cast(account_id   as varchar) as account_id,
    cast(customer_id  as varchar) as customer_id,
    cast(account_type as varchar) as account_type,
    upper(currency)               as currency,
    cast(open_date    as date)    as open_date,
    cast(status       as varchar) as account_status
from {{ source('payments', 'accounts') }}
