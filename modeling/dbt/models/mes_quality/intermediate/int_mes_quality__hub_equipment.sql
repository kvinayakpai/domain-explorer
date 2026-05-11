-- Vault hub for Equipment.
{{ config(materialized='ephemeral') }}

with src as (
    select equipment_id from {{ ref('stg_mes_quality__equipment') }}
    where equipment_id is not null
)

select
    md5(equipment_id)         as h_equipment_hk,
    equipment_id              as equipment_bk,
    current_date              as load_date,
    'mes_quality.equipment'   as record_source
from src
group by equipment_id
