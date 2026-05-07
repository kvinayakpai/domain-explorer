-- Vault-style link between Policy and Policyholder.
{{ config(materialized='ephemeral') }}

with src as (
    select policy_id, policyholder_id
    from {{ ref('stg_p_and_c_claims__policies') }}
    where policy_id is not null and policyholder_id is not null
)

select
    md5(policy_id || '|' || policyholder_id) as l_policy_policyholder_hk,
    md5(policy_id)                           as h_policy_hk,
    md5(policyholder_id)                     as h_policyholder_hk,
    current_date                             as load_date,
    'p_and_c_claims.policies'                as record_source
from src
group by policy_id, policyholder_id
