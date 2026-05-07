-- Vault-style hub for the Policyholder business key.
{{ config(materialized='ephemeral') }}

with src as (
    select policyholder_id, tenure_years
    from {{ ref('stg_p_and_c_claims__policyholders') }}
    where policyholder_id is not null
)

select
    md5(policyholder_id)        as h_policyholder_hk,
    policyholder_id             as policyholder_bk,
    current_date                as load_date,
    'p_and_c_claims.policyholders' as record_source
from src
group by policyholder_id
