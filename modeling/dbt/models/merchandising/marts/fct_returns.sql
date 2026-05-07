-- Grain: one row per return event.
{{ config(materialized='table') }}

with r as (select * from {{ ref('stg_merchandising__returns') }}),
     s as (select * from {{ ref('stg_merchandising__sales_lines') }}),
     hub_p as (select * from {{ ref('int_merchandising__hub_product') }})

select
    md5(r.return_id)                                as return_key,
    r.return_id,
    r.sale_line_id,
    r.sku,
    p.h_product_hk                                  as product_key,
    s.store_id,
    r.quantity                                      as returned_quantity,
    r.amount                                        as returned_amount,
    r.reason,
    r.returned_at,
    cast(strftime(r.returned_at, '%Y%m%d') as integer) as returned_date_key,
    case
        when s.ts is not null
            then date_diff('day', s.ts, r.returned_at)
    end                                             as days_since_sale
from r
left join s     on s.sale_line_id = r.sale_line_id
left join hub_p p on p.product_bk = r.sku
