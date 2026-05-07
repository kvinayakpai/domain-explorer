-- Staging: light typing on p_and_c_claims.policyholders.
{{ config(materialized='view') }}

select
    cast(policyholder_id as varchar) as policyholder_id,
    cast(full_name       as varchar) as full_name,
    cast(email           as varchar) as email,
    upper(country)                   as country_code,
    cast(credit_band     as varchar) as credit_band,
    cast(tenure_years    as integer) as tenure_years
from {{ source('p_and_c_claims', 'policyholders') }}
