{{ config(materialized='view') }}

select
    cast(item_id           as varchar)    as item_id,
    cast(gtin              as varchar)    as gtin,
    cast(department        as varchar)    as department,
    cast(category          as varchar)    as category,
    cast(unit_cost_minor   as bigint)     as unit_cost_minor,
    cast(unit_retail_minor as bigint)     as unit_retail_minor,
    cast(craved_score      as double)     as craved_score,
    cast(eas_protected     as boolean)    as eas_protected,
    cast(rfid_tagged       as boolean)    as rfid_tagged
from {{ source('loss_prevention', 'item') }}
