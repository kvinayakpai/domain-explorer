-- Staging: production work orders.
{{ config(materialized='view') }}

select
    cast(work_order_id as varchar)   as work_order_id,
    cast(line_id       as varchar)   as line_id,
    cast(product_code  as varchar)   as product_code,
    cast(qty_planned   as integer)   as qty_planned,
    cast(qty_produced  as integer)   as qty_produced,
    cast(started_at    as timestamp) as started_at,
    cast(ended_at      as timestamp) as ended_at,
    cast(status        as varchar)   as status
from {{ source('mes_quality', 'work_orders') }}
