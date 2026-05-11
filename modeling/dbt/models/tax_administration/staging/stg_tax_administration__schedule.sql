{{ config(materialized='view') }}

select
    cast(schedule_id   as varchar) as schedule_id,
    cast(return_id     as varchar) as return_id,
    cast(schedule_code as varchar) as schedule_code,
    cast(line_count    as integer) as line_count,
    cast(total_amount  as double)  as total_amount
from {{ source('tax_administration', 'schedule') }}
