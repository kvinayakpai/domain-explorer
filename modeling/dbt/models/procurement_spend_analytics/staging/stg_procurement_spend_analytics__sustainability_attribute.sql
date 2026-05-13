{{ config(materialized='view') }}

select
    cast(sustainability_attr_id  as varchar)    as sustainability_attr_id,
    cast(supplier_id             as varchar)    as supplier_id,
    cast(source                  as varchar)    as source,
    cast(reporting_year          as smallint)   as reporting_year,
    cast(scope1_tco2e            as double)     as scope1_tco2e,
    cast(scope2_market_tco2e     as double)     as scope2_market_tco2e,
    cast(scope2_location_tco2e   as double)     as scope2_location_tco2e,
    cast(scope3_tco2e            as double)     as scope3_tco2e,
    cast(renewable_energy_pct    as double)     as renewable_energy_pct,
    cast(water_withdrawal_m3     as double)     as water_withdrawal_m3,
    cast(waste_tonnes            as double)     as waste_tonnes,
    cast(sbti_target_year        as smallint)   as sbti_target_year,
    cast(net_zero_target_year    as smallint)   as net_zero_target_year,
    cast(observed_at             as timestamp)  as observed_at
from {{ source('procurement_spend_analytics', 'sustainability_attribute') }}
