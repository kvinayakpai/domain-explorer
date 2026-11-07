{{ config(materialized='view') }}

-- SAP PM orders (PM01/PM02/PM03).
select
    cast(work_order_id          as varchar ) as work_order_id,
    cast(order_type             as varchar ) as order_type,
    cast(notification_id        as varchar ) as notification_id,
    cast(functional_location_id as varchar ) as functional_location_id,
    cast(equipment_id           as varchar ) as equipment_id,
    cast(basic_start            as date    ) as basic_start,
    cast(basic_finish           as date    ) as basic_finish,
    cast(short_text             as varchar ) as short_text
from {{ source('refinery_operations', 'work_order') }}
