-- Vault hub for the Outlet business key.
{{ config(materialized='ephemeral') }}

with src as (
    select outlet_id from {{ ref('stg_trade_promotion_management__customer_outlet') }}
    where outlet_id is not null
)

select
    md5(outlet_id)                                 as h_outlet_hk,
    outlet_id                                      as outlet_bk,
    current_date                                   as load_date,
    'trade_promotion_management.customer_outlet'   as record_source
from src
group by outlet_id
