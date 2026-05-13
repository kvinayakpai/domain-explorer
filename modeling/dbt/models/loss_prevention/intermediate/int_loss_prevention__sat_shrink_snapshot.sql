-- Vault sat: store × department × period shrink snapshot (insert-only).
{{ config(materialized='ephemeral') }}

select
    md5(store_id)                           as h_store_hk,
    cast(period_start as timestamp)         as load_dts,
    department,
    period_start,
    period_end,
    opening_inventory_minor,
    receipts_minor,
    cogs_minor,
    closing_inventory_minor,
    known_shrink_minor,
    unknown_shrink_minor,
    total_shrink_minor,
    shrink_pct,
    'loss_prevention.shrink_snapshot'       as record_source
from {{ ref('stg_loss_prevention__shrink_snapshot') }}
