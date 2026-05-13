-- Vault satellite: liquidation lot proceeds (insert-only).
{{ config(materialized='ephemeral') }}

select
    md5(lot_id)                                          as hk_lot,
    sold_ts                                              as load_dts,
    marketplace,
    item_count,
    total_cogs_minor,
    proceeds_minor,
    currency,
    recovery_pct,
    'returns_reverse_logistics.liquidation_lot'          as record_source
from {{ ref('stg_returns_reverse_logistics__liquidation_lots') }}
