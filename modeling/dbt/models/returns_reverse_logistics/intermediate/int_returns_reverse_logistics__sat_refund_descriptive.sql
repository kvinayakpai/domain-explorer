-- Vault satellite: refund descriptive + status (insert-only).
{{ config(materialized='ephemeral') }}

select
    md5(refund_id)                                       as hk_refund,
    issued_ts                                            as load_dts,
    refund_type,
    refund_amount_minor,
    currency,
    restocking_fee_collected_minor,
    payment_rail,
    status,
    'returns_reverse_logistics.refund'                   as record_source
from {{ ref('stg_returns_reverse_logistics__refunds') }}
