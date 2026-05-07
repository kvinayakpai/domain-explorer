-- Staging: vendor master.
{{ config(materialized='view') }}

select
    cast(vendor_id      as varchar) as vendor_id,
    cast(vendor_name    as varchar) as vendor_name,
    upper(country)                  as country_code,
    cast(tier           as varchar) as tier,
    cast(lead_time_days as integer) as lead_time_days,
    cast(active         as boolean) as is_active
from {{ source('merchandising', 'vendors') }}
