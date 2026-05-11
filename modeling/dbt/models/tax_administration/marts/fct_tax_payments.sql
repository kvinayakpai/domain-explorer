-- Grain: one row per tax payment applied to a return.
-- Suffixed `_tax_payments` to avoid collision with payments.fct_payments.
{{ config(materialized='table') }}

with p as (select * from {{ ref('stg_tax_administration__payment') }})

select
    md5(p.payment_id)              as payment_key,
    p.payment_id,
    md5(p.return_id)               as return_key,
    p.return_id,
    p.payment_method,
    p.amount,
    p.paid_at,
    p.paid_date_key,
    p.applied_to_year,
    p.designated_as,
    p.status,
    case when p.status = 'posted' then true else false end as is_posted
from p
