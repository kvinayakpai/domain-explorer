-- Item dimension for loss_prevention. _lp suffix avoids collision with
-- merchandising / pricing_and_promotions dim_product tables.
{{ config(materialized='table') }}

select
    row_number() over (order by item_id)         as product_sk,
    item_id,
    gtin,
    department,
    category,
    unit_cost_minor,
    unit_retail_minor,
    craved_score,
    eas_protected,
    rfid_tagged
from {{ ref('stg_loss_prevention__item') }}
