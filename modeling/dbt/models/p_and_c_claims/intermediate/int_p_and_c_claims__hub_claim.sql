-- Vault-style hub for Claim.
{{ config(materialized='ephemeral') }}

with src as (
    select claim_id, fnol_ts
    from {{ ref('stg_p_and_c_claims__claims') }}
    where claim_id is not null
)

select
    md5(claim_id)                as h_claim_hk,
    claim_id                     as claim_bk,
    min(fnol_ts)                 as load_ts,
    'p_and_c_claims.claims'      as record_source
from src
group by claim_id
