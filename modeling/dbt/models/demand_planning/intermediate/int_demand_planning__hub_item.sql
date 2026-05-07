-- Vault-style hub for Item.
{{ config(materialized='ephemeral') }}

with src as (
    select item_id from {{ ref('stg_demand_planning__items') }}
    where item_id is not null
    union
    select distinct item_id from {{ ref('stg_demand_planning__historical_demand') }}
    where item_id is not null
    union
    select distinct item_id from {{ ref('stg_demand_planning__forecasts') }}
    where item_id is not null
)

select
    md5(item_id)              as h_item_hk,
    item_id                   as item_bk,
    current_date              as load_date,
    'demand_planning.items'   as record_source
from src
group by item_id
