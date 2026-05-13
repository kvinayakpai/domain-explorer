{{ config(materialized='view') }}

select
    cast(deduction_id      as varchar) as deduction_id,
    cast(account_id        as varchar) as account_id,
    cast(order_id          as varchar) as order_id,
    cast(stop_id           as varchar) as stop_id,
    cast(claim_number      as varchar) as claim_number,
    cast(deduction_type    as varchar) as deduction_type,
    cast(amount_cents      as bigint)  as amount_cents,
    cast(open_amount_cents as bigint)  as open_amount_cents,
    cast(opened_date       as date)    as opened_date,
    cast(aging_days        as integer) as aging_days,
    cast(status            as varchar) as status,
    cast(dispute_reason    as varchar) as dispute_reason,
    cast(epod_evidence_uri as varchar) as epod_evidence_uri,
    cast(resolution_date   as date)    as resolution_date,
    case when epod_evidence_uri is not null then true else false end as has_epod_evidence
from {{ source('direct_store_delivery', 'deduction') }}
