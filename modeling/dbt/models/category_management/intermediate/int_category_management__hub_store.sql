-- Vault hub for the Store business key.
{{ config(materialized='ephemeral') }}

with src as (
    select store_id
    from {{ ref('stg_category_management__stores') }}
    where store_id is not null
)

select
    md5(store_id)                  as h_store_hk,
    store_id                       as store_bk,
    current_date                   as load_date,
    'category_management.store'    as record_source
from src
group by store_id
