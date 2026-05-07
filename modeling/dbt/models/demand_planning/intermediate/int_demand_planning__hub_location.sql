-- Vault-style hub for Location.
{{ config(materialized='ephemeral') }}

with src as (
    select location_id from {{ ref('stg_demand_planning__locations') }}
    where location_id is not null
    union
    select distinct location_id from {{ ref('stg_demand_planning__historical_demand') }}
    where location_id is not null
)

select
    md5(location_id)             as h_location_hk,
    location_id                  as location_bk,
    current_date                 as load_date,
    'demand_planning.locations'  as record_source
from src
group by location_id
