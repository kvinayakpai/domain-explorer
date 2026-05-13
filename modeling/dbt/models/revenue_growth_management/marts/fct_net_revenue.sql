{{ config(materialized='table') }}

with s as (select * from {{ ref('stg_revenue_growth_management__sales_transactions') }}),
     a as (select * from {{ ref('dim_account_rgm') }}),
     p as (select * from {{ ref('dim_pack') }})

select
    s.transaction_id,
    cast({{ format_date('cast(s.invoice_date as date)', '%Y%m%d') }} as integer) as date_key,
    a.account_sk,
    p.pack_sk,
    s.deal_id,
    s.units,
    s.gross_revenue_cents,
    s.off_invoice_cents,
    s.rebate_accrual_cents,
    s.scan_down_cents,
    s.bill_back_cents,
    s.mcb_cents,
    s.slotting_cents,
    s.marketing_dev_funds_cents,
    s.total_gtn_cents,
    s.net_revenue_cents,
    s.cogs_cents,
    cast(s.net_revenue_cents - s.cogs_cents as bigint) as gross_margin_cents,
    s.price_realization,
    s.currency,
    s.invoice_date
from s
left join a on a.account_id = s.account_id
left join p on p.pack_id    = s.pack_id
