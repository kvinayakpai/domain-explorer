{{ config(materialized='table') }}

with ol as (select * from {{ ref('stg_omnichannel_oms__order_lines') }}),
     o  as (select * from {{ ref('stg_omnichannel_oms__orders') }}),
     p  as (select * from {{ ref('dim_product_oms') }}),
     c  as (select * from {{ ref('dim_customer_oms') }})

select
    ol.order_line_id,
    ol.order_id,
    cast({{ format_date('o.captured_at', '%Y%m%d') }} as integer) as date_key,
    p.product_sk,
    c.customer_sk,
    ol.fulfillment_method,
    ol.quantity,
    ol.line_total_minor,
    ol.line_status,
    ol.is_substituted,
    ol.is_cancelled,
    ol.is_first_pick_filled
from ol
left join o on o.order_id      = ol.order_id
left join p on p.product_id    = ol.product_id
left join c on c.customer_id   = o.customer_id
