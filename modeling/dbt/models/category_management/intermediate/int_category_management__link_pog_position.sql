-- Vault link for planogram-position SKU placement.
{{ config(materialized='ephemeral') }}

with src as (
    select planogram_id, sku_id, position_id, shelf_number, position_index, facings
    from {{ ref('stg_category_management__planogram_positions') }}
    where planogram_id is not null and sku_id is not null
)

select
    md5(planogram_id || '|' || sku_id || '|' || position_id)        as l_pog_position_hk,
    md5(planogram_id)                                                as h_planogram_hk,
    md5(sku_id)                                                      as h_sku_hk,
    position_id,
    shelf_number,
    position_index,
    facings,
    current_date                                                      as load_date,
    'category_management.planogram_position'                          as record_source
from src
