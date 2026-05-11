-- Vault-style link between Charge Record and Billing Account.
{{ config(materialized='ephemeral') }}

with src as (
    select charge_record_id, billing_account_id
    from {{ ref('stg_cloud_finops__charge_record') }}
    where charge_record_id is not null and billing_account_id is not null
)

select
    md5(charge_record_id || '|' || billing_account_id) as l_charge_account_hk,
    md5(charge_record_id)                              as h_charge_hk,
    md5(billing_account_id)                            as h_billing_account_hk,
    current_date                                       as load_date,
    'cloud_finops.charge_record'                       as record_source
from src
group by charge_record_id, billing_account_id
