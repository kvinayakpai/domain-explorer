-- Vault-style link between Return and Taxpayer.
{{ config(materialized='ephemeral') }}

with src as (
    select return_id, taxpayer_id
    from {{ ref('stg_tax_administration__return') }}
    where return_id is not null and taxpayer_id is not null
)

select
    md5(return_id || '|' || taxpayer_id)  as l_return_taxpayer_hk,
    md5(return_id)                        as h_return_hk,
    md5(taxpayer_id)                      as h_taxpayer_hk,
    current_date                          as load_date,
    'tax_administration.return'           as record_source
from src
group by return_id, taxpayer_id
