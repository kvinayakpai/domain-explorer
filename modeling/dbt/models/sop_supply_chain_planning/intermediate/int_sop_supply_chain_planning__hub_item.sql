-- Vault hub for the Item business key (GS1 GTIN where assigned).
{{ config(materialized='ephemeral') }}

with src as (
    select item_id, gtin
    from {{ ref('stg_sop_supply_chain_planning__items') }}
    where item_id is not null
)

select
    md5(item_id)                          as h_item_hk,
    item_id                                as item_bk,
    max(gtin)                              as gtin,
    current_date                           as load_date,
    'sop_supply_chain_planning.item'       as record_source
from src
group by item_id
