{{ config(materialized='view') }}

select
    cast(sku_id          as varchar)  as sku_id,
    cast(attribute_name  as varchar)  as attribute_name,
    cast(attribute_value as varchar)  as attribute_value,
    cast(attribute_level as smallint) as attribute_level,
    cast(source_system   as varchar)  as source_system
from {{ source('category_management', 'sku_attribute') }}
