-- Staging: scrap events.
{{ config(materialized='view') }}

select
    cast(scrap_id      as varchar)   as scrap_id,
    cast(work_order_id as varchar)   as work_order_id,
    cast(qty           as integer)   as qty,
    cast(reason_code   as varchar)   as reason_code,
    cast(ts            as timestamp) as ts,
    cast(cost          as double)    as cost
from {{ source('mes_quality', 'scrap_events') }}
