-- Vault hub for the Deduction business key.
{{ config(materialized='ephemeral') }}

with src as (
    select deduction_id from {{ ref('stg_trade_promotion_management__deduction') }}
    where deduction_id is not null
)

select
    md5(deduction_id)                        as h_deduction_hk,
    deduction_id                             as deduction_bk,
    current_date                             as load_date,
    'trade_promotion_management.deduction'   as record_source
from src
group by deduction_id
