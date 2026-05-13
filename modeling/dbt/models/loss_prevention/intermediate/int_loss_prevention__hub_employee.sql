-- Vault hub for the Employee business key.
{{ config(materialized='ephemeral') }}

with src as (
    select employee_id
    from {{ ref('stg_loss_prevention__employee') }}
    where employee_id is not null
)

select
    md5(employee_id)                    as h_employee_hk,
    employee_id                         as employee_bk,
    current_date                        as load_date,
    'loss_prevention.employee'          as record_source
from src
group by employee_id
