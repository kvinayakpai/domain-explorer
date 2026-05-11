-- Vault-style hub for the Taxpayer business key.
{{ config(materialized='ephemeral') }}

with src as (
    select taxpayer_id, registered_at
    from {{ ref('stg_tax_administration__taxpayer') }}
    where taxpayer_id is not null
)

select
    md5(taxpayer_id)                          as h_taxpayer_hk,
    taxpayer_id                               as taxpayer_bk,
    coalesce(min(registered_at), current_date) as load_date,
    'tax_administration.taxpayer'             as record_source
from src
group by taxpayer_id
