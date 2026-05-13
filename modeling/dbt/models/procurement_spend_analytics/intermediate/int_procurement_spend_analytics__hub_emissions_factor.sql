-- Vault hub for the Emissions Factor business key.
{{ config(materialized='ephemeral') }}

select
    md5(emissions_factor_id)                                   as h_emissions_factor_hk,
    emissions_factor_id                                        as emissions_factor_bk,
    current_date                                               as load_date,
    'procurement_spend_analytics.emissions_factor'             as record_source
from {{ ref('stg_procurement_spend_analytics__emissions_factor') }}
where emissions_factor_id is not null
group by emissions_factor_id
