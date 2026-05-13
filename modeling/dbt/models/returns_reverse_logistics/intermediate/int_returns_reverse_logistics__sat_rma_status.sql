-- Vault satellite: RMA lifecycle state (insert-only).
{{ config(materialized='ephemeral') }}

select
    md5(rma_id)                                          as hk_rma,
    issued_ts                                            as load_dts,
    rma_status,
    return_method,
    return_platform,
    carrier,
    cross_border,
    'returns_reverse_logistics.return_authorization'     as record_source
from {{ ref('stg_returns_reverse_logistics__return_authorizations') }}
