-- Staging: equipment master.
{{ config(materialized='view') }}

select
    cast(equipment_id  as varchar) as equipment_id,
    cast(line_id       as varchar) as line_id,
    cast(kind          as varchar) as kind,
    cast(vendor        as varchar) as vendor,
    cast(install_year  as integer) as install_year,
    cast(criticality   as varchar) as criticality
from {{ source('mes_quality', 'equipment') }}
