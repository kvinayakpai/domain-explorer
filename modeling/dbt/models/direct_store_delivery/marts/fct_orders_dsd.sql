-- Fact: one row per DSD order line. Joins dim_route, dim_driver, dim_vehicle,
--       dim_product_dsd, dim_stop, dim_outlet_dsd, dim_account_dsd, dim_date_dsd.
--       Order-level columns (presell vs deliver, swap flag) carried inline.
{{ config(materialized='table') }}

with l   as (select * from {{ ref('stg_direct_store_delivery__dsd_order_line') }}),
     o   as (select * from {{ ref('stg_direct_store_delivery__dsd_order') }}),
     s   as (select * from {{ ref('stg_direct_store_delivery__stop') }}),
     dp  as (select * from {{ ref('dim_product_dsd') }}),
     dr  as (select * from {{ ref('dim_route') }}),
     dst as (select * from {{ ref('dim_stop') }}),
     do_ as (select * from {{ ref('dim_outlet_dsd') }}),
     da  as (select * from {{ ref('dim_account_dsd') }})

select
    l.order_line_id,
    cast(strftime(o.order_date, '%Y%m%d') as integer)            as date_key,
    dp.product_sk,
    dr.route_sk,
    dst.stop_sk,
    do_.outlet_sk,
    da.account_sk,
    l.order_id,
    o.order_type,
    l.ordered_units,
    l.ordered_cases,
    l.delivered_units,
    l.delivered_cases,
    l.returned_units,
    l.short_units,
    l.unit_price_cents,
    l.extended_amount_cents,
    (l.delivered_units * dp.cost_of_goods_cents)                 as cogs_cents,
    (l.extended_amount_cents - (l.delivered_units * dp.cost_of_goods_cents)) as gross_profit_cents,
    o.is_presell,
    o.is_swap,
    l.case_fill_rate,
    l.promo_tactic_id
from l
left join o   on o.order_id    = l.order_id
left join s   on s.stop_id     = o.stop_id
left join dp  on dp.sku_id     = l.sku_id
left join dr  on dr.route_id   = s.route_id
left join dst on dst.stop_id   = o.stop_id
left join do_ on do_.outlet_id = o.outlet_id
left join da  on da.account_id = o.account_id
