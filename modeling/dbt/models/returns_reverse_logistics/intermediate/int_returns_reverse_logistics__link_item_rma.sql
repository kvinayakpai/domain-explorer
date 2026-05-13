-- Vault link: return_item ↔ RMA ↔ reason_code ↔ disposition.
{{ config(materialized='ephemeral') }}

select
    md5(concat_ws('|', return_item_id, rma_id, coalesce(reason_code_id, ''), coalesce(disposition_id, '')))
                                                         as hk_link,
    md5(return_item_id)                                  as hk_return_item,
    md5(rma_id)                                          as hk_rma,
    md5(coalesce(reason_code_id, ''))                    as hk_reason_code,
    md5(coalesce(disposition_id, ''))                    as hk_disposition,
    disposition_decided_ts                               as load_dts,
    'returns_reverse_logistics.return_item'              as record_source
from {{ ref('stg_returns_reverse_logistics__return_items') }}
