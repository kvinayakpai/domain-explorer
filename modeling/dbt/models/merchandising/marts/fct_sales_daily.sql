-- Grain: one row per (sale_date, store, channel). Daily revenue / units / margin
-- aggregates derived from the line-grain fct_sales.
{{ config(materialized='table') }}

with f as (select * from {{ ref('fct_sales') }}),
     hub_s as (select * from {{ ref('int_merchandising__hub_store') }})

select
    md5(cast(f.sale_date_key as varchar) || '|' || coalesce(f.store_id,'unknown') || '|' || coalesce(f.channel,'unknown'))
                                                                  as sales_daily_key,
    f.sale_date_key,
    cast(strptime(cast(f.sale_date_key as varchar), '%Y%m%d') as date) as sale_date,
    f.store_id,
    st.h_store_hk                                                  as store_key,
    f.channel,
    count(*)                                                       as line_count,
    count(distinct f.sale_line_id)                                 as distinct_sale_count,
    count(distinct f.sku)                                          as distinct_sku_count,
    sum(f.quantity)                                                as units_sold,
    sum(f.extended_amount)                                         as gross_revenue,
    sum(f.cogs)                                                    as total_cogs,
    sum(f.gross_profit)                                            as total_gross_profit,
    sum(f.returned_amount)                                         as returned_amount,
    sum(f.returned_units)                                          as returned_units,
    case
        when sum(f.extended_amount) > 0
            then sum(f.gross_profit) / sum(f.extended_amount)
    end                                                            as gross_margin_pct,
    case
        when sum(f.quantity) > 0
            then sum(f.returned_units)::double / sum(f.quantity)
    end                                                            as return_unit_rate
from f
left join hub_s st on st.store_bk = f.store_id
group by 2, 3, 4, 5, 6
