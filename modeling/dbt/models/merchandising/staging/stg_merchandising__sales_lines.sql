-- Staging: POS sales line items.
{{ config(materialized='view') }}

select
    cast(sale_line_id     as varchar)   as sale_line_id,
    cast(sku              as varchar)   as sku,
    cast(store_id         as varchar)   as store_id,
    cast(quantity         as integer)   as quantity,
    cast(unit_price       as double)    as unit_price,
    cast(extended_amount  as double)    as extended_amount,
    cast(ts               as timestamp) as ts,
    cast(channel          as varchar)   as channel
from {{ source('merchandising', 'sales_lines') }}
