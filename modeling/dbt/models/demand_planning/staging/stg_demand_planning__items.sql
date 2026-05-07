-- Staging: item master.
{{ config(materialized='view') }}

select
    cast(item_id          as varchar) as item_id,
    cast(item_name        as varchar) as item_name,
    cast(category         as varchar) as category,
    cast(abc_class        as varchar) as abc_class,
    cast(lead_time_days   as integer) as lead_time_days,
    cast(unit_cost        as double)  as unit_cost,
    cast(shelf_life_days  as integer) as shelf_life_days
from {{ source('demand_planning', 'items') }}
