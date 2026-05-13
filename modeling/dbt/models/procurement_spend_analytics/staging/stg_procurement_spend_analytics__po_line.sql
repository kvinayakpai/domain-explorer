{{ config(materialized='view') }}

select
    cast(po_line_id              as varchar)    as po_line_id,
    cast(po_id                   as varchar)    as po_id,
    cast(line_number             as smallint)   as line_number,
    cast(item_id                 as varchar)    as item_id,
    cast(item_description        as varchar)    as item_description,
    cast(category_code           as varchar)    as category_code,
    cast(quantity                as double)     as quantity,
    cast(uom                     as varchar)    as uom,
    cast(unit_price              as double)     as unit_price,
    cast(line_amount             as double)     as line_amount,
    cast(line_currency           as varchar)    as line_currency,
    cast(line_amount_base_usd    as double)     as line_amount_base_usd,
    cast(requested_delivery_date as date)        as requested_delivery_date,
    cast(tax_amount              as double)     as tax_amount,
    cast(discount_pct            as double)     as discount_pct,
    cast(scope3_kgco2e           as double)     as scope3_kgco2e
from {{ source('procurement_spend_analytics', 'po_line') }}
