-- Employee dimension. PII pre-hashed at the source; never carries raw HRIS ids.
{{ config(materialized='table') }}

select
    row_number() over (order by employee_id)     as employee_sk,
    employee_id,
    employee_ref_hash,
    home_store_id,
    role,
    status,
    cast(hire_date as timestamp)                 as valid_from,
    cast(termination_date as timestamp)          as valid_to,
    case when termination_date is null then true else false end as is_current
from {{ ref('stg_loss_prevention__employee') }}
