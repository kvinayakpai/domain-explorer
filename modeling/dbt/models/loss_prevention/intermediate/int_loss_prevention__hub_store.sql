-- Vault hub for the Store business key.
{{ config(materialized='ephemeral') }}

with src as (
    select store_id
    from {{ ref('stg_loss_prevention__store') }}
    where store_id is not null
)

select
    md5(store_id)                       as h_store_hk,
    store_id                            as store_bk,
    current_date                        as load_date,
    'loss_prevention.store'             as record_source
from src
group by store_id
