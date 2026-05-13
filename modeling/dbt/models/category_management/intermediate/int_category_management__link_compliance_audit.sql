-- Vault link binding a planogram-compliance audit observation to its store + planogram.
{{ config(materialized='ephemeral') }}

with src as (
    select audit_id, store_id, planogram_id, audit_date
    from {{ ref('stg_category_management__compliance_audits') }}
    where store_id is not null and planogram_id is not null
)

select
    md5(audit_id)                                               as l_compliance_audit_hk,
    md5(store_id)                                               as h_store_hk,
    md5(planogram_id)                                           as h_planogram_hk,
    audit_id,
    audit_date,
    current_date                                                 as load_date,
    'category_management.planogram_compliance_audit'             as record_source
from src
