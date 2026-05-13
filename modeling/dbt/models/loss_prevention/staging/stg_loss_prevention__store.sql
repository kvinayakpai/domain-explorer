{{ config(materialized='view') }}

select
    cast(store_id          as varchar)    as store_id,
    cast(store_name        as varchar)    as store_name,
    cast(banner            as varchar)    as banner,
    cast(region            as varchar)    as region,
    cast(country_iso2      as varchar)    as country_iso2,
    cast(format            as varchar)    as format,
    cast(lp_staffing_tier  as varchar)    as lp_staffing_tier,
    cast(eas_enabled       as boolean)    as eas_enabled,
    cast(rfid_enabled      as boolean)    as rfid_enabled,
    cast(status            as varchar)    as status
from {{ source('loss_prevention', 'store') }}
