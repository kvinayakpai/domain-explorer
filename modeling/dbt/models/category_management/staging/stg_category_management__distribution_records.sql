{{ config(materialized='view') }}

select
    cast(distribution_record_id as varchar)   as distribution_record_id,
    cast(store_id               as varchar)   as store_id,
    cast(sku_id                 as varchar)   as sku_id,
    cast(week_start_date        as date)      as week_start_date,
    cast(is_listed              as boolean)   as is_listed,
    cast(is_on_shelf            as boolean)   as is_on_shelf,
    cast(acv_weight             as double)    as acv_weight,
    cast(mandated_flag          as boolean)   as mandated_flag,
    cast(compliant_flag         as boolean)   as compliant_flag,
    cast(source_doc             as varchar)   as source_doc,
    cast(ingested_at            as timestamp) as ingested_at
from {{ source('category_management', 'distribution_record') }}
