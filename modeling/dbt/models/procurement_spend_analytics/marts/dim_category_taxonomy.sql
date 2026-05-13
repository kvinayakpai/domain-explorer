-- UNSPSC-anchored category dimension for the spend cube.
{{ config(materialized='table') }}

select
    row_number() over (order by category_code) as category_sk,
    category_code,
    segment_code,
    family_code,
    class_code,
    commodity_code,
    segment_name,
    family_name,
    class_name,
    commodity_name,
    direct_or_indirect,
    capex_or_opex,
    scope3_category
from {{ ref('stg_procurement_spend_analytics__category_taxonomy') }}
