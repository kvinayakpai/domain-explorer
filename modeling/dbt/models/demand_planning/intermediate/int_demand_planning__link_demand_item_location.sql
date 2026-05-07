-- Vault-style link between Demand fact, Item, and Location.
{{ config(materialized='ephemeral') }}

with src as (
    select demand_id, item_id, location_id
    from {{ ref('stg_demand_planning__historical_demand') }}
    where demand_id is not null and item_id is not null and location_id is not null
)

select
    md5(demand_id)                                  as h_demand_hk,
    md5(item_id)                                    as h_item_hk,
    md5(location_id)                                as h_location_hk,
    md5(demand_id || '|' || item_id || '|' || location_id) as l_demand_item_location_hk,
    current_date                                    as load_date,
    'demand_planning.historical_demand'             as record_source
from src
