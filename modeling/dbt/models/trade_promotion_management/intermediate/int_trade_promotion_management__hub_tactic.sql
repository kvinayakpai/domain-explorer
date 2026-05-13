-- Vault hub for the Tactic business key.
{{ config(materialized='ephemeral') }}

with src as (
    select tactic_id from {{ ref('stg_trade_promotion_management__promo_tactic') }}
    where tactic_id is not null
)

select
    md5(tactic_id)                              as h_tactic_hk,
    tactic_id                                   as tactic_bk,
    current_date                                as load_date,
    'trade_promotion_management.promo_tactic'   as record_source
from src
group by tactic_id
