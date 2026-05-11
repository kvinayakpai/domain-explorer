-- Vault-style hub for the Service Point business key.
{{ config(materialized='ephemeral') }}

with src as (
    select service_point_id, active_since
    from {{ ref('stg_smart_metering__service_point') }}
    where service_point_id is not null
)

select
    md5(service_point_id)                     as h_service_point_hk,
    service_point_id                          as service_point_bk,
    coalesce(min(active_since), current_date) as load_date,
    'smart_metering.service_point'            as record_source
from src
group by service_point_id
