-- Vault-style hub for Store.
{{ config(materialized='ephemeral') }}

with src as (
    select store_id from {{ ref('stg_merchandising__stores') }}
    where store_id is not null
    union
    select distinct store_id from {{ ref('stg_merchandising__sales_lines') }}
    where store_id is not null
)

select
    md5(store_id)             as h_store_hk,
    store_id                  as store_bk,
    current_date              as load_date,
    'merchandising.stores'    as record_source
from src
group by store_id
