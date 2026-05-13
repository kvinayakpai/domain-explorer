{{ config(materialized='view') }}

select
    cast(emissions_factor_id      as varchar)    as emissions_factor_id,
    cast(source                   as varchar)    as source,
    cast(vintage_year             as smallint)   as vintage_year,
    cast(category_code            as varchar)    as category_code,
    cast(country_iso2             as varchar)    as country_iso2,
    cast(factor_kgco2e_per_usd    as double)     as factor_kgco2e_per_usd,
    cast(factor_kgco2e_per_unit   as double)     as factor_kgco2e_per_unit,
    cast(unit                     as varchar)    as unit,
    cast(ghg_scope3_category      as smallint)   as ghg_scope3_category,
    cast(uncertainty_pct          as double)     as uncertainty_pct,
    cast(last_updated             as timestamp)  as last_updated
from {{ source('procurement_spend_analytics', 'emissions_factor') }}
