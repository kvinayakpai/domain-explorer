-- Grain: one row per reconciliation break.
{{ config(materialized='table') }}

with b as (select * from {{ ref('stg_settlement_clearing__reconciliation_break') }})

select
    md5(b.break_id)                                       as break_key,
    b.break_id,
    b.recon_type,
    b.side_a_system,
    b.side_b_system,
    b.instrument_id,
    b.qty_diff,
    b.amount_diff,
    b.currency,
    cast({{ format_date('b.detected_at', '%Y%m%d') }} as integer)     as detected_date_key,
    b.detected_at,
    b.status,
    b.owner_team,
    b.aged_days,
    case when b.status in ('Resolved','WrittenOff') then true else false end as is_closed
from b
