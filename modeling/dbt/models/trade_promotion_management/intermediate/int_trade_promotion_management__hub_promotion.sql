-- Vault hub for the Promotion business key.
{{ config(materialized='ephemeral') }}

with src as (
    select promotion_id from {{ ref('stg_trade_promotion_management__promotion') }}
    where promotion_id is not null
)

select
    md5(promotion_id)                       as h_promotion_hk,
    promotion_id                            as promotion_bk,
    current_date                            as load_date,
    'trade_promotion_management.promotion'  as record_source
from src
group by promotion_id
