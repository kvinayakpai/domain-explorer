{{ config(materialized='view') }}

-- Engineering changes; expedited ones may waive qualification.
select
    cast(engineering_change_id as varchar ) as engineering_change_id,
    cast(title                 as varchar ) as title,
    cast(part                  as varchar ) as part,
    cast(approval_route        as varchar ) as approval_route,
    cast(qualification_waived  as boolean ) as qualification_waived,
    cast(approved_on           as date    ) as approved_on,
    cast(status                as varchar ) as status,
    cast(supplier_from         as date    ) as supplier_from,
    cast(supplier_to           as date    ) as supplier_to
from {{ source('refinery_operations', 'engineering_change') }}
