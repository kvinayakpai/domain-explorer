{{ config(materialized='view') }}

select
    cast(order_id        as varchar)    as order_id,
    cast(customer_id     as varchar)    as customer_id,
    cast(channel         as varchar)    as channel,
    cast(order_ts        as timestamp)  as order_ts,
    cast(ship_node       as varchar)    as ship_node,
    cast(subtotal_minor  as bigint)     as subtotal_minor,
    cast(shipping_minor  as bigint)     as shipping_minor,
    cast(tax_minor       as bigint)     as tax_minor,
    cast(total_minor     as bigint)     as total_minor,
    upper(currency)                      as currency
from {{ source('returns_reverse_logistics', 'sales_order') }}
