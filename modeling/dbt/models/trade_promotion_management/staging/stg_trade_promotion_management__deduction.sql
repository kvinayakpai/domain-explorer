{{ config(materialized='view') }}

select
    cast(deduction_id           as varchar) as deduction_id,
    cast(account_id             as varchar) as account_id,
    cast(invoice_id             as varchar) as invoice_id,
    cast(claim_number           as varchar) as claim_number,
    cast(tactic_id              as varchar) as tactic_id,
    cast(deduction_type         as varchar) as deduction_type,
    cast(amount_cents           as bigint)  as amount_cents,
    cast(open_amount_cents      as bigint)  as open_amount_cents,
    cast(opened_date            as date)    as opened_date,
    cast(aging_days             as integer) as aging_days,
    cast(status                 as varchar) as status,
    cast(dispute_reason         as varchar) as dispute_reason,
    cast(resolution_date        as date)    as resolution_date,
    cast(validation_evidence_uri as varchar) as validation_evidence_uri
from {{ source('trade_promotion_management', 'deduction') }}
