{{ config(materialized='table') }}

with hub as (select * from {{ ref('int_direct_store_delivery__hub_driver') }}),
     stg as (select * from {{ ref('stg_direct_store_delivery__driver') }})

select
    h.h_driver_hk           as driver_sk,
    h.driver_bk             as driver_id,
    s.branch_id,
    s.employee_number,
    s.full_name,
    s.cdl_class,
    s.cdl_expiry,
    s.hire_date,
    s.tenure_years,
    s.eld_device_id,
    s.home_terminal,
    s.pay_class,
    s.status,
    s.hire_date             as valid_from,
    cast(null as timestamp) as valid_to,
    true                    as is_current
from hub h
left join stg s on s.driver_id = h.driver_bk
