{{ config(materialized='table') }}

select
    row_number() over (order by reason_code_id)  as reason_code_sk,
    reason_code_id,
    reason_code,
    reason_category,
    customer_facing_text,
    defect_attribution,
    actionable,
    severity
from {{ ref('stg_returns_reverse_logistics__reason_codes') }}
