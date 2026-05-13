-- Outlet dimension (DSD-suffixed; trade_promotion_management already publishes
-- a customer_outlet dimension under its own naming).
{{ config(materialized='table') }}

with hub as (select * from {{ ref('int_direct_store_delivery__hub_outlet') }}),
     stg as (select * from {{ ref('stg_direct_store_delivery__outlet') }})

select
    h.h_outlet_hk    as outlet_sk,
    h.outlet_bk      as outlet_id,
    s.account_id,
    s.gln,
    s.store_number,
    s.country_iso2,
    s.state_region,
    s.postal_code,
    s.format,
    s.lat,
    s.lng,
    s.status
from hub h
left join stg s on s.outlet_id = h.outlet_bk
