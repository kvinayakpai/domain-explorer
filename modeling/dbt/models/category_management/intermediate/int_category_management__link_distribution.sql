-- Vault link for store × SKU × week distribution observations.
{{ config(materialized='ephemeral') }}

with src as (
    select distribution_record_id, store_id, sku_id, week_start_date
    from {{ ref('stg_category_management__distribution_records') }}
    where store_id is not null and sku_id is not null
)

select
    md5(distribution_record_id)                                  as l_distribution_hk,
    md5(store_id)                                                as h_store_hk,
    md5(sku_id)                                                  as h_sku_hk,
    distribution_record_id,
    week_start_date,
    current_date                                                  as load_date,
    'category_management.distribution_record'                     as record_source
from src
