-- Vault satellite for Equipment descriptive attributes.
{{ config(materialized='ephemeral') }}

with src as (select * from {{ ref('stg_mes_quality__equipment') }})

select
    md5(equipment_id)                                                        as h_equipment_hk,
    current_date                                                             as load_date,
    md5(coalesce(kind,'') || '|' || coalesce(vendor,'')
        || '|' || coalesce(criticality,'')
        || '|' || cast(coalesce(install_year, 0) as varchar))                 as hashdiff,
    kind,
    vendor,
    install_year,
    criticality,
    'mes_quality.equipment'                                                   as record_source
from src
