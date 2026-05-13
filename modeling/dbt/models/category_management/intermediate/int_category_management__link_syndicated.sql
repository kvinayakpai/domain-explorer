-- Vault link for syndicated POS / panel measurement.
{{ config(materialized='ephemeral') }}

with src as (
    select measurement_id, sku_id, store_id, category_id, week_start_date, source
    from {{ ref('stg_category_management__syndicated_measurements') }}
    where measurement_id is not null
)

select
    md5(measurement_id)                                            as l_syndicated_hk,
    md5(coalesce(sku_id,''))                                       as h_sku_hk,
    md5(coalesce(store_id,''))                                     as h_store_hk,
    md5(coalesce(category_id,''))                                  as h_category_hk,
    measurement_id,
    week_start_date,
    source,
    current_date                                                    as load_date,
    'category_management.syndicated_measurement'                    as record_source
from src
