-- Vault link: supply plan row keyed by (item, location, cycle, scenario, period).
{{ config(materialized='ephemeral') }}

with src as (
    select item_id, location_id, cycle_id, scenario_id, period_start
    from {{ ref('stg_sop_supply_chain_planning__supply_plans') }}
    where item_id is not null
)

select
    md5(item_id || '|' || coalesce(location_id,'') || '|' || coalesce(cycle_id,'')
        || '|' || coalesce(scenario_id,'') || '|' || cast(period_start as varchar))
                                                          as l_supply_plan_hk,
    md5(item_id)                                           as h_item_hk,
    md5(location_id)                                       as h_location_hk,
    md5(cycle_id)                                          as h_cycle_hk,
    md5(coalesce(scenario_id, ''))                         as h_scenario_hk,
    period_start,
    current_date                                           as load_date,
    'sop_supply_chain_planning.supply_plan'                as record_source
from src
