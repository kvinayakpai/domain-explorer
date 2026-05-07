-- Grain: one row per POS sale line. Surfaces SKU + store keys and any
-- markdown active on the sale day plus return signals.
{{ config(materialized='table') }}

with s as (select * from {{ ref('stg_merchandising__sales_lines') }}),
     hub_p as (select * from {{ ref('int_merchandising__hub_product') }}),
     hub_s as (select * from {{ ref('int_merchandising__hub_store') }}),
     prod  as (select * from {{ ref('stg_merchandising__products') }}),
     ret as (
         select
             sale_line_id,
             count(*)               as return_event_count,
             sum(quantity)          as returned_units,
             sum(amount)            as returned_amount
         from {{ ref('stg_merchandising__returns') }}
         group by sale_line_id
     ),
     md_active as (
         select sku, max(depth_pct) as max_md_depth_pct
         from {{ ref('stg_merchandising__markdowns') }}
         group by sku
     )

select
    md5(s.sale_line_id)                              as sale_key,
    s.sale_line_id,
    s.sku,
    p.h_product_hk                                   as product_key,
    s.store_id,
    st.h_store_hk                                    as store_key,
    s.quantity,
    s.unit_price,
    s.extended_amount,
    s.channel,
    s.ts                                             as sale_ts,
    cast(strftime(s.ts, '%Y%m%d') as integer)        as sale_date_key,
    coalesce(prod.cost, 0.0) * s.quantity            as cogs,
    s.extended_amount - coalesce(prod.cost, 0.0) * s.quantity  as gross_profit,
    md_active.max_md_depth_pct                       as max_md_depth_pct,
    coalesce(ret.return_event_count, 0)              as return_event_count,
    coalesce(ret.returned_units, 0)                  as returned_units,
    coalesce(ret.returned_amount, 0.0)               as returned_amount,
    case
        when s.quantity > 0
            then coalesce(ret.returned_units, 0)::double / s.quantity
    end                                              as return_unit_rate
from s
left join hub_p p   on p.product_bk     = s.sku
left join hub_s st  on st.store_bk      = s.store_id
left join prod      on prod.sku         = s.sku
left join ret       on ret.sale_line_id = s.sale_line_id
left join md_active on md_active.sku    = s.sku
