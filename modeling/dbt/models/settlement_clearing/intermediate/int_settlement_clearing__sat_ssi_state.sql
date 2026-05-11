-- Vault satellite carrying mutable Settlement Instruction state.
{{ config(materialized='ephemeral') }}

with src as (select * from {{ ref('stg_settlement_clearing__settlement_instruction') }})

select
    md5(ssi_id)                                                              as h_ssi_hk,
    created_at                                                               as load_ts,
    md5(coalesce(status,'') || '|' || coalesce(delivery_type,'')
        || '|' || coalesce(payment_type,'') || '|'
        || cast(coalesce(settlement_quantity, 0) as varchar)
        || '|' || cast(coalesce(settlement_amount, 0) as varchar))            as hashdiff,
    settlement_quantity,
    settlement_amount,
    settlement_currency,
    settlement_date,
    delivery_type,
    payment_type,
    status,
    'settlement_clearing.settlement_instruction'                              as record_source
from src
