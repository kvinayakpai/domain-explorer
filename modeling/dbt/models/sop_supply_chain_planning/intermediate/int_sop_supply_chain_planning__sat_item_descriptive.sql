-- Vault satellite carrying descriptive Item attributes.
{{ config(materialized='ephemeral') }}

with src as (select * from {{ ref('stg_sop_supply_chain_planning__items') }})

select
    md5(item_id)                                                           as h_item_hk,
    cast(created_at as timestamp)                                          as load_ts,
    md5(coalesce(item_family,'') || '|' || coalesce(item_class,'') || '|'
        || coalesce(xyz_class,'') || '|' || coalesce(lifecycle_stage,'')
        || '|' || coalesce(status,''))                                     as hashdiff,
    gtin,
    sku,
    item_family,
    item_class,
    xyz_class,
    lifecycle_stage,
    uom_base,
    planning_uom,
    unit_cost,
    unit_price,
    shelf_life_days,
    status,
    'sop_supply_chain_planning.item'                                       as record_source
from src
