-- Vault-style satellite carrying descriptive Meter attributes.
{{ config(materialized='ephemeral') }}

with src as (
    select * from {{ ref('stg_smart_metering__meter') }}
)

select
    md5(meter_id)                                       as h_meter_hk,
    cast(installed_at as timestamp)                     as load_ts,
    md5(coalesce(manufacturer,'') || '|' || coalesce(model,'') || '|'
        || coalesce(firmware_version,'') || '|' || coalesce(status,''))
                                                        as hashdiff,
    serial_number,
    manufacturer,
    model,
    firmware_version,
    form_factor,
    communication_protocol,
    ct_ratio,
    status,
    'smart_metering.meter'                              as record_source
from src
