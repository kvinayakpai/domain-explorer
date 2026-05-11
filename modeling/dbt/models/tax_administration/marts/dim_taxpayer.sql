-- Taxpayer dimension fed from the Vault hub + staging attributes.
{{ config(materialized='table') }}

with hub as (select * from {{ ref('int_tax_administration__hub_taxpayer') }}),
     stg as (select * from {{ ref('stg_tax_administration__taxpayer') }})

select
    h.h_taxpayer_hk        as taxpayer_key,
    h.taxpayer_bk          as taxpayer_id,
    s.tin_hash,
    s.tin_type,
    s.filing_entity_type,
    s.legal_name,
    s.address_line,
    s.address_city,
    s.address_state,
    s.address_country,
    s.filing_status,
    s.registered_at,
    s.is_active,
    case when s.filing_entity_type = 'Individual' then true else false end as is_individual,
    h.load_date            as dim_loaded_at
from hub h
left join stg s on s.taxpayer_id = h.taxpayer_bk
