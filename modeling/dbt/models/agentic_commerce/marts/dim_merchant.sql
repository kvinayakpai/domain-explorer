{{ config(materialized='table') }}

select
    row_number() over (order by merchant_id) as merchant_sk,
    merchant_id,
    legal_name,
    domain,
    country_iso2,
    mcc,
    agent_aware_tier,
    has_mcp_endpoint,
    has_ap2_endpoint
from {{ ref('stg_agentic_commerce__merchants') }}
