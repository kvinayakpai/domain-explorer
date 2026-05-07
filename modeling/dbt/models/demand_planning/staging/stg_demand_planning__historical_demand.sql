-- Staging: realised historical demand.
{{ config(materialized='view') }}

select
    cast(demand_id   as varchar) as demand_id,
    cast(item_id     as varchar) as item_id,
    cast(location_id as varchar) as location_id,
    cast(period_date as date)    as period_date,
    cast(quantity    as double)  as quantity,
    cast(channel     as varchar) as channel
from {{ source('demand_planning', 'historical_demand') }}
