-- Fact — one row per PO header. Spend cube at header grain plus cycle time,
-- touchless%, maverick%, channel mix.
{{ config(materialized='table') }}

with p as (select * from {{ ref('stg_procurement_spend_analytics__purchase_order') }}),
     pl as (
        select po_id, count(*) as line_count
        from {{ ref('stg_procurement_spend_analytics__po_line') }}
        group by po_id
     ),
     s as (select supplier_sk, supplier_id from {{ ref('dim_supplier') }}),
     ct as (select contract_sk, contract_id from {{ ref('dim_contract') }}),
     c as (select category_sk, category_code from {{ ref('dim_category_taxonomy') }}),
     cur as (select currency_sk, currency_code from {{ ref('dim_currency') }})

select
    p.po_id,
    cast({{ format_date('p.po_issued_ts', '%Y%m%d') }} as integer) as date_key,
    s.supplier_sk,
    ct.contract_sk,
    c.category_sk,
    cast(null as bigint)                            as channel_sk,
    cur.currency_sk,
    p.requisition_ts,
    p.po_issued_ts,
    cast(p.cycle_time_hours as double)              as cycle_time_hours,
    p.total_amount,
    p.total_amount_base_usd,
    coalesce(pl.line_count, 0)::smallint            as line_count,
    p.touchless,
    p.maverick_flag,
    p.payment_terms,
    p.status
from p
left join pl  on pl.po_id          = p.po_id
left join s   on s.supplier_id     = p.supplier_id
left join ct  on ct.contract_id    = p.contract_id
left join c   on c.category_code   = p.category_code
left join cur on cur.currency_code = p.total_currency
