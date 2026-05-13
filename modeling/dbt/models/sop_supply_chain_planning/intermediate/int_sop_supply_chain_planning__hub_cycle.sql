-- Vault hub for the S&OP cycle business key.
{{ config(materialized='ephemeral') }}

with src as (
    select distinct cycle_id
    from {{ ref('stg_sop_supply_chain_planning__sop_cycles') }}
    where cycle_id is not null
)

select
    md5(cycle_id)                          as h_cycle_hk,
    cycle_id                                as cycle_bk,
    current_date                            as load_date,
    'sop_supply_chain_planning.sop_cycle'   as record_source
from src
