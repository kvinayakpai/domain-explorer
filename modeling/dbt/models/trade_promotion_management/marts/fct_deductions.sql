-- Fact: one row per deduction with lifecycle flags + match-confidence.
{{ config(materialized='table') }}

with d as (select * from {{ ref('stg_trade_promotion_management__deduction') }}),
     da as (select * from {{ ref('dim_account_tpm') }}),
     dt as (select * from {{ ref('dim_tactic') }})

select
    d.deduction_id,
    da.account_sk,
    dt.tactic_sk,
    cast({{ format_date('d.opened_date', '%Y%m%d') }} as integer)              as opened_date_key,
    case when d.resolution_date is not null
         then cast({{ format_date('d.resolution_date', '%Y%m%d') }} as integer)
         else null end                                                          as resolution_date_key,
    d.deduction_type,
    d.amount_cents,
    d.open_amount_cents,
    d.aging_days,
    d.status,
    case when d.status = 'disputed'      then true else false end              as is_disputed,
    case when d.status = 'paid'          then true else false end              as is_paid,
    case when d.status = 'written_off'   then true else false end              as is_written_off,
    case when d.tactic_id is null then 0.0 else 1.0 end                        as match_confidence
from d
left join da on da.account_id = d.account_id
left join dt on dt.tactic_id  = d.tactic_id
