-- Vault-style satellite carrying descriptive Claim attributes.
{{ config(materialized='ephemeral') }}

with src as (
    select * from {{ ref('stg_p_and_c_claims__claims') }}
)

select
    md5(claim_id)                                          as h_claim_hk,
    fnol_ts                                                as load_ts,
    md5(coalesce(peril,'') || '|' || coalesce(severity,'') || '|'
        || coalesce(claim_status,'') || '|' || cast(incurred_amount as varchar))
                                                           as hashdiff,
    peril,
    severity,
    claim_status,
    incurred_amount,
    fraud_score,
    loss_date,
    fnol_ts,
    report_lag_days,
    'p_and_c_claims.claims'                                as record_source
from src
