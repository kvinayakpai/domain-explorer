-- Vault satellite carrying capacity utilization state per period.
{{ config(materialized='ephemeral') }}

with src as (select * from {{ ref('stg_sop_supply_chain_planning__capacity') }})

select
    md5(coalesce(location_id,'') || '|' || coalesce(resource_id,'')
        || '|' || cast(period_start as varchar))                          as l_capacity_hk,
    cast(period_start as timestamp)                                       as load_ts,
    md5(cast(available_hours as varchar) || '|'
        || cast(planned_load_hours as varchar)
        || '|' || coalesce(status,''))                                    as hashdiff,
    resource_type,
    available_hours,
    planned_load_hours,
    utilization_pct,
    changeover_hours,
    status,
    'sop_supply_chain_planning.capacity'                                  as record_source
from src
