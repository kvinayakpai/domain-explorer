-- Vault hub for the Loyalty Account business key.
{{ config(materialized='ephemeral') }}

with src as (
    select loyalty_account_id, program_code
    from {{ ref('stg_customer_loyalty_cdp__loyalty_account') }}
    where loyalty_account_id is not null
)

select
    md5(loyalty_account_id)                            as h_loyalty_account_hk,
    loyalty_account_id                                 as loyalty_account_bk,
    max(program_code)                                  as program_code,
    current_date                                       as load_date,
    'customer_loyalty_cdp.loyalty_account'             as record_source
from src
group by loyalty_account_id
