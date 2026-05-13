-- Vault satellite — consent state per customer × jurisdiction.
{{ config(materialized='ephemeral') }}

select
    md5(customer_id)                              as h_customer_hk,
    event_ts                                      as load_dts,
    jurisdiction,
    consent_basis,
    consent_string,
    purpose_codes,
    action,
    source_system,
    'customer_loyalty_cdp.consent_record'         as record_source
from {{ ref('stg_customer_loyalty_cdp__consent_record') }}
