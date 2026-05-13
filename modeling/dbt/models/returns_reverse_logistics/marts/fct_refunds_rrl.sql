-- Fact — one row per refund event.
{{ config(materialized='table') }}

with r as (select * from {{ ref('stg_returns_reverse_logistics__refunds') }}),
     cust as (select * from {{ ref('dim_customer_rrl') }}),
     rma as (
         select rma_id, issued_ts as rma_issued_ts
         from {{ ref('stg_returns_reverse_logistics__return_authorizations') }}
     )

select
    r.refund_id,
    cast({{ format_date('r.issued_ts', '%Y%m%d') }} as integer)              as date_key,
    cust.customer_sk,
    r.order_id,
    r.rma_id,
    r.refund_type,
    r.refund_amount_minor,
    case r.currency
        when 'USD' then r.refund_amount_minor / 100.0
        when 'EUR' then r.refund_amount_minor / 100.0 * 1.08
        when 'GBP' then r.refund_amount_minor / 100.0 * 1.27
        when 'JPY' then r.refund_amount_minor / 100.0 * 0.0067
        when 'CAD' then r.refund_amount_minor / 100.0 * 0.74
        when 'AUD' then r.refund_amount_minor / 100.0 * 0.66
        else r.refund_amount_minor / 100.0
    end                                                                       as refund_amount_usd,
    r.restocking_fee_collected_minor,
    r.currency,
    r.payment_rail,
    r.psp_refund_id,
    r.is_returnless,
    case
        when r.issued_ts is not null and rma.rma_issued_ts is not null
        then datediff('hour', rma.rma_issued_ts, r.issued_ts)
        else null
    end                                                                       as issue_latency_hours,
    r.issued_ts                                                                as issued_at,
    r.status
from r
left join cust on cust.customer_id = r.customer_id
left join rma  on rma.rma_id       = r.rma_id
