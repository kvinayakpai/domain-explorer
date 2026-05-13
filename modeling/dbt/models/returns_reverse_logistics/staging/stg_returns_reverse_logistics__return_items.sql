{{ config(materialized='view') }}

select
    cast(return_item_id          as varchar)    as return_item_id,
    cast(rma_id                  as varchar)    as rma_id,
    cast(order_id                as varchar)    as order_id,
    cast(sku_id                  as varchar)    as sku_id,
    cast(gtin                    as varchar)    as gtin,
    cast(category                as varchar)    as category,
    cast(quantity                as integer)    as quantity,
    cast(unit_cogs_minor         as bigint)     as unit_cogs_minor,
    cast(unit_retail_minor       as bigint)     as unit_retail_minor,
    cast(reason_code_id          as varchar)    as reason_code_id,
    cast(condition_grade         as varchar)    as condition_grade,
    cast(disposition_id          as varchar)    as disposition_id,
    cast(disposition_decided_ts  as timestamp)  as disposition_decided_ts,
    cast(serial_number           as varchar)    as serial_number
from {{ source('returns_reverse_logistics', 'return_item') }}
