-- Vault hub for the Scenario business key.
{{ config(materialized='ephemeral') }}

with src as (
    select distinct scenario_id
    from {{ ref('stg_sop_supply_chain_planning__scenarios') }}
    where scenario_id is not null
)

select
    md5(scenario_id)                         as h_scenario_hk,
    scenario_id                               as scenario_bk,
    current_date                              as load_date,
    'sop_supply_chain_planning.scenario'      as record_source
from src
