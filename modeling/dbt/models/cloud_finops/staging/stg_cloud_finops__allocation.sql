{{ config(materialized='view') }}

select
    cast(allocation_id        as varchar) as allocation_id,
    cast(billing_account_id   as varchar) as billing_account_id,
    cast(cost_center          as varchar) as cost_center,
    cast(department           as varchar) as department,
    cast(period_start         as date)    as period_start,
    cast(period_end           as date)    as period_end,
    cast(allocated_amount_usd as double)  as allocated_amount_usd,
    cast(allocation_method    as varchar) as allocation_method
from {{ source('cloud_finops', 'allocation') }}
