-- Vault link: BOM parent ↔ component, optionally per location.
{{ config(materialized='ephemeral') }}

with src as (
    select parent_item_id, component_item_id, location_id, bom_version
    from {{ ref('stg_sop_supply_chain_planning__bom') }}
    where parent_item_id is not null
)

select
    md5(parent_item_id || '|' || coalesce(component_item_id,'')
        || '|' || coalesce(location_id,'') || '|' || coalesce(bom_version,''))
                                                          as l_bom_hk,
    md5(parent_item_id)                                    as h_parent_item_hk,
    md5(coalesce(component_item_id, ''))                   as h_component_item_hk,
    md5(coalesce(location_id, ''))                         as h_location_hk,
    bom_version,
    current_date                                           as load_date,
    'sop_supply_chain_planning.bom'                        as record_source
from src
