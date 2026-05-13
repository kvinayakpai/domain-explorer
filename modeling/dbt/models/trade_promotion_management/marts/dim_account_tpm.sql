-- Account dimension (TPM-suffixed to avoid collision with dim_account in other anchors).
{{ config(materialized='table') }}

with hub as (select * from {{ ref('int_trade_promotion_management__hub_account') }}),
     stg as (select * from {{ ref('stg_trade_promotion_management__account') }})

select
    h.h_account_hk         as account_sk,
    h.account_bk           as account_id,
    s.account_name,
    s.parent_account_id,
    s.channel,
    s.country_iso2,
    s.gln,
    s.trade_terms_code,
    s.status,
    s.created_at           as valid_from,
    cast(null as timestamp) as valid_to,
    true                   as is_current
from hub h
left join stg s on s.account_id = h.account_bk
