-- Vault-style hub for the Meter business key.
{{ config(materialized='ephemeral') }}

with src as (
    select meter_id, installed_at
    from {{ ref('stg_smart_metering__meter') }}
    where meter_id is not null
)

select
    md5(meter_id)                            as h_meter_hk,
    meter_id                                 as meter_bk,
    coalesce(min(installed_at), current_date) as load_date,
    'smart_metering.meter'                   as record_source
from src
group by meter_id
