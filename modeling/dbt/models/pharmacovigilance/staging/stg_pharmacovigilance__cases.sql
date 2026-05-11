-- Staging: ICSR case headers.
{{ config(materialized='view') }}

select
    cast(case_id            as varchar)   as case_id,
    cast(patient_id         as varchar)   as patient_id,
    cast(reporter_id        as varchar)   as reporter_id,
    cast(primary_product_id as varchar)   as primary_product_id,
    cast(received_at        as timestamp) as received_at,
    cast(seriousness        as varchar)   as seriousness,
    cast(expectedness       as varchar)   as expectedness,
    cast(case_status        as varchar)   as case_status,
    upper(country)                        as country,
    case
        when cast(seriousness as varchar) in ('serious','life_threatening','death') then true
        else false
    end as is_serious
from {{ source('pharmacovigilance', 'cases') }}
