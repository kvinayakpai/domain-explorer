-- Vault link — customer <-> loyalty account.
{{ config(materialized='ephemeral') }}

select
    md5(coalesce(customer_id, '') || '|' || coalesce(loyalty_account_id, ''))   as l_customer_loyalty_hk,
    md5(customer_id)                                                             as h_customer_hk,
    md5(loyalty_account_id)                                                      as h_loyalty_account_hk,
    enrolled_at                                                                  as load_date,
    'customer_loyalty_cdp.loyalty_account'                                       as record_source
from {{ ref('stg_customer_loyalty_cdp__loyalty_account') }}
where customer_id is not null and loyalty_account_id is not null
