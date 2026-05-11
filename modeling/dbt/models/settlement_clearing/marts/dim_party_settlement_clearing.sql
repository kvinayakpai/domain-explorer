-- Party dimension for settlement (CSD / CCP / agent / custodian).
{{ config(materialized='table') }}

with hub as (select * from {{ ref('int_settlement_clearing__hub_party') }}),
     sat as (select * from {{ ref('int_settlement_clearing__sat_party_descriptive') }})

select
    h.h_party_hk     as party_key,
    h.party_bk       as party_id,
    s.legal_name,
    s.party_role,
    s.country_iso,
    s.bic,
    s.lei,
    s.status,
    h.load_date      as dim_loaded_at,
    true             as is_current
from hub h
left join sat s on s.h_party_hk = h.h_party_hk
