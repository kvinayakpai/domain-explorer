-- Vault hub for the Category business key.
{{ config(materialized='ephemeral') }}

with src as (
    select category_id
    from {{ ref('stg_category_management__categories') }}
    where category_id is not null
)

select
    md5(category_id)                    as h_category_hk,
    category_id                         as category_bk,
    current_date                        as load_date,
    'category_management.category'      as record_source
from src
group by category_id
