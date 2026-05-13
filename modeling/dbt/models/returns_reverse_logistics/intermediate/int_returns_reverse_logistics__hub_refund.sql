-- Vault hub for the Refund business key.
{{ config(materialized='ephemeral') }}

with src as (
    select refund_id
    from {{ ref('stg_returns_reverse_logistics__refunds') }}
    where refund_id is not null
)

select
    md5(refund_id)                                  as hk_refund,
    refund_id                                       as refund_bk,
    current_date                                    as load_dts,
    'returns_reverse_logistics.refund'              as record_source
from src
group by refund_id
