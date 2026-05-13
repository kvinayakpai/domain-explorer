-- Fact: one row per (route_id, settlement_date). Drives Settlement Accuracy %,
--       Cost per Stop, Cost per Case rollups.
{{ config(materialized='table') }}

with s   as (select * from {{ ref('stg_direct_store_delivery__settlement') }}),
     dr  as (select * from {{ ref('dim_route') }}),
     dd  as (select * from {{ ref('dim_driver') }}),
     dv  as (select * from {{ ref('dim_vehicle') }})

select
    s.settlement_id,
    cast(strftime(s.settlement_date, '%Y%m%d') as integer)       as date_key,
    dr.route_sk,
    dd.driver_sk,
    dv.vehicle_sk,
    s.total_invoiced_cents,
    s.total_collected_cash_cents,
    s.total_collected_check_cents,
    s.total_collected_eft_cents,
    s.total_charge_account_cents,
    s.returns_credit_cents,
    s.spoilage_credit_cents,
    s.variance_cents,
    s.abs_variance_cents,
    s.is_balanced,
    case when s.status = 'disputed' then true else false end     as is_disputed,
    s.closed_at
from s
left join dr on dr.route_id   = s.route_id
left join dd on dd.driver_id  = s.driver_id
left join dv on dv.vehicle_id = s.vehicle_id
