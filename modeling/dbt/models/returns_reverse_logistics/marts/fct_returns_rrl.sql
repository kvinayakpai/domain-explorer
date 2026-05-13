-- Fact — one row per return_item (the disposition grain).
{{ config(materialized='table') }}

with ri as (select * from {{ ref('stg_returns_reverse_logistics__return_items') }}),
     rma as (select * from {{ ref('stg_returns_reverse_logistics__return_authorizations') }}),
     cust as (select * from {{ ref('dim_customer_rrl') }}),
     prod as (select * from {{ ref('dim_product_rrl') }}),
     reas as (select * from {{ ref('dim_reason_code') }}),
     disp as (select * from {{ ref('dim_disposition') }}),
     fraud as (
         select rma_id, max(case when is_denied or is_stepup or recommendation in ('verify','deny','stepup_required') then 1 else 0 end) as is_fraud_flagged_int
         from {{ ref('stg_returns_reverse_logistics__fraud_signals') }}
         group by rma_id
     )

select
    ri.return_item_id,
    ri.rma_id,
    cast({{ format_date('rma.issued_ts', '%Y%m%d') }} as integer)            as date_key,
    cust.customer_sk,
    prod.product_sk,
    reas.reason_code_sk,
    disp.disposition_sk,
    ri.quantity,
    ri.unit_cogs_minor,
    ri.unit_retail_minor,
    -- USD pass-through for the demo
    ri.unit_cogs_minor   / 100.0                                              as cogs_usd,
    ri.unit_retail_minor / 100.0                                              as retail_usd,
    ri.condition_grade,
    rma.return_method,
    rma.return_platform,
    rma.cross_border,
    case when coalesce(fraud.is_fraud_flagged_int, 0) = 1 then true else false end as is_fraud_flagged,
    case
        when ri.disposition_decided_ts is not null and rma.issued_ts is not null
        then datediff('day', rma.issued_ts, ri.disposition_decided_ts)
        else null
    end                                                                       as days_to_disposition,
    rma.issued_ts                                                              as rma_issued_at,
    rma.issued_ts                                                              as received_at,
    ri.disposition_decided_ts                                                  as disposition_decided_at
from ri
left join rma   on rma.rma_id          = ri.rma_id
left join cust  on cust.customer_id    = rma.customer_id
left join prod  on prod.sku_id         = ri.sku_id
left join reas  on reas.reason_code_id = ri.reason_code_id
left join disp  on disp.disposition_id = ri.disposition_id
left join fraud on fraud.rma_id        = ri.rma_id
