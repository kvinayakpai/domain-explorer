{{ config(materialized='view') }}

select
    cast(merchant_id       as varchar)    as merchant_id,
    cast(legal_name        as varchar)    as legal_name,
    cast(domain            as varchar)    as domain,
    upper(country_iso2)                   as country_iso2,
    cast(mcc               as varchar)    as mcc,
    cast(agent_aware_tier  as varchar)    as agent_aware_tier,
    cast(mcp_endpoint      as varchar)    as mcp_endpoint,
    cast(ap2_endpoint      as varchar)    as ap2_endpoint,
    cast(created_at        as timestamp)  as created_at,
    case when mcp_endpoint is not null then true else false end as has_mcp_endpoint,
    case when ap2_endpoint is not null then true else false end as has_ap2_endpoint
from {{ source('agentic_commerce', 'merchant') }}
