{{ config(materialized='view') }}

select
    cast(payment_id      as varchar)   as payment_id,
    cast(return_id       as varchar)   as return_id,
    cast(payment_method  as varchar)   as payment_method,
    cast(amount          as double)    as amount,
    cast(paid_at         as timestamp) as paid_at,
    cast(applied_to_year as integer)   as applied_to_year,
    cast(designated_as   as varchar)   as designated_as,
    cast(status          as varchar)   as status,
    cast({{ format_date('paid_at', '%Y%m%d') }} as integer) as paid_date_key
from {{ source('tax_administration', 'payment') }}
