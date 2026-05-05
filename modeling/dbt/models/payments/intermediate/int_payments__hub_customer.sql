-- Vault-style hub for the Customer business key.
-- One row per natural customer_id, with a hash key and load metadata.
{{ config(materialized='ephemeral') }}

with src as (
    select customer_id, signup_date
    from {{ ref('stg_payments__customers') }}
    where customer_id is not null
)

select
    md5(customer_id)                              as h_customer_hk,
    customer_id                                   as customer_bk,
    coalesce(min(signup_date), current_date)      as load_date,
    'payments.customers'                          as record_source
from src
group by customer_id
