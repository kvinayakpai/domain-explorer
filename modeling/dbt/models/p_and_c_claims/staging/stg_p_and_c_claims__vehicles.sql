-- Staging: vehicles attached to auto policies.
{{ config(materialized='view') }}

select
    cast(vehicle_id     as varchar) as vehicle_id,
    cast(policy_id      as varchar) as policy_id,
    cast(make           as varchar) as make,
    cast(model_year     as integer) as model_year,
    cast(vin            as varchar) as vin,
    cast(annual_mileage as integer) as annual_mileage,
    cast(primary_use    as varchar) as primary_use
from {{ source('p_and_c_claims', 'vehicles') }}
