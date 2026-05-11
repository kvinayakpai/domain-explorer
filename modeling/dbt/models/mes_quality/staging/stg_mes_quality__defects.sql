-- Staging: defect catalog (children of failed inspections).
{{ config(materialized='view') }}

select
    cast(defect_id     as varchar)   as defect_id,
    cast(inspection_id as varchar)   as inspection_id,
    cast(code          as varchar)   as code,
    cast(severity      as varchar)   as severity,
    cast(category      as varchar)   as category,
    cast(logged_at     as timestamp) as logged_at
from {{ source('mes_quality', 'defects') }}
