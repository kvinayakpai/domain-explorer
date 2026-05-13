-- Vault satellite: return_item condition + disposition decision (insert-only).
{{ config(materialized='ephemeral') }}

select
    md5(return_item_id)                                  as hk_return_item,
    disposition_decided_ts                               as load_dts,
    condition_grade,
    unit_cogs_minor,
    unit_retail_minor,
    quantity,
    'returns_reverse_logistics.return_item'              as record_source
from {{ ref('stg_returns_reverse_logistics__return_items') }}
