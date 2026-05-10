{{ config(materialized='view') }}

select
    cast(principal_id        as varchar)    as principal_id,
    cast(external_user_ref   as varchar)    as external_user_ref,
    upper(country_iso2)                     as country_iso2,
    cast(kyc_level           as varchar)    as kyc_level,
    cast(created_at          as timestamp)  as created_at,
    cast(stepup_capable      as boolean)    as stepup_capable,
    cast(status              as varchar)    as status
from {{ source('agentic_commerce', 'principal') }}
