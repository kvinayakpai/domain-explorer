-- Staging: quality inspections.
{{ config(materialized='view') }}

select
    cast(inspection_id as varchar)   as inspection_id,
    cast(work_order_id as varchar)   as work_order_id,
    cast(ts            as timestamp) as ts,
    cast(result        as varchar)   as result,
    cast(inspector     as varchar)   as inspector,
    cast(method        as varchar)   as method
from {{ source('mes_quality', 'inspections') }}
