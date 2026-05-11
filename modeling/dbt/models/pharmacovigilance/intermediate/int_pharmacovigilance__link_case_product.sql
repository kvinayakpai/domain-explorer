-- Vault-style link between Case and Product (via case_drugs).
{{ config(materialized='ephemeral') }}

with src as (
    select case_id, product_id, role
    from {{ ref('stg_pharmacovigilance__case_drugs') }}
    where case_id is not null and product_id is not null
)

select
    md5(case_id || '|' || product_id || '|' || coalesce(role,'')) as l_case_product_hk,
    md5(case_id)                                                  as h_case_hk,
    md5(product_id)                                               as h_product_hk,
    role                                                          as drug_role,
    current_date                                                  as load_date,
    'pharmacovigilance.case_drugs'                                as record_source
from src
group by case_id, product_id, role
