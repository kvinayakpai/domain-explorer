-- Staging: insured properties.
{{ config(materialized='view') }}

select
    cast(property_id          as varchar) as property_id,
    cast(policy_id            as varchar) as policy_id,
    cast(property_type        as varchar) as property_type,
    cast(year_built           as integer) as year_built,
    cast(square_feet          as integer) as square_feet,
    cast(construction         as varchar) as construction,
    cast(fire_protection_class as integer) as fire_protection_class,
    cast(zip                  as varchar) as zip
from {{ source('p_and_c_claims', 'properties') }}
