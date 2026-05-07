-- Vault-style hub for Policy.
{{ config(materialized='ephemeral') }}

with src as (
    select policy_id, effective_date
    from {{ ref('stg_p_and_c_claims__policies') }}
    where policy_id is not null
)

select
    md5(policy_id)              as h_policy_hk,
    policy_id                   as policy_bk,
    coalesce(min(effective_date), current_date) as load_date,
    'p_and_c_claims.policies'   as record_source
from src
group by policy_id
