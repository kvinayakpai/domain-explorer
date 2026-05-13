-- Vault hub for the RMA business key.
{{ config(materialized='ephemeral') }}

with src as (
    select rma_id
    from {{ ref('stg_returns_reverse_logistics__return_authorizations') }}
    where rma_id is not null
)

select
    md5(rma_id)                                     as hk_rma,
    rma_id                                          as rma_bk,
    current_date                                    as load_dts,
    'returns_reverse_logistics.return_authorization' as record_source
from src
group by rma_id
