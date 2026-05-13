{{ config(materialized='view') }}

select
    cast(employee_id        as varchar)   as employee_id,
    cast(employee_ref_hash  as varchar)   as employee_ref_hash,
    cast(home_store_id      as varchar)   as home_store_id,
    cast(role               as varchar)   as role,
    cast(hire_date          as date)      as hire_date,
    cast(termination_date   as date)      as termination_date,
    cast(status             as varchar)   as status
from {{ source('loss_prevention', 'employee') }}
