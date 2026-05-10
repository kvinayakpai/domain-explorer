{{ config(materialized='table') }}

select
    row_number() over (order by principal_id) as principal_sk,
    principal_id,
    country_iso2,
    kyc_level,
    stepup_capable,
    status,
    created_at as valid_from,
    cast(null as timestamp) as valid_to,
    true as is_current
from {{ ref('stg_agentic_commerce__principals') }}
