-- Vault link: liquidation_lot ↔ return_item with allocation rule output.
{{ config(materialized='ephemeral') }}

select
    md5(concat_ws('|', lot_id, return_item_id))         as hk_link,
    md5(lot_id)                                          as hk_lot,
    md5(return_item_id)                                  as hk_return_item,
    allocated_cogs_minor,
    allocated_proceeds_minor,
    current_date                                         as load_dts,
    'returns_reverse_logistics.liquidation_lot_item'     as record_source
from {{ ref('stg_returns_reverse_logistics__liquidation_lot_items') }}
