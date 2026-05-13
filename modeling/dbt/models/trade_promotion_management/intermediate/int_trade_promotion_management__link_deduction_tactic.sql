-- Vault link: Deduction -> Tactic -> Account (with match confidence).
{{ config(materialized='ephemeral') }}

with src as (
    select deduction_id, tactic_id, account_id
    from {{ ref('stg_trade_promotion_management__deduction') }}
)

select
    md5(coalesce(deduction_id,'')||'|'||coalesce(tactic_id,'')||'|'||coalesce(account_id,'')) as l_link_hk,
    md5(deduction_id)                                                as h_deduction_hk,
    md5(coalesce(tactic_id, ''))                                     as h_tactic_hk,
    md5(account_id)                                                  as h_account_hk,
    case when tactic_id is null then 0.0 else 1.0 end                as match_confidence,
    current_date                                                     as load_date,
    'trade_promotion_management.deduction'                           as record_source
from src
