-- Vault-style link between Payment and Customer (resolved via instructions+accounts).
{{ config(materialized='ephemeral') }}

with payments as (
    select payment_id, instruction_id from {{ ref('stg_payments__payments') }}
),
instr as (
    select instruction_id, source_account_id from {{ ref('stg_payments__payment_instructions') }}
),
accts as (
    select account_id, customer_id from {{ ref('stg_payments__accounts') }}
),
joined as (
    select
        p.payment_id,
        a.customer_id
    from payments p
    left join instr i on i.instruction_id = p.instruction_id
    left join accts a on a.account_id     = i.source_account_id
    where p.payment_id is not null and a.customer_id is not null
)

select
    md5(payment_id || '|' || customer_id) as l_payment_customer_hk,
    md5(payment_id)                       as h_payment_hk,
    md5(customer_id)                      as h_customer_hk,
    current_date                          as load_date,
    'payments.derived'                    as record_source
from joined
group by payment_id, customer_id
