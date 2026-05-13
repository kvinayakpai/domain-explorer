-- Vault satellite carrying time-phased supply-plan value attributes.
{{ config(materialized='ephemeral') }}

with src as (select * from {{ ref('stg_sop_supply_chain_planning__supply_plans') }})

select
    md5(item_id || '|' || coalesce(location_id,'') || '|' || coalesce(cycle_id,'')
        || '|' || coalesce(scenario_id,'') || '|' || cast(period_start as varchar))
                                                                         as l_supply_plan_hk,
    cast(published_at as timestamp)                                       as load_ts,
    md5(cast(planned_units as varchar) || '|' || cast(planned_value as varchar)
        || '|' || coalesce(supply_type,'') || '|' || coalesce(status,'')) as hashdiff,
    supply_type,
    source_location_id,
    planned_units,
    planned_value,
    lead_time_days,
    status,
    'sop_supply_chain_planning.supply_plan'                               as record_source
from src
