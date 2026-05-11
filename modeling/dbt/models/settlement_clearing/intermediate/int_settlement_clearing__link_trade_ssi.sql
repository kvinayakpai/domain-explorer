-- Vault link: Trade ↔ Settlement Instruction.
{{ config(materialized='ephemeral') }}

with s as (
    select ssi_id, trade_id from {{ ref('stg_settlement_clearing__settlement_instruction') }}
    where ssi_id is not null and trade_id is not null
)

select
    md5(trade_id || '|' || ssi_id)               as l_trade_ssi_hk,
    md5(trade_id)                                as h_trade_hk,
    md5(ssi_id)                                  as h_ssi_hk,
    current_date                                 as load_date,
    'settlement_clearing.settlement_instruction' as record_source
from s
group by trade_id, ssi_id
