{{ config(materialized='view') }}

select
    cast(sales_history_id as bigint)   as sales_history_id,
    cast(item_id          as varchar)  as item_id,
    cast(location_id      as varchar)  as location_id,
    cast(customer_id      as varchar)  as customer_id,
    cast(period_start     as date)     as period_start,
    cast(period_grain     as varchar)  as period_grain,
    cast(shipped_units    as double)   as shipped_units,
    cast(shipped_value    as double)   as shipped_value,
    cast(returns_units    as double)   as returns_units,
    cast(source_system    as varchar)  as source_system,
    cast(ingested_at      as timestamp) as ingested_at
from {{ source('sop_supply_chain_planning', 'sales_history') }}
