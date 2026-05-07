-- Vault-style link between Claim and Policy.
{{ config(materialized='ephemeral') }}

with src as (
    select claim_id, policy_id
    from {{ ref('stg_p_and_c_claims__claims') }}
    where claim_id is not null and policy_id is not null
)

select
    md5(claim_id || '|' || policy_id) as l_claim_policy_hk,
    md5(claim_id)                     as h_claim_hk,
    md5(policy_id)                    as h_policy_hk,
    current_date                      as load_date,
    'p_and_c_claims.claims'           as record_source
from src
group by claim_id, policy_id
