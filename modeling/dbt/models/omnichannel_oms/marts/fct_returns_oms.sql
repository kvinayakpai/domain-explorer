{{ config(materialized='table') }}

with r as (select * from {{ ref('stg_omnichannel_oms__returns') }}),
     c as (select * from {{ ref('dim_customer_oms') }}),
     l as (select * from {{ ref('dim_location') }})

select
    r.rma_id,
    r.order_id,
    cast({{ format_date('r.initiated_at', '%Y%m%d') }} as integer) as date_key,
    c.customer_sk,
    l.location_sk                                                  as return_location_sk,
    r.return_reason,
    r.return_method,
    r.refund_method,
    r.refund_amount_minor,
    r.restock_outcome,
    r.initiated_at,
    r.refund_issued_at,
    r.return_cycle_days,
    r.is_refunded
from r
left join c on c.customer_id = r.customer_id
left join l on l.location_id = r.return_location_id
