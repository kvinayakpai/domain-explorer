-- Account dimension.
{{ config(materialized='table') }}

with hub as (select * from {{ ref('int_capital_markets__hub_account') }}),
     stg as (select * from {{ ref('stg_capital_markets__account') }})

select
    h.h_account_hk         as account_key,
    h.account_bk           as account_id,
    s.owner_party_id,
    s.account_type,
    s.base_currency,
    s.status,
    h.load_date            as dim_loaded_at,
    true                   as is_current
from hub h
left join stg s on s.account_id = h.account_bk
