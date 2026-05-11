-- Vault-style satellite carrying descriptive Case attributes.
{{ config(materialized='ephemeral') }}

with src as (
    select * from {{ ref('stg_pharmacovigilance__cases') }}
)

select
    md5(case_id)                                          as h_case_hk,
    received_at                                           as load_ts,
    md5(coalesce(seriousness,'') || '|' || coalesce(expectedness,'')
        || '|' || coalesce(case_status,'') || '|' || coalesce(country,''))
                                                          as hashdiff,
    seriousness,
    expectedness,
    case_status,
    country,
    is_serious,
    received_at,
    'pharmacovigilance.cases'                             as record_source
from src
