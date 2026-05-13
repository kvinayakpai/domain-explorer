{{ config(materialized='view') }}

select
    cast(reason_code_id       as varchar)  as reason_code_id,
    cast(reason_code          as varchar)  as reason_code,
    cast(reason_category      as varchar)  as reason_category,
    cast(customer_facing_text as varchar)  as customer_facing_text,
    cast(defect_attribution   as varchar)  as defect_attribution,
    cast(actionable           as boolean)  as actionable,
    cast(severity             as varchar)  as severity
from {{ source('returns_reverse_logistics', 'reason_code') }}
