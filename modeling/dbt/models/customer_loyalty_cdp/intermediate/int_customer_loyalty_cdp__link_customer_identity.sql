-- Vault link — identity-graph edge from customer to identifier.
{{ config(materialized='ephemeral') }}

select
    md5(coalesce(customer_id, '') || '|' || coalesce(identity_id, ''))   as l_customer_identity_hk,
    md5(customer_id)                                                      as h_customer_hk,
    identity_id                                                           as h_identity_id,
    match_method,
    match_confidence,
    first_observed_at                                                     as load_date,
    'customer_loyalty_cdp.identity_link'                                  as record_source
from {{ ref('stg_customer_loyalty_cdp__identity_link') }}
where customer_id is not null
