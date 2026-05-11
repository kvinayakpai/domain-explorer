-- Vault-style hub for the Case business key.
{{ config(materialized='ephemeral') }}

with src as (
    select case_id, received_at
    from {{ ref('stg_pharmacovigilance__cases') }}
    where case_id is not null
)

select
    md5(case_id)                                         as h_case_hk,
    case_id                                              as case_bk,
    coalesce(min(cast(received_at as date)), current_date) as load_date,
    'pharmacovigilance.cases'                            as record_source
from src
group by case_id
