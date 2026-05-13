-- Vault hub for the Range Review business key.
{{ config(materialized='ephemeral') }}

with src as (
    select range_review_id
    from {{ ref('stg_category_management__range_reviews') }}
    where range_review_id is not null
)

select
    md5(range_review_id)                       as h_range_review_hk,
    range_review_id                            as range_review_bk,
    current_date                               as load_date,
    'category_management.range_review'         as record_source
from src
group by range_review_id
