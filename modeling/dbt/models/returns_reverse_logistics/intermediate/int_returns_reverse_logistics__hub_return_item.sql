-- Vault hub for the Return Item business key.
{{ config(materialized='ephemeral') }}

with src as (
    select return_item_id
    from {{ ref('stg_returns_reverse_logistics__return_items') }}
    where return_item_id is not null
)

select
    md5(return_item_id)                             as hk_return_item,
    return_item_id                                  as return_item_bk,
    current_date                                    as load_dts,
    'returns_reverse_logistics.return_item'         as record_source
from src
group by return_item_id
