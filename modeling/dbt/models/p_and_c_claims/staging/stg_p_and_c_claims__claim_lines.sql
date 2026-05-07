-- Staging: per-coverage breakdown of a claim.
{{ config(materialized='view') }}

select
    cast(claim_line_id as varchar) as claim_line_id,
    cast(claim_id      as varchar) as claim_id,
    cast(coverage      as varchar) as coverage,
    cast(amount        as double)  as amount,
    cast(status        as varchar) as line_status
from {{ source('p_and_c_claims', 'claim_lines') }}
