{{ config(materialized='view') }}

-- Physical pumps by maker's serial.
select
    cast(equipment_id   as varchar ) as equipment_id,
    cast(equipment_kind as varchar ) as equipment_kind,
    cast(model          as varchar ) as model,
    cast(maker_id       as varchar ) as maker_id,
    cast(customer_id    as varchar ) as customer_id,
    cast(built_on       as date    ) as built_on,
    cast(shipped_on     as date    ) as shipped_on
from {{ source('refinery_operations', 'equipment') }}
