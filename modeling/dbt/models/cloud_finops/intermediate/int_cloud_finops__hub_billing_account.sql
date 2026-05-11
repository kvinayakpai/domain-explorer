-- Vault-style hub for the Billing Account business key.
{{ config(materialized='ephemeral') }}

with src as (
    select billing_account_id from {{ ref('stg_cloud_finops__billing_account') }}
    where billing_account_id is not null
)

select
    md5(billing_account_id)              as h_billing_account_hk,
    billing_account_id                   as billing_account_bk,
    current_date                         as load_date,
    'cloud_finops.billing_account'       as record_source
from src
group by billing_account_id
