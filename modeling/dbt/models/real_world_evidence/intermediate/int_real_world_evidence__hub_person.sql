-- Vault-style hub for the OMOP Person business key.
{{ config(materialized='ephemeral') }}

with src as (
    select person_id
    from {{ ref('stg_real_world_evidence__person') }}
    where person_id is not null
)

select
    md5(cast(person_id as varchar))    as h_person_hk,
    person_id                          as person_bk,
    current_date                       as load_date,
    'real_world_evidence.person'       as record_source
from src
group by person_id
