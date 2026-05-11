-- Staging: party master (counterparty / broker / custodian / CCP).
{{ config(materialized='view') }}

select
    cast(party_id    as varchar) as party_id,
    cast(lei         as varchar) as lei,
    cast(bic         as varchar) as bic,
    cast(legal_name  as varchar) as legal_name,
    cast(party_role  as varchar) as party_role,
    upper(country_iso)           as country_iso,
    cast(status      as varchar) as status
from {{ source('capital_markets', 'party') }}
