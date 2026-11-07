{{ config(materialized='view') }}

-- Component lots at the pump maker.
select
    cast(lot_id                as varchar ) as lot_id,
    cast(material              as varchar ) as material,
    cast(supplier_id           as varchar ) as supplier_id,
    cast(received_on           as date    ) as received_on,
    cast(quantity              as integer ) as quantity,
    cast(engineering_change_id as varchar ) as engineering_change_id,
    cast(purchase_order        as varchar ) as purchase_order
from {{ source('refinery_operations', 'material_lot') }}
