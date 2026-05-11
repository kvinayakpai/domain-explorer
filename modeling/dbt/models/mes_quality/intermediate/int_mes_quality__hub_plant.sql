-- Vault hub for Plant.
{{ config(materialized='ephemeral') }}

with src as (
    select plant_id from {{ ref('stg_mes_quality__plants') }}
    where plant_id is not null
)

select
    md5(plant_id)              as h_plant_hk,
    plant_id                   as plant_bk,
    current_date               as load_date,
    'mes_quality.plants'       as record_source
from src
group by plant_id
