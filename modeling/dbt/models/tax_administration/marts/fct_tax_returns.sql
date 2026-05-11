-- Grain: one row per filed tax return.
-- FKs: taxpayer_key, filed_date_key, form_key (primary form_code).
{{ config(materialized='table') }}

with sat as (select * from {{ ref('int_tax_administration__sat_return') }}),
     hub as (select * from {{ ref('int_tax_administration__hub_return') }}),
     l_rt as (select * from {{ ref('int_tax_administration__link_return_taxpayer') }}),
     stg as (select * from {{ ref('stg_tax_administration__return') }})

select
    h.h_return_hk                                       as return_key,
    h.return_bk                                         as return_id,
    l_rt.h_taxpayer_hk                                  as taxpayer_key,
    cast({{ format_date('s.load_ts', '%Y%m%d') }} as integer)      as filed_date_key,
    md5(s.form_type)                                    as form_key,
    s.tax_year,
    s.form_type,
    s.filing_status,
    s.submission_id,
    s.is_amended,
    s.is_extension,
    s.agi,
    s.total_income,
    s.taxable_income,
    s.total_tax,
    s.total_payments,
    s.refund_amount,
    s.balance_due,
    s.filing_method,
    s.status,
    g.days_late,
    case when g.days_late > 0 then true else false end  as is_late_filed,
    case when s.refund_amount > 0 then true else false end as has_refund,
    case when s.balance_due > 0 then true else false end   as has_balance_due
from hub h
join sat   s    on s.h_return_hk      = h.h_return_hk
left join l_rt  on l_rt.h_return_hk   = h.h_return_hk
left join stg g on g.return_id       = h.return_bk
