-- Grain: one row per opened audit case.
{{ config(materialized='table') }}

with a as (select * from {{ ref('stg_tax_administration__audit') }})

select
    md5(a.audit_id)                                 as audit_key,
    a.audit_id,
    md5(a.return_id)                                as return_key,
    a.return_id,
    a.audit_type,
    a.selection_reason,
    a.opened_at,
    a.closed_at,
    cast({{ format_date('a.opened_at', '%Y%m%d') }} as integer) as opened_date_key,
    a.examiner_id,
    a.proposed_adjustment,
    a.outcome,
    a.resolution_days,
    case when a.outcome in ('agreed_change', 'tax_court') then true else false end as resulted_in_change,
    case when a.closed_at is null then true else false end as is_open
from a
