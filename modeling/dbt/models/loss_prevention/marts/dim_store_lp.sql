-- Type-2 store dimension for loss_prevention. _lp suffix avoids collision with
-- merchandising / pricing_and_promotions / store_ops dim_store tables.
{{ config(materialized='table') }}

select
    row_number() over (order by store_id)        as store_sk,
    store_id,
    store_name,
    banner,
    region,
    country_iso2,
    format,
    lp_staffing_tier,
    eas_enabled,
    rfid_enabled,
    status,
    cast(null as timestamp)                      as valid_from,
    cast(null as timestamp)                      as valid_to,
    true                                         as is_current
from {{ ref('stg_loss_prevention__store') }}
