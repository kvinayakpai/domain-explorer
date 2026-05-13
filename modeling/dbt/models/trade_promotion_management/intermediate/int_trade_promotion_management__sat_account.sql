-- Vault satellite carrying mutable Account attributes.
{{ config(materialized='ephemeral') }}

with src as (select * from {{ ref('stg_trade_promotion_management__account') }})

select
    md5(account_id)                                                              as h_account_hk,
    coalesce(created_at, current_timestamp)                                      as load_ts,
    md5(coalesce(account_name,'') || '|' || coalesce(channel,'') || '|' ||
        coalesce(trade_terms_code,'') || '|' || coalesce(status,''))             as hashdiff,
    account_name,
    parent_account_id,
    channel,
    country_iso2,
    gln,
    trade_terms_code,
    status,
    'trade_promotion_management.account'                                          as record_source
from src
