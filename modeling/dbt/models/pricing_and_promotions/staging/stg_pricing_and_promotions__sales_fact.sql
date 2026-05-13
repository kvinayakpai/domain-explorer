{{ config(materialized='view') }}

select
    cast(sales_id             as varchar)  as sales_id,
    cast(product_id           as varchar)  as product_id,
    cast(store_id             as varchar)  as store_id,
    cast(sale_date            as date)     as sale_date,
    cast(units_sold           as integer)  as units_sold,
    cast(gross_revenue_minor  as bigint)   as gross_revenue_minor,
    cast(discount_minor       as bigint)   as discount_minor,
    cast(net_revenue_minor    as bigint)   as net_revenue_minor,
    cast(cogs_minor           as bigint)   as cogs_minor,
    cast(on_promo             as boolean)  as on_promo,
    cast(promo_id             as varchar)  as promo_id,
    cast(realized_price_minor as bigint)   as realized_price_minor
from {{ source('pricing_and_promotions', 'sales_fact') }}
