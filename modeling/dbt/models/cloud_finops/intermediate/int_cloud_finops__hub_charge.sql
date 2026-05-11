-- Vault-style hub for the Charge Record business key.
{{ config(materialized='ephemeral') }}

with src as (
    select charge_record_id, charge_period_start
    from {{ ref('stg_cloud_finops__charge_record') }}
    where charge_record_id is not null
)

select
    md5(charge_record_id)                as h_charge_hk,
    charge_record_id                     as charge_bk,
    min(charge_period_start)             as load_ts,
    'cloud_finops.charge_record'         as record_source
from src
group by charge_record_id
