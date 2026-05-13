-- Fact: one row per POS exception. Joins to dim_store_lp / dim_employee / dim_date_lp.
{{ config(materialized='table') }}

with e as (select * from {{ ref('stg_loss_prevention__pos_exception') }}),
     s as (select * from {{ ref('dim_store_lp') }}),
     m as (select * from {{ ref('dim_employee') }})

select
    e.exception_id,
    cast({{ format_date('e.detected_at', '%Y%m%d') }} as integer) as date_key,
    s.store_sk,
    m.employee_sk,
    e.transaction_id,
    e.exception_type,
    e.exception_score,
    e.source_system,
    e.amount_at_risk_minor,
    e.is_open,
    e.is_closed_confirmed,
    e.is_closed_unfounded,
    e.detected_at
from e
left join s on s.store_id    = e.store_id
left join m on m.employee_id = e.employee_id
