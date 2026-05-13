-- Vault link: capacity row keyed by (location, resource, period).
{{ config(materialized='ephemeral') }}

with src as (
    select location_id, resource_id, period_start
    from {{ ref('stg_sop_supply_chain_planning__capacity') }}
    where location_id is not null
)

select
    md5(coalesce(location_id,'') || '|' || coalesce(resource_id,'')
        || '|' || cast(period_start as varchar))           as l_capacity_hk,
    md5(location_id)                                       as h_location_hk,
    resource_id,
    period_start,
    current_date                                           as load_date,
    'sop_supply_chain_planning.capacity'                   as record_source
from src
