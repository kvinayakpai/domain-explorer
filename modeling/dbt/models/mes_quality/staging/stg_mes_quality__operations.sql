-- Staging: per-step operations under a work order.
{{ config(materialized='view') }}

select
    cast(op_id            as varchar) as op_id,
    cast(work_order_id    as varchar) as work_order_id,
    cast(step             as integer) as step,
    cast(name             as varchar) as op_name,
    cast(duration_seconds as double)  as duration_seconds,
    cast(operator_id      as varchar) as operator_id
from {{ source('mes_quality', 'operations') }}
