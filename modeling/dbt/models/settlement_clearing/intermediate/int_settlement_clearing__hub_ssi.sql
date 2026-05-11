-- Vault hub for Settlement Instruction (sese.023).
{{ config(materialized='ephemeral') }}

with src as (
    select ssi_id, created_at
    from {{ ref('stg_settlement_clearing__settlement_instruction') }}
    where ssi_id is not null
)

select
    md5(ssi_id)                                  as h_ssi_hk,
    ssi_id                                       as ssi_bk,
    min(created_at)                              as load_ts,
    'settlement_clearing.settlement_instruction' as record_source
from src
group by ssi_id
