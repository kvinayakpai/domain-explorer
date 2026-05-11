-- Staging: drugs implicated in a case by role.
{{ config(materialized='view') }}

select
    cast(case_drug_id as varchar) as case_drug_id,
    cast(case_id      as varchar) as case_id,
    cast(product_id   as varchar) as product_id,
    cast(role         as varchar) as role,
    cast(dose_text    as varchar) as dose_text,
    cast(indication   as varchar) as indication,
    case when cast(role as varchar) = 'suspect' then true else false end as is_suspect
from {{ source('pharmacovigilance', 'case_drugs') }}
