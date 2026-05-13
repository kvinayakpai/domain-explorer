{{ config(materialized='view') }}

select
    cast(category_code        as varchar)    as category_code,
    cast(segment_code         as varchar)    as segment_code,
    cast(family_code          as varchar)    as family_code,
    cast(class_code           as varchar)    as class_code,
    cast(commodity_code       as varchar)    as commodity_code,
    cast(segment_name         as varchar)    as segment_name,
    cast(family_name          as varchar)    as family_name,
    cast(class_name           as varchar)    as class_name,
    cast(commodity_name       as varchar)    as commodity_name,
    cast(direct_or_indirect   as varchar)    as direct_or_indirect,
    cast(capex_or_opex        as varchar)    as capex_or_opex,
    cast(internal_category_id as varchar)    as internal_category_id,
    cast(scope3_category      as smallint)   as scope3_category
from {{ source('procurement_spend_analytics', 'category_taxonomy') }}
