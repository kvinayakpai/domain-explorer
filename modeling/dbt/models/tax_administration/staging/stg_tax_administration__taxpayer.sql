{{ config(materialized='view') }}

select
    cast(taxpayer_id        as varchar) as taxpayer_id,
    cast(tin_hash           as varchar) as tin_hash,
    cast(tin_type           as varchar) as tin_type,
    cast(filing_entity_type as varchar) as filing_entity_type,
    cast(legal_name         as varchar) as legal_name,
    cast(address_line       as varchar) as address_line,
    cast(address_city       as varchar) as address_city,
    upper(address_state)                as address_state,
    upper(address_country)              as address_country,
    cast(filing_status      as varchar) as filing_status,
    cast(registered_at      as date)    as registered_at,
    cast(active             as boolean) as is_active
from {{ source('tax_administration', 'taxpayer') }}
