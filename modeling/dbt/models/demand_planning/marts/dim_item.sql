-- Item dimension.
{{ config(materialized='table') }}

with hub as (select * from {{ ref('int_demand_planning__hub_item') }}),
     stg as (select * from {{ ref('stg_demand_planning__items') }})

select
    h.h_item_hk            as item_key,
    h.item_bk              as item_id,
    s.item_name,
    s.category,
    s.abc_class,
    s.lead_time_days,
    s.unit_cost,
    s.shelf_life_days,
    case
        when s.shelf_life_days is null then 'unknown'
        when s.shelf_life_days < 60    then 'short'
        when s.shelf_life_days < 365   then 'medium'
        else 'long'
    end                    as shelf_life_band,
    h.load_date            as dim_loaded_at
from hub h
left join stg s on s.item_id = h.item_bk
