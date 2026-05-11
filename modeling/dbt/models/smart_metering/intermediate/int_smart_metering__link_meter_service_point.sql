-- Vault-style link between Meter and Service Point.
{{ config(materialized='ephemeral') }}

with src as (
    select meter_id, service_point_id
    from {{ ref('stg_smart_metering__meter') }}
    where meter_id is not null and service_point_id is not null
)

select
    md5(meter_id || '|' || service_point_id) as l_meter_service_point_hk,
    md5(meter_id)                            as h_meter_hk,
    md5(service_point_id)                    as h_service_point_hk,
    current_date                             as load_date,
    'smart_metering.meter'                   as record_source
from src
group by meter_id, service_point_id
