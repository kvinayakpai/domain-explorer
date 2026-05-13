-- Vault satellite carrying Deduction state through its lifecycle.
{{ config(materialized='ephemeral') }}

with src as (select * from {{ ref('stg_trade_promotion_management__deduction') }})

select
    md5(deduction_id)                                                            as h_deduction_hk,
    coalesce(opened_date::timestamp, current_timestamp)                          as load_ts,
    md5(coalesce(status,'') || '|' || cast(coalesce(open_amount_cents,0) as varchar) || '|' ||
        coalesce(dispute_reason,'') || '|' || coalesce(deduction_type,''))       as hashdiff,
    invoice_id,
    claim_number,
    deduction_type,
    amount_cents,
    open_amount_cents,
    aging_days,
    status,
    dispute_reason,
    resolution_date,
    'trade_promotion_management.deduction'                                        as record_source
from src
