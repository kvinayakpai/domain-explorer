-- Vault-style hub for the Return business key.
{{ config(materialized='ephemeral') }}

with src as (
    select return_id, filed_at
    from {{ ref('stg_tax_administration__return') }}
    where return_id is not null
)

select
    md5(return_id)                       as h_return_hk,
    return_id                            as return_bk,
    min(filed_at)                        as load_ts,
    'tax_administration.return'          as record_source
from src
group by return_id
