-- Vault link: Promotion -> Account.
{{ config(materialized='ephemeral') }}

with src as (
    select promotion_id, account_id
    from {{ ref('stg_trade_promotion_management__promotion') }}
)

select
    md5(coalesce(promotion_id,'')||'|'||coalesce(account_id,'')) as l_link_hk,
    md5(promotion_id)                                            as h_promotion_hk,
    md5(account_id)                                              as h_account_hk,
    current_date                                                 as load_date,
    'trade_promotion_management.promotion'                       as record_source
from src
where promotion_id is not null and account_id is not null
