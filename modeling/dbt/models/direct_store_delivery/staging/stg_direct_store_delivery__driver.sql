{{ config(materialized='view') }}

select
    cast(driver_id        as varchar) as driver_id,
    cast(branch_id        as varchar) as branch_id,
    cast(employee_number  as varchar) as employee_number,
    cast(full_name        as varchar) as full_name,
    cast(cdl_class        as varchar) as cdl_class,
    cast(cdl_expiry       as date)    as cdl_expiry,
    cast(hire_date        as date)    as hire_date,
    cast(tenure_years     as double)  as tenure_years,
    cast(eld_device_id    as varchar) as eld_device_id,
    cast(home_terminal    as varchar) as home_terminal,
    cast(pay_class        as varchar) as pay_class,
    cast(status           as varchar) as status
from {{ source('direct_store_delivery', 'driver') }}
